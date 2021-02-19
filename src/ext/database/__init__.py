""" This is an example of a multi-file and useful extension. database - ylcb-devs """
import sqlite3

import discord
import modules.utilities as utils
from discord.ext import commands
from ext import Extension
from modules.utilities import logger as l
from modules.utilities import prefix


class database(Extension):
	"""Database Extension - ylcb-devs"""
	def __init__(self, bot: commands.Bot):
		"""Database(bot)"""
		super().__init__(bot, "ext.database")
		self.columns:dict = self.config.data["columns"]
		self.db: sqlite3.Connection	= sqlite3.connect('./src/ext/database/main.db')
	
	
	def add_new_user(self, user: discord.Member):
		params: dict = {}
		values_str = ""
		i = 1
		
		for item in self.config.data["columns"]:
			params[item["name"]] = item["default"]
			values_str += f":{item['name']},"
			i += 1
		values_str = values_str[:-1]
		params["discord_id"] = user.id
		
		self.db.execute(f"INSERT INTO Users VALUES ({values_str})", params)
		self.db.commit()
	
	
	@commands.Cog.listener()
	async def on_member_join(self, user: discord.Member):
		self.add_new_user(user)
	
	
	@commands.command(name="new", usage=f"{prefix}new [user:user]")
	async def new_member_in_db(self, ctx, user: discord.Member=None):
		"""Registers a new member into the database"""
		if not user: user = ctx.author
		if self.db.cursor().execute("SELECT * FROM Users WHERE discord_id=:d_id", {"d_id": user.id}).fetchone():
			await ctx.send(f"{ctx.author.mention}, user already in the database")
			return
		try: self.add_new_user(user)
		except: await ctx.send(f"{ctx.author.mention}, error occurred, please check ")
		else: await ctx.send(f"{ctx.author.mention}, user successfully added")


def setup(bot):
	bot.add_cog(database(bot))
