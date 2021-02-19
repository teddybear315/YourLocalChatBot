import json

from discord.ext import commands
from modules.utilities import Config

extensions = Config("extensions.json")


class Extension(commands.Cog):
	def __init__(self, bot: commands.Bot, name: str):
		self.config = Config(f"{name.replace('.', '/')}.json")
		self.cog_name = name
		self.bot = bot
