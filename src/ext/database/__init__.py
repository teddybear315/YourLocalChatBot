""" This is an example of a multi-file and useful extension. database - ylcb-devs """
import discord, sqlite3

import modules.utilities as utils
from modules.utilities import logger as l

from discord.ext 			import commands
from ext 					import Extension


class database(Extension):
	"""Database Extension - ylcb-devs"""
	def __init__(self, bot: commands.Bot):
		"""Database(bot)"""
		super().__init__(bot, "ext.database")
		self.columns:dict = self.config.data["columns"]
		self.db: sqlite3.Connection	= sqlite3.connect('src/ext/database/main.db')
	
	
	@commands.Cog.listener()
	async def on_member_join(self, user: discord.Member):
		self.db.execute(
			"INSERT INTO Users VALUES (:username,:id,:d_id,:json,:bal,:inventory)", 
			{
				"username": None,
				"id": None,
				"d_id": user.id,
				"json": "{}",
				"bal": 100,
				"inventory": "{}"
			}
		)
		self.db.commit()
	
	
	@commands.command(name="new")
	async def new_member_in_db(self, ctx):
		l.log(ctx)
		if self.db.cursor().execute("SELECT * FROM Users WHERE discord_id=:d_id", {"d_id": ctx.author.id}).fetchone():
			await ctx.send(f"{ctx.author.mention}, you're already in the database")
			return
		self.db.execute(
			"INSERT INTO Users VALUES (:username,:id,:d_id,:json,:bal,:inventory)", 
			{
				"username": None,
				"id": None,
				"d_id": ctx.author.id,
				"json": "{}",
				"bal": 100,
				"inventory": "{}"
			}
		)
		self.db.commit()


def setup(bot):
	bot.add_cog(database(bot))