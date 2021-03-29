import json

from discord.ext import commands

from .utilities import Config

extensions = Config("extensions.json")


class Extension(commands.Cog):
	def __init__(self, bot: commands.Bot, name: str):
		"""
		Extension(bot, name)

		Args:
			bot (`commands.Bot`): commands.Bot instance
			name (`str`): Name of extension
		"""
		self.config = Config(f"{name.replace('.', '/')}.json")
		self.name = name
		self.bot = bot
