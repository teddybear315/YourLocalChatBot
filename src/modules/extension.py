import json

from discord.ext import commands

from .utilities import Config


class Extension(commands.Cog):
	def __init__(self, bot: commands.Bot, name: str):
		"""
		Extension(bot, name)

		Args:
			bot (`commands.Bot`): commands.Bot instance
			name (`str`): Name of extension
		"""
		self.config = Config(f"./src/ext/config/{name}.json")
		self.name = name
		self.bot = bot
