""" This is an example of a multi-file and useful extension. database - ylcb-devs """
import discord
import sqlite3

import modules.utilities as utils

from discord.ext 			import commands
from ext 					import Extension


class database(Extension):
	"""Database Extension - ylcb-devs"""
	def __init__(self, bot: commands.Bot):
		"""Database(bot)"""
		super().__init__(
			bot,
			"ext.database",
			config=utils.Config("exts/database.json")
		)
		self.columns:dict = self.config.data["columns"]
		self.db: sqlite3.Connection	= sqlite3.connect('src/ext/database/main.db')
	
	
	@commands.Cog.listener()
	async def on_member_join(self, user: discord.Member):
		self.db.execute(
			"INSERT INTO Users VALUES (:username,:id,:d_id,:json,:bal)", 
			{
				"username": None,
				"id": None,
				"d_id": user.id,
				"json": "{}",
				"bal": 100
			}
		)
		self.db.commit()

	# if db.find({"discord_id": str(user.id)}):
	# 	db.delete_one({"discord_id": str(user.id)})


def setup(bot):
	bot.add_cog(database(bot))