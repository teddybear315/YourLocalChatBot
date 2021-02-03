import datetime, json, gzip, discord

from discord.ext.commands import Context
from neotermcolor import cprint
from sys import argv

class Config:
	"""Config class"""
	
	def __init__(self, path: str = "config.json"):
		"""Config()"""
		self.path = f"config/{path}"
		if __debug__: self.path = f"config/DEBUG {path}"
		self.data: dict
		self.updateData()
	
	
	def updateFile(self) -> None:
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
	CMD = 1
	WRN = 2
	ERR = 3
	LOG = 4
	FLG = 5
	
	
	def __init__(self):
		"""Logger()"""
		self.log_file_path = f"logs/{str(datetime.datetime.now()).replace(':', '-')}.log"
	
	
	def log(self, msg, lvl = LOG):
		"""Decent logging system"""
		timestamp = str(datetime.datetime.now().isoformat(timespec='seconds')).replace('T', ' ')
		log_file = open(self.log_file_path, "a+")
		
		if type(msg) is Context:
			logString = f"{timestamp}: {msg.command.name} command ran by {msg.author.name}#{msg.author.discriminator}"
			lvl = CMD
		else: logString = f"{timestamp}: {msg}"
		
		if lvl == WRN:
			cprint(f"[WRN] {logString}", color="yellow")
			log_file.write(f"[WRN] {logString}\n")
		elif lvl == ERR:
			cprint(f"[ERR] {logString}", color="red")
			log_file.write(f"[ERR] {logString}\n")
		elif lvl == CMD:
			cprint(f"[CMD] {logString}", color="green")
			log_file.write(f"[CMD] {logString}\n")
		elif lvl == FLG:
			cprint(f"[FLG] {logString}", color="magenta")
			log_file.write(f"[FLG] {logString}\n")
		else:
			print(f"[LOG] {logString}")
			log_file.write(f"[LOG] {logString}\n")
		gzip.compress(9)
		log_file.close()


class Utilities:
	"""Utilities class"""
	@staticmethod
	def admin(author: discord.Member) -> bool:
		"""Returns if user is an admin"""
		if author.guild_permissions.administrator: return True
		return False
	
	
	@staticmethod
	def streamer(user: discord.Member) -> bool:
		"""Returns if a user is a streamer"""
		for role in user.roles:
			if role.id == ylcb_config.data["discord"]["streamer_role_id"]: return True
		return False
	
	
	@staticmethod
	def dev(author: discord.Member) -> bool:
		"""Returns if user is a developer"""
		if author.id in ylcb_config.data["devs"]: return True
		return False


ylcb_config = Config("config.json")
secrets = Config("secrets.json")
utilities = Utilities()
logger = Logger()