import json

from discord.ext.commands import Cog, Bot
from modules.utilities import Config

desired_extensions = json.load(open(f"config/extensions.json"))["exts"]


class Extension(Cog):
	def __init__(self, bot: Bot, requirements: list = {}, config: Config = {}):
		self.requirements = requirements
		self.config = config
		self.bot = bot