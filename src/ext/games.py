import discord
import random
import datetime

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
		self.printer.start()
	
	
	def cog_unload(self):
		self.printer.cancel()
	
	
	@tasks.loop(hours=1)
	async def printer(self):
		return
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
					"name": self.bot.user.name,
					"icon_url": str(self.bot.user.avatar_url)
				}
			}
			embed = discord.Embed.from_dict(embed_dict)
			channel = await self.bot.fetch_channel(ylcb_config.data["discord"]["event_channel_id"])
			
			msg: discord.Message = await channel.send(embed=embed)
			await msg.add_reaction("🛄")
			def check(reaction: discord.Reaction, user: discord.Member): return user != self.bot.user and str(reaction.emoji) == "🛄"
			reaction, user = await self.bot.wait_for("reaction_add", check=check) #(":baggage_claim:")
			l.log(f"{user.name}#{user.discriminator} claimed an airdrop worth ${money}")
			bal = self.econ.get_bal_from_d_id(user.id)
			self.econ.set_balance_from_d_id(bal + money, user.id)
			
			embed_dict["title"] = "Claimed!"
			embed_dict["timestamp"] = datetime.datetime.now().isoformat()
			embed_dict["color"] = 0x00ff00
			embed_dict["author"] = {
				"name": user.name,
				"icon_url": str(user.avatar_url)
			}
			
			embed = discord.Embed.from_dict(embed_dict)
			await msg.edit(embed=embed)
	
	
	@printer.before_loop
	async def before_printer(self):
		await self.bot.wait_until_ready()
	
	
	async def can_user_play(self, ctx, _cfg, bet, points):
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
		l.log(f"{game_name} start: {ctx.author.name}#{ctx.author.discriminator} | Bet:${bet} | Multiplier:{multiplier}x | CPU:{cpu_score}")
	"""
	
	
	@commands.command(name="blackjack")
	async def blackjack(self, ctx, bet: float = None):
		"""Blackjack minigame"""
		l.log(ctx)
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
		l.log(f"Blackjack start: {ctx.author.name}#{ctx.author.discriminator} | Bet:${bet}")
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
		multiplier = 1
		if p_score > cpu_score:
			multiplier = _cfg["win_multiplier"]
			if p_score == 21: multiplier = _cfg["bj_multiplier"]
			self.econ.set_balance_from_d_id(points + (bet*multiplier), ctx.author.id)
			embed_dict["color"] = 0x00ff00
			embed_dict["title"] = f"You won ${bet*multiplier}!"
		elif cpu_score > p_score:
			embed_dict["color"] = 0xff0000
			embed_dict["title"] = f"You lost ${bet}!"
		embed = discord.Embed.from_dict(embed_dict)
		await ctx.send(embed=embed)
		l.log(f"Blackjack outcome: {ctx.author.name}#{ctx.author.discriminator}:{p_score} | Bet:${bet} | Multiplier:{multiplier}x | CPU:{cpu_score}")


def setup(bot):
	bot.add_cog(games(bot))