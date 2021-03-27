""" This is an example of a multi-file and useful extension. database - ylcb-devs """
import sqlite3
from sys import argv

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
		if "--debug" not in argv: self.db: sqlite3.Connection	= sqlite3.connect('./src/ext/database/main.db')
		else: self.db: sqlite3.Connection	= sqlite3.connect('./src/ext/database/testing.db')
	
	
	def add_new_user_from_id(self, _id):
		params: dict = {}
		values_str = ""
		
		for item in self.config.data["columns"]:
			params[item["name"]] = item["default"]
			values_str += f":{item['name']},"
		values_str = values_str[:-1]
		params["discord_id"] = _id
		
		self.db.execute(f"INSERT INTO Users VALUES ({values_str})", params)
		self.db.commit()
	def exist_check_from_id(self, _id):
		try:
			self.db.cursor().execute("SELECT discord_id FROM Users WHERE discord_id=:d_id", {"d_id": _id}).fetchone()
		except:
			self.add_new_user(_id)
	def select(self, search_table, select_column, search_column, search_value):
		if type(search_value) == int and search_column == "discord_id": self.exist_check_from_id(search_value)
		return self.db.cursor().execute(f"SELECT {select_column} FROM {search_table} WHERE {search_column}={search_value}").fetchone()[0]
	def update(self, set_table, set_column, set_value, search_column, search_value):
		if type(search_value) == int and search_column == "discord_id": self.exist_check_from_id(search_value)
		self.db.execute(f"UPDATE {set_table} SET {set_column}={set_value} WHERE {search_column}={search_value}")
		self.db.commit()
	
	@commands.Cog.listener()
	async def on_member_join(self, user: discord.Member):
		self.add_new_user(user.id)
	
	
	@commands.command(name="new", usage=f"{prefix}new [user:user]")
	async def new_member_in_db(self, ctx, user: discord.Member=None):
		"""Registers a new member into the database"""
		if not user: user = ctx.author
		if self.db.cursor().execute("SELECT * FROM Users WHERE discord_id=:d_id", {"d_id": user.id}).fetchone():
			await ctx.send(f"{ctx.author.mention}, user already in the database")
			return
		try: self.add_new_user(user.id)
		except: await ctx.send(f"{ctx.author.mention}, error occurred, please check ")
		else: await ctx.send(f"{ctx.author.mention}, user successfully added")


def setup(bot):
	bot.add_cog(database(bot))
