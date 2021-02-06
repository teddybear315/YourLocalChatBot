import json

from discord.ext.commands import errors
from discord.ext.commands import Cog, Bot
from modules.utilities import Config

extensions = Config("extensions.json")


class Extension(Cog):
	def __init__(self, bot: Bot, name: str):
		self.config = Config(f"{name.replace('.', '/')}.json")
		self.cog_name = name
		self.bot = bot