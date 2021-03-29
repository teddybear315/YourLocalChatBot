""" This is a template for a single-file extension.  - ylcb-devs """
from discord.ext import commands
from modules.extension import Extension
from modules.utilities import logger as l


class ext_name(Extension):
	"""ext_name Extension - ylcb-devs"""
	def __init__(self, bot: commands.Bot):
		"""
		ext_name(bot)

		Args:
			bot (`commands.Bot`): `commands.Bot` instance
		"""
		"""ext_name(bot)"""
		super().__init__(bot, "ext.ext_name")
		self.loop.start()
	
	
	def cog_unload(self):
		self.loop.cancel()
	
	
	@tasks.loop(hours=1)
	async def loop(self):
		pass
	
	
	@loop.before_loop
	async def before_loop(self):
		await self.bot.wait_until_ready()
	
	
	@commands.command(name=command_name, aliases=[], usage=f"{prefix}command_name [arg:str]", brief="Command brief")
	async def command_name(self, ctx, arg: str = None):
		"""
		Command brief

		Args:
			arg (`str`, optional): A simple argument. Defaults to `None`.
		"""


def setup(bot):
	bot.add_cog(ext_name(bot))
