import discord
import random
import datetime

import modules.utilities as utils

from discord.ext.commands 	import Context
from discord.ext 			import commands
from modules 				import db
from modules				import u
from ext 					import Extension


class Games(Extension):
	"""Games Extension - ylcb-devs"""
	def __init__(self, bot: commands.Bot):
		"""Games(bot)"""
		super().__init__(
			bot,
			{"ext.database"},
			utils.Config(f"exts/games.json")
		)
	
	async def can_user_play(self, ctx, _cfg, points):
		if not self.config.data["enabled"] or not _cfg["enabled"]:
			await ctx.send(f"{ctx.author.mention}, this game has been disabled by an admin.")
			return False
		# TODO when database setup check if has enough points to play
		if _cfg["min_bet"] < 1:
			_cfg["min_bet"] = 1
			self.config.updateFile()
			u.log("min_bet was lower than 1, min_bet was set to 1", u.FLG)
		if points > _cfg["max_bet"] and _cfg["max_bet"] != 0:
			await ctx.send(f"{ctx.author.mention}, the max bet is {_cfg['max_bet']}")
			return False
		return True
	
	"""
	Game functions need to start with this template
	@commands.command(name="game_name")
	async def game_name(self, ctx, points: int = None):
		u.log(ctx)
		_cfg = self.config.data["games"][game_name]
		## important checks needed to play the game lol
		if not points: 
			await ctx.send(f"{ctx.author.mention}, please specify a bet")
			return
		if not await self.can_user_play(ctx, _cfg, points): return
		## logging the successful start of a game
		u.log(f"{game_name} start: {ctx.author.name}#{ctx.author.discriminator} | Bet:${points}")
	"""
	
	@commands.command(name="blackjack")
	async def blackjack(self, ctx, points: int = None):
		"""Blackjack minigame"""
		u.log(ctx)
		_cfg = self.config.data["games"]["blackjack"]
		## important checks needed to play the game lol
		if not points: 
			await ctx.send(f"{ctx.author.mention}, please specify a bet")
			return
		if not await self.can_user_play(ctx, _cfg, points): return
		
		## logging the successful start of a bj game
		u.log(f"Blackjack start: {ctx.author.name}#{ctx.author.discriminator} | Bet:${points}")
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
		#embed.add_field(name="Changelog", value=f"\t- {nt.join(config['meta']['changelog'])}")
		#embed.set_footer(datetime.datetime.now())
		if p_score > cpu_score:
			embed_dict["color"] = 0x00ff00
			embed_dict["title"] = "You won!"
			if p_score == 21: 
				points = points * _cfg["bj_multiplier"]
				# TODO add point stuff
			else: 
				points = points * _cfg["bj_multiplier"]
				# TODO add point stuff
		elif cpu_score > p_score:
			embed_dict["color"] = 0xff0000
			embed_dict["title"] = "You lost!"
			points = 0
			# TODO add point stuff
		embed = discord.Embed.from_dict(embed_dict)
		await ctx.send(embed=embed)
		u.log(f"Blackjack outcome: {ctx.author.name}#{ctx.author.discriminator}:{p_score} | Payout:${points} | CPU:{cpu_score}")


def setup(bot):
	bot.add_cog(Games(bot))