import json
from datetime import datetime
from sys import argv

import discord
from discord.ext import commands
from neotermcolor import cprint

debugging = ("--debug" in argv)


class Config:
	"""Config class"""
	def __init__(self, path: str = "./config/config.json"):
		"""
		Config(path)

		Args:
			path (`str`, optional): Path to config file. Defaults to `"config.json"`. Prefix: `"./config/"`
		"""
		self.path = path
		self.data: dict
		self.updateData()
	
	
	def updateFile(self):
		"""
		Updates config file with current data
		"""
		with open(self.path, "w+") as f:
			f.write(json.dumps(self.data))
			f.close()
	
	
	def updateData(self) -> dict:
		"""
		Loads contents of config file into data

		Returns:
			`dict`: New data
		"""
		self.data = json.load(open(self.path))
		return self.data


class Logger:
	"""Logger class"""
	# Logging Levels
	CMD = 0
	WRN = 1
	ERR = 2
	LOG = 3
	FLG = 4
	
	# Input Channels
	SYSTEM	= 0
	DISCORD	= 1
	TWITCH	= 2
	
	FILE = 0
	CONSOLE = 1
	BOTH = 2
	
	
	def __init__(self):
		self.config = ylcb_config.data["logging"]
		self.path = self.config["path"]+datetime.now().strftime(self.config["format"])+self.config["type"]
		if debugging:
			self.path = self.config["path"]+ "DEBUG " +datetime.now().strftime(self.config["format"])+self.config["type"]
	
	
	def write(self, string: str = "\n"):
		"""
		Appends line to log file

		Args:
			string (str, optional): String to append to file. Defaults to "\n".
		"""
		with open(self.path, "a+") as file:
			file.write(string)
	
	
	def log(self, msg, lvl = LOG, channel = SYSTEM, destination = BOTH):
		"""
		Decent logging system

		Args:
			msg (str): Message to log
			lvl (int, optional): Logging level. Defaults to LOG.
			channel (int, optional): Logging channel. Defaults to SYSTEM.
		"""
		timestamp = str(datetime.now().isoformat(timespec="seconds")).replace("T", " ")
		
		prefix = "LOG"
		color = "white"
		
		if type(msg) is commands.Context:
			lvl = self.CMD
			msg = f"{msg.command.name} command ran by {str(msg.author)}"
		
		if lvl == self.WRN:
			prefix = "WRN"
			color = "yellow"
		elif lvl == self.ERR:
			prefix = "ERR"
			color = "red"
		elif lvl == self.CMD:
			prefix = "CMD"
			color = "green"
		elif lvl == self.FLG:
			prefix = "FLG"
			color = "magenta"
		
		cprint(f"[{channel}][{prefix}] {timestamp}: {msg}", color=color)
		self.write(f"[{channel}][{prefix}] {timestamp}: {msg}\n")


class Utilities:
	"""Utilities class"""
	
	
	@staticmethod
	def discordify(string: str) -> str:
		"""
		Replaces markdown indicators with normal characters

		Args:
			string (`str`): String to discordify

		Returns:
			`str`: Discordified string
		"""
		return string.replace("_", "\_").replace("*", "\*").replace("`", "\`").replace("~", "\~").replace(">", "\>")
	
	
	@staticmethod
	def is_admin() -> bool:
		"""
		Command decorator

		Args:
			ctx (`commands.Context`): Command context

		Returns:
			`bool`: If user is an administrator
		"""
		async def predicate(ctx: commands.Context):
			return ctx.author.guild_permissions.administrator
		return commands.check(predicate)
	
	
	@staticmethod
	def is_dev() -> bool:
		"""
		Command decorator

		Args:
			ctx (`commands.Context`): Command context

		Returns:
			`bool`: If user is a developer
		"""
		async def predicate(ctx):
			return ctx.author.id in ylcb_config.data["devs"]
		return commands.check(predicate)
	
	
	@staticmethod
	def streamer(user: discord.Member) -> bool:
		"""
		Returns if a user is a streamer

		Args:
			user (discord.Member): User to check

		Returns:
			bool: If user is a streamer
		"""
		for role in user.roles:
			if role.id == ylcb_config.data["discord"]["streamer_role_id"]: return True
		return False


ylcb_config = Config("./config/config.json")
secrets = Config("./config/secrets.json")
utilities = Utilities()
logger = Logger()

if debugging:
	prefix = ylcb_config.data["bot"]["dev_prefix"]
else:
	prefix = ylcb_config.data["bot"]["prefix"]
