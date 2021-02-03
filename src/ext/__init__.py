import json

from discord.ext.commands import errors
from discord.ext.commands import Cog, Bot
from modules.utilities import Config


extensions = Config("extensions.json")


class Extension(Cog):
	def __init__(self, bot: Bot, name: str, requirements: list = {}, config: Config = {}):
		self.requirements = requirements
		self.config = config
		self.bot = bot