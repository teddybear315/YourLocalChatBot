import datetime
import json
import discord

from discord.ext.commands import Context
from neotermcolor import cprint
from sys import argv

class Utils:
	"""Utilities class"""
	CMD = 1
	WRN = 2
	ERR = 3
	LOG = 4

	def __init__(self, _config):
		"""Utils(config)"""
		self.config = _config
		if "--nolog" not in argv:
			self.log_file = open(f"logs/{str(datetime.datetime.now()).replace(':', '-')}.txt", "a+")


	def vip(self, author: discord.Member):
		"""Returns if user is a vip"""
		for role in author.roles:
			if role.id == self.config["discord"]["vip_role_id"]: return True
		return False

	def streamer(self, user: discord.Member):
		"""Returns if a user is a streamer"""
		for role in user.roles:
			if role.id == self.config["discord"]["streamer_role_id"]: return True
		return False

	def dev(self, author: discord.Member):
		"""Returns if user is a developer"""
		if author.id in self.config["devs"]: return True
		return False

	def editConfig(self, fp, value):
		"""Edits a config file with a dictionary"""
		json_str = json.dumps(value)
		with open(f"config/{fp}", "w+") as f:
			f.write(json_str)
			f.close()

	def reloadConfig(self, configFP = "config.json"):
		"""
		Loads a config file (json formatted) into a variable
		Usage: configFile = reloadConfig(configFile)
		"""
		fp = f"config/{configFP}"
		_json = json.dumps(json.load(open(fp)))
		with open(fp, "w+") as f:
			f.write(_json)
			f.close()
		return json.load(open(fp))

	def log(self, msg, lvl = LOG): # TODO add logging to files
		"""Decent logging system"""
		logString = f"{datetime.datetime.now().isoformat(timespec='seconds')}: {msg}"
		if type(msg) is Context:
			logString = f"{datetime.datetime.now().isoformat(timespec='seconds')}: {msg.command.name} command ran by {msg.author.name}#{msg.author.discriminator}"
			lvl = self.CMD
		if lvl == self.WRN:
			cprint(f"[WRN] {logString}", color="yellow")
			self.log_file.write(f"[WRN] {logString}\n")
		elif lvl == self.ERR:
			cprint(f"[ERR] {logString}", color="red")
			self.log_file.write(f"[ERR] {logString}\n")
		elif lvl == self.CMD:
			cprint(f"[CMD] {logString}", color="green")
			self.log_file.write(f"[CMD] {logString}\n")
		else:
			print(f"[LOG] {logString}")
			self.log_file.write(f"[LOG] {logString}\n")