from ext.games.blackjack import Blackjack
import discord,random,datetime,os

import modules.utilities as utils

from discord.ext.commands 	import Context
from discord.ext 			import commands, tasks
from modules.utilities		import logger as l, utilities as u,secrets,ylcb_config
from ext 					import Extension, database

class games(Extension):
	"""Games Extension - ylcb-devs"""
	def __init__(self, bot: commands.Bot):
		"""Games(bot)"""
		super().__init__(bot, "ext.games")
		self.econ = bot.get_cog("economy")
		self.airdrop_spawner.start()
	
	
	def cog_unload(self):
		self.airdrop_spawner.cancel()
	
	
	@tasks.loop(hours=1)
	async def airdrop_spawner(self):
		chance = random.randint(1,100)
		if chance <= 50:
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
			embed = discord.Embed.from_dict(embed_dict)
			channel = await self.bot.fetch_channel(ylcb_config.data["discord"]["event_channel_id"])
			
			msg: discord.Message = await channel.send(embed=embed)
			await msg.add_reaction("🛄")
			def check(reaction: discord.Reaction, user: discord.Member): return user != self.bot.user and str(reaction.emoji) == "🛄"
			reaction, user = await self.bot.wait_for("reaction_add", check=check) #(":baggage_claim:")
			l.log(f"{user.display_name}#{user.discriminator} claimed an airdrop worth ${money}")
			bal = self.econ.get_bal_from_d_id(user.id)
			self.econ.set_balance_from_d_id(bal + money, user.id)
			
			embed_dict["title"] = "Claimed!"
			embed_dict["timestamp"] = datetime.datetime.now().isoformat()
			embed_dict["color"] = 0x00ff00
			embed_dict["author"] = {
				"name": user.display_name,
				"icon_url": str(user.avatar_url)
			}
			
			embed = discord.Embed.from_dict(embed_dict)
			await msg.edit(embed=embed)
	
	
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
		self.econ.set_balance_from_d_id(points - bet, ctx.author.id)
		return True
	
	
	"""
	Game functions need to start with this template
	@commands.command(name="game_name")
	async def game_name(self, ctx, points: int = None):
		l.log(ctx)
		_cfg = self.config.data["games"][game_name]
		points = self.econ.get_bal_from_d_id(ctx.author.id)
		## important checks needed to play the game lol
		if not points: 
			await ctx.send(f"{ctx.author.mention}, please specify a bet")
			return
		if not await self.can_user_play(ctx, _cfg, points): return
		## set points again because can_user_play edits
		points = self.econ.get_bal_from_d_id(ctx.author.id)
		## logging the successful start of a game
		l.log(f"{game_name} start: {ctx.author.display_name}#{ctx.author.discriminator} | Bet:${bet} | CPU:{cpu_score}")
	"""
	
	
	@commands.command(name="21")
	async def blackjack(self, ctx, bet: float = None):
		"""Blackjack minigame"""
		l.log(ctx)
		bet = round(bet, 2)
		_cfg = self.config.data["games"]["blackjack"]
		points = self.econ.get_bal_from_d_id(ctx.author.id)
		## important checks needed to play the game lol
		if not bet: 
			await ctx.send(f"{ctx.author.mention}, please specify a bet")
			return
		if not await self.can_user_play(ctx, _cfg, bet, points): return
		## set points again because can_user_play edits
		points = self.econ.get_bal_from_d_id(ctx.author.id)
		## logging the successful start of a bj game
		l.log(f"Blackjack start: {ctx.author.display_name}#{ctx.author.discriminator} | Bet:${bet}")
		## lazy man's blackjack
		bj = Blackjack()
		await bj.game(ctx,self,bet)
		p_score = Blackjack.total(bj.player_hand)
		cpu_score = Blackjack.total(bj.dealer_hand)
		l.log(f"Blackjack outcome: {ctx.author.display_name}#{ctx.author.discriminator}:{p_score} | Bet:${bet} | CPU:{cpu_score}")


def setup(bot):
	bot.add_cog(games(bot))