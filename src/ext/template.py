""" This is a template for a single-file extension.  - ylcb-devs """
from discord.ext import commands
from modules.utilities import logger as l

from ext import Extension


class ext_name(Extension):
	"""ext_name Extension - ylcb-devs"""
	def __init__(self, bot: commands.Bot):
		"""ext_name(bot)"""
		super().__init__(bot, "ext.ext_name")
		self.loop.start()
	
	
	def cog_unload(self):
		self.loop.cancel()
	
	
	@tasks.loop(hours=1)
	async def loop(self):
		pass
	
	
	@loop.before_loop
	async def before_airdrop_spawner(self):
		await self.bot.wait_until_ready()


def setup(bot):
	bot.add_cog(ext_name(bot))
