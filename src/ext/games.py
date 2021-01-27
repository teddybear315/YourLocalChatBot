import discord
import random
import datetime

from discord.ext import commands
from discord.ext.commands import Context

from modules import utils as u
from modules import db

__requirements__ = ["cogs.database"]

class Games(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.requirements: list[str]	= {"ext.database"}
		self.bot: commands.Bot			= bot
		self.guild: discord.Guild		= self.bot.get_guild(u.config["discord"]["guild_id"])
		self.streamerRole: discord.Role	= self.guild.get_role(u.config["discord"]["streamer_role_id"])

	async def can_user_play(self, ctx, _cfg, points):
		if not _cfg["enabled"]:
			await ctx.send(f"{ctx.author.mention}, this game has been disabled by an admin.")
			return False
		if _cfg["vip_only"] and not u.vip(ctx.author):
			await ctx.send(f"{ctx.author.mention}, you must be a vip to play this game.")
			return False
		# TODO when database setup check if has enough points to play with
		return True

	@commands.command(name="blackjack")
	async def blackjack(self, ctx, points: int = None):
		u.log(ctx)
		_cfg = u.config["games"]["blackjack"]
		## important checks needed to play the game lol
		if not points: 
			await ctx.send(f"{ctx.author.mention}, please specify a bet")
			return
		if not await self.can_user_play(ctx, _cfg, points): return
		if _cfg["min_bet"] < 1:
			_cfg["min_bet"] = 1
			u.editConfig()
			u.config = u.reloadConfig()
			u.log("min_bet was lower than 1, min_bet was set to 1", lvl=u.WRN)
		if points > _cfg["max_bet"] and _cfg["max_bet"] != 0:
			await ctx.send(f"{ctx.author.mention}, the max bet is {_cfg['max_bet']}")
			return
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