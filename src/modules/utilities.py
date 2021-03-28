import datetime
import json
from sys import argv

import discord
from discord.ext import commands
from neotermcolor import cprint


class Config:
	"""Config class"""
	def __init__(self, path: str = "config.json"):
		"""Config()"""
		self.path = f"./config/{path}"
		self.data: dict
		self.updateData()
	
	
	def updateFile(self):
		"""Updates config file with current data"""
		with open(self.path, "w+") as f:
			f.write(json.dumps(self.data))
			f.close()
	
	
	def updateData(self) -> dict:
		"""Loads contents of config file into data"""
		self.data = json.load(open(self.path))
		return self.data


class Logger:
	"""Logger class"""
	# Logging Levels
	CMD = 1
	WRN = 2
	ERR = 3
	LOG = 4
	FLG = 5
	
	# Input Channels
	SYSTEM	= 0
	DISCORD	= 1
	TWITCH	= 2
	
	@staticmethod
	def log(msg, lvl = LOG, channel = SYSTEM):
		"""Decent logging system"""
		timestamp = str(datetime.datetime.now().isoformat(timespec="seconds")).replace("T", " ")
		
		prefix = "LOG"
		color = "white"
		
		if type(msg) is commands.Context:
			lvl = Logger.CMD
			msg = f"{msg.command.name} command ran by {msg.author.display_name}#{msg.author.discriminator}"
		
		if lvl == Logger.WRN:
			prefix = "WRN"
			color = "yellow"
		elif lvl == Logger.ERR:
			prefix = "ERR"
			color = "red"
		elif lvl == Logger.CMD:
			prefix = "CMD"
			color = "green"
		elif lvl == Logger.FLG:
			prefix = "FLG"
			color = "magenta"
		
		cprint(f"[{channel}][{prefix}] {timestamp}: {msg}", color=color)


class Utilities:
	"""Utilities class"""
	@staticmethod
	def discordify(string: str) -> str:
		return string.replace("_", "\_").replace("*", "\*").replace("`", "\`").replace("~", "\~").replace(">", "\>")
	
	
	@staticmethod
	def is_admin() -> bool:
		"""Returns if user is an admin"""
		async def predicate(ctx):
			return ctx.author.guild_permissions.administrator
		return commands.check(predicate)
	
	
	@staticmethod
	def is_dev() -> bool:
		"""Returns if user is one of my developers"""
		async def predicate(ctx):
			return ctx.author.id in ylcb_config.data["devs"]
		return commands.check(predicate)
	
	
	@staticmethod
	def streamer(user: discord.Member) -> bool:
		"""Returns if a user is a streamer"""
		for role in user.roles:
			if role.id == ylcb_config.data["discord"]["streamer_role_id"]: return True
		return False


ylcb_config = Config("config.json")
secrets = Config("secrets.json")
utilities = Utilities()
logger = Logger()

debugging = ("--debug" in argv)
if debugging:
	prefix = ylcb_config.data["bot"]["dev_prefix"]
else:
	prefix = ylcb_config.data["bot"]["prefix"]
