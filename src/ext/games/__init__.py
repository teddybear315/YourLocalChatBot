import datetime
import os
import random

import discord
import modules.utilities as utils
from discord.ext import commands, tasks
from ext import Extension
from ext.games.blackjack import Blackjack
from modules.utilities import logger as l
from modules.utilities import prefix, secrets
from modules.utilities import utilities as u
from modules.utilities import ylcb_config


class games(Extension):
	"""Games Extension - ylcb-devs"""
	def __init__(self, bot: commands.Bot):
		"""Games(bot)"""
		super().__init__(bot, "ext.games")
		self.econ = bot.get_cog("economy")
		self.db = bot.get_cog("database").db
		self.items = bot.get_cog("items")
		self.airdrop_spawner.start()
	
	
	def cog_unload(self):
		self.airdrop_spawner.cancel()
	
	
	@tasks.loop(hours=1)
	async def airdrop_spawner(self):
		chance = random.randint(1,100)
		if chance < 60:
			l.log("Airdrop Spawned")
			money = random.randint(10,1000)
			embed_dict = {
				"title":"Airdrop!",
				"type": "rich",
				"timestamp": datetime.datetime.now().isoformat(),
				"color": 0xff8800,
				"fields": [
					{"name": "Money:", "value": "$"+str(money)}
				],
				"author": {
					"name": self.bot.user.display_name,
					"icon_url": str(self.bot.user.avatar_url)
				}
			}
			
			rand_id = random.randint(1,10)
			try: item = self.items.get_item_from_id(rand_id)
			except: item = None
			if item: embed_dict["fields"].append({"name": "Contains:", "value": "1x "+item["name"]})
			
			embed = discord.Embed.from_dict(embed_dict)
			channel = await self.bot.fetch_channel(ylcb_config.data["discord"]["event_channel_id"])
			
			msg: discord.Message = await channel.send("@here", embed=embed)
			await msg.add_reaction("🛄")
			def check(reaction: discord.Reaction, user: discord.Member): return user != self.bot.user and str(reaction.emoji) == "🛄"
			reaction, user = await self.bot.wait_for("reaction_add", check=check) #(":baggage_claim:")
			l.log(f"{user.display_name}#{user.discriminator} claimed an airdrop worth ${money}", channel=l.DISCORD)
			self.econ.set_balance_from_d_id(user.id, self.econ.get_balance_from_d_id(user.id) + money)
			if item: self.items.add_item_to_inventory_from_d_id(user.id, item["id"])
			
			embed_dict["title"] = "Claimed!"
			embed_dict["timestamp"] = datetime.datetime.now().isoformat()
			embed_dict["color"] = 0x00ff00
			embed_dict["author"] = {
				"name": user.display_name,
				"icon_url": str(user.avatar_url)
			}
			
			embed = discord.Embed.from_dict(embed_dict)
			await msg.edit(content=None, embed=embed)
	
	
	@airdrop_spawner.before_loop
	async def before_airdrop_spawner(self):
		await self.bot.wait_until_ready()
	
	
	async def can_user_play(self, ctx, _cfg: dict, bet: float, points: float):
		bet = round(bet, 2)
		if not self.config.data["enabled"] or not _cfg["enabled"]:
			await ctx.send(f"{ctx.author.mention}, this game has been disabled by an admin.")
			return False
		if points < bet:
			await ctx.send(f"{ctx.author.mention}, you only have ${points} to bet!")
			return False
		if _cfg["min_bet"] < 1:
			_cfg["min_bet"] = 1
			self.config.updateFile()
			l.log("min_bet was lower than 1, min_bet was set to 1", l.FLG)
		if bet > _cfg["max_bet"] and _cfg["max_bet"] != 0:
			await ctx.send(f"{ctx.author.mention}, the max bet is {_cfg['max_bet']}")
			return False
		self.econ.set_balance_from_d_id(ctx.author.id, points - bet)
		return True
	
	
	"""
	Game functions need to start with this template
	@commands.command(name=game_name)
	async def game_name(self, ctx, points: int = None):
		# _cfg = self.config.data["games"][game_name]
		## important checks needed to play the game lol
		if not points: 
			await ctx.send(f"{ctx.author.mention}, please specify a bet")
			return
		if not await self.can_user_play(ctx, (self.config.data["games"][game_name] or _cfg), bet, self.econ.get_balance_from_d_id(ctx.author.id)): return
		points = self.econ.get_balance_from_d_id(ctx.author.id)
		## logging the successful start of a game
		l.log(f"{game_name} start: {ctx.author.display_name}#{ctx.author.discriminator}:{p_score} | Bet:${bet} | CPU:{cpu_score}", channel=l.DISCORD)
	"""
	
	
	@commands.command(name="chance", usage=f"{prefix}chance <bet:float>")
	async def chance(self, ctx, bet: float = None):
		"""Quick and easy betting"""
		bet = round(bet, 2) 
		_cfg = self.config.data["games"]["chance"]
		## important checks needed to play the game lol
		if not bet: 
			await ctx.send(f"{ctx.author.mention}, please specify a bet")
			return
		if not await self.can_user_play(ctx, _cfg, bet, self.econ.get_balance_from_d_id(ctx.author.id)): return
		points = self.econ.get_balance_from_d_id(ctx.author.id)
		
		## logging the successful start of a chance game
		l.log(f"Chance start: {ctx.author.name}#{ctx.author.discriminator} | Bet:${bet}", channel=l.DISCORD)
		## lazy man's blackjack
		p_score	  = random.randint(2,21)
		cpu_score = random.randint(2,21)
		
		embed_dict = {
			"title":"It\'s a push!",
			"type": "rich",
			"timestamp": datetime.datetime.now().isoformat(),
			"color": 0xffdd00,
			"fields": [
				{"name": "You scored:", "value": p_score, "inline": True},
				{"name": "I scored:", "value": cpu_score, "inline": True}
			]
		}
		
		boost = self.items.get_boost_from_d_id(ctx.author.id)
		multiplier = 1 + boost
		if p_score > cpu_score:
			won = bet*multiplier
			multiplier = _cfg["small_multiplier"] + boost
			if p_score == 21: multiplier = _cfg["large_multiplier"] + boost
			self.econ.set_balance_from_d_id(ctx.author.id, points + won)
			embed_dict["color"] = 0x00ff00
			embed_dict["title"] = f"You won ${won}!"
		elif cpu_score > p_score:
			embed_dict["color"] = 0xff0000
			embed_dict["title"] = f"You lost ${bet}!"
		elif cpu_score == p_score:
			self.econ.set_balance_from_d_id(ctx.author.id, points + bet)
		embed = discord.Embed.from_dict(embed_dict)
		await ctx.send(embed=embed)
		l.log(f"Chance outcome: {ctx.author.name}#{ctx.author.discriminator}:{p_score} | Bet:${bet} | Multiplier:{multiplier}x ({boost}) | CPU:{cpu_score}", channel=l.DISCORD)
	
	
	@commands.command(name="21", aliases=["bj", "blackjack"], usage=f"{prefix}21 <bet:float>")
	async def blackjack(self, ctx, bet: float = None):
		"""Basic version of blackjack"""
		bet = round(bet, 2) 
		## important checks needed to play the game lol
		if not bet: 
			await ctx.send(f"{ctx.author.mention}, please specify a bet")
			return
		if not await self.can_user_play(ctx, self.config.data["games"]["blackjack"], bet, self.econ.get_balance_from_d_id(ctx.author.id)): return
		## logging the successful start of a bj game
		l.log(f"Blackjack start: {ctx.author.display_name}#{ctx.author.discriminator} | Bet:${bet}", channel=l.DISCORD)
		
		bj = Blackjack(ctx,self,bet)
		await bj.game()
		
		l.log(f"Blackjack outcome: {ctx.author.display_name}#{ctx.author.discriminator}:{Blackjack.total(bj.player_hand)} | Bet:${bet} | Multiplier:{bj.multiplier}x ({bj.boost}) | CPU:{Blackjack.total(bj.dealer_hand)}", channel=l.DISCORD)


def setup(bot):
	bot.add_cog(games(bot))
