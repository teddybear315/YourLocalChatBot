import datetime
import json
from asyncio import sleep

import discord
import modules.utilities as utils
from discord.ext import commands
from modules.extension import Extension
from modules.utilities import logger as l
from modules.utilities import prefix
from modules.utilities import utilities as u


class economy(Extension):
	"""
	Economy Extension - ylcb-devs
	"""
	def __init__(self, bot: commands.Bot):
		"""
		economy(bot)

		Args:
			bot (`commands.Bot`): commands.Bot instance
		"""
		super().__init__(bot, "ext.economy")
		self.db = bot.get_cog("database").db
	
	
	def get_balance_from_d_id(self, discord_id: int)										-> float:
		"""
		Returns a user's balance

		Args:
			discord_id (int): User's id

		Returns:
			float: Balance
		"""
		return self.db.execute("SELECT balance FROM Users WHERE discord_id=?", (discord_id,)).fetchone()[0]
	def set_balance_from_d_id(self, discord_id: int, bal: int)								-> float:
		"""
		Set a user's balance

		Args:
			discord_id (int): User's id
			bal (int): New balance value

		Returns:
			float: Balance
		"""
		self.db.cursor().execute("UPDATE Users SET balance=? WHERE discord_id=?", (round(bal,2), discord_id))
		self.db.commit()
		return round(bal, 2)
	def can_pay_amount(self, discord_id: int, amount: int)									-> bool :
		"""
		Returns if a user can pay amount

		Args:
			discord_id (int): User's id
			amount (int): Amount to pay

		Returns:
			bool: If user can pay amount
		"""
		snd_bal = self.get_balance_from_d_id(discord_id)
		return snd_bal > amount
	def get_transaction_history_from_id(self, discord_id: int)								-> list :
		"""
		Return a user's transaction history

		Args:
			discord_id (int): User's id

		Returns:
			list: Transaction History
		"""
		th = self.db.execute("SELECT transaction_history FROM Users WHERE discord_id=?", (discord_id,)).fetchone()[0]
		return json.loads(th.replace("\'","\""))
	def set_transaction_history_from_id(self, discord_id: int, value: list) 				-> list :
		"""
		Set a user's transaction history

		Args:
			discord_id (int): User's id
			value (list): New transaction history

		Returns:
			list: value
		"""
		self.db.cursor().execute("UPDATE Users SET transaction_history=? WHERE discord_id=?", (str(value), discord_id))
		self.db.commit()
		return value
	def clear_transaction_history_from_id(self, discord_id: int)							-> dict :
		"""
		Clear a user's transaction history

		Args:
			discord_id (int): User's id

		Returns:
			dict: Empty array
		"""
		return self.set_transaction_history_from_id(discord_id, [])
	def push_transaction_history_from_id(self, discord_id: int, place: str, amount: float)	-> dict :
		"""
		Push an entry to a user's transaction history

		Args:
			discord_id (int): User's id
			place (str): Place money was spent
			amount (float): Amount of money spent

		Returns:
			dict: New transaction history value
		"""
		thCur: list = self.get_transaction_history_from_id(discord_id)
		if len(thCur) >= 3:
			for x in range(len(thCur) - 2):
				thCur.pop()
		thCur.insert(0,{"place": place, "amount": amount})
		self.set_transaction_history_from_id(discord_id, thCur)
		return thCur
	
	@commands.command(name="balance", aliases=["bal"], usage=f"{prefix}balance [user:user]", brief="Returns you or another user's balance")
	async def balance(self, ctx, user: discord.Member = None):
		"""
		Returns you or another user's balance

		Args:
			user (`discord.Member`, optional): User to get balance for. Defaults to `None`.
		"""
		if not user: user = ctx.author
		points = self.get_balance_from_d_id(user.id)
		th: list = self.get_transaction_history_from_id(user.id)
		description: str = ""
		if th:
			description = "Transaction History\nYour 3 recent transactions\n\n"
			for entry in th:
				entry: dict
				if entry["amount"] > 0 : emoji = "🟩"
				else: emoji = "🟥"
				if len(entry["place"]) > 20: 
					entry["place"] = entry["place"][:20]
					entry["place"][19] = "…"
				description = description + f"{emoji} {entry['place'].ljust(20,'.')} ${str(entry['amount'])}\n"
		embed_dict = {
			"title":f"${str(points)}",
			"description": description,
			"type": "rich",
			"timestamp": datetime.datetime.now().isoformat(),
			"color": 0x00ff00,
			"author": {
				"name": u.discordify(user.display_name),
				"icon_url": str(user.avatar_url)
			}
		}
		await ctx.send(embed=discord.Embed.from_dict(embed_dict))
	
	
	@commands.command(name="leaderboard", aliases=["lb"], usage=f"{prefix}leaderboard", brief="Show server leaderboard")
	async def leaderboard(self, ctx):
		"""
		Show server leaderboard
		"""
		lb: list = self.db.execute("SELECT * FROM Users ORDER BY balance DESC").fetchmany(5)
		
		lb_total: int = 0
		fields: list = []
		for entry in lb: lb_total += entry[4]
		for i, entry in enumerate(lb):
			entry_user = await self.bot.fetch_user(entry[2])
			fields.append({"name": f"{i+1}. {u.discordify(entry_user.display_name)}", "value": f"({str(round(entry[4]/lb_total*100, 1))}%) ${'{:,}'.format(entry[4])}"})
		embed_dict = {
			"title":f"Leaderboard (${lb_total})",
			"type": "rich",
			"timestamp": datetime.datetime.now().isoformat(),
			"color": 0x00cc99,
			"fields": fields,
			"author": {
				"name": u.discordify(self.bot.user.display_name),
				"icon_url": str(self.bot.user.avatar_url)
			}
		}
		await ctx.send(embed=discord.Embed.from_dict(embed_dict))
	
	
	@commands.command(name="pay", usage=f"{prefix}pay <receiver:user> [amount:float=50] [message:str]", brief="Pay another user")
	async def pay(self, ctx, reciever: discord.Member, amount: float = 50, *, message: str = None):
		"""
		Pay another user

		Args:
			reciever (`discord.Member`): Person to pay money to
			amount (`float`, optional): Amount to pay. Defaults to `50`.
			message (`str`, optional): Message to user. Defaults to `None`.
		"""
		if reciever == ctx.author:
			await ctx.send(f"{ctx.author.mention}, you cannot send money to yourself")
			return
		amount = round(amount, 2)
		if self.can_pay_amount(ctx.author.id, amount):
			l.log(f"Check: {u.discordify(ctx.author.name)}#{ctx.author.discriminator} | Amount:${amount} | Reciever:{reciever.name}#{reciever.discriminator} | Status: AWAITING APPROVAL", channel=l.DISCORD)
			self.set_balance_from_d_id(ctx.author.id, self.get_balance_from_d_id(ctx.author.id)-amount)
			embed_dict = {
				"title":"Check [AWAITING APPROVAL]",
				"type": "rich",
				"timestamp": datetime.datetime.now().isoformat(),
				"color": 0xff8800,
				"fields": [
					{"name": "Pay To:", "value": u.discordify(reciever.name)+"#"+reciever.discriminator, "inline":True},
					{"name": "Balance:", "value": "$"+str(amount), "inline":True},
					{"name": "From:", "value": u.discordify(ctx.author.name)+"#"+ctx.author.discriminator, "inline":True},
				]
			}
			if message: embed_dict["fields"].append({"name": "Message:", "value": message})
			
			embed = discord.Embed.from_dict(embed_dict)
			msg: dicsord.Message = await ctx.send(f"Are you sure you want to pay this user ${amount}",embed=embed)
			await msg.add_reaction("✅")
			await msg.add_reaction("❎")
			await sleep(0.3)
			def check(payload: discord.RawReactionActionEvent): return payload.user_id == ctx.author.id and str(payload.emoji) in ["✅", "❎"] and payload.message_id == msg.id
			payload = await self.bot.wait_for("raw_reaction_add", check=check)
			
			if str(payload.emoji) == "✅":
				embed_dict["title"] = "Check [PENDING]"
				l.log(f"Check: {ctx.author.name}#{ctx.author.discriminator} | Amount:${amount} | Reciever:{reciever.name}#{reciever.discriminator} | Status: APPROVED,PENDING", channel=l.DISCORD)
			elif str(payload.emoji) == "❎":
				await msg.delete()
				await ctx.message.delete()
				self.set_balance_from_d_id(ctx.author.id, self.get_balance_from_d_id(ctx.author.id)+amount)
				l.log(f"Check: {ctx.author.name}#{ctx.author.discriminator} | Amount:${amount} | Reciever:{reciever.name}#{reciever.discriminator} | Status: CANCELED", channel=l.DISCORD)
			
			embed = discord.Embed.from_dict(embed_dict)
			await msg.edit(content=reciever.mention,embed=embed)
			
			await sleep(0.3)
			def check(payload: discord.RawReactionActionEvent): return payload.member == reciever and str(payload.emoji) in ["✅", "❎"] and payload.message_id == msg.id
			payload = await self.bot.wait_for("raw_reaction_add", check=check)
			
			if str(payload.emoji) == "✅":
				embed_dict["title"] = "Check [ACCEPTED]"
				embed_dict["color"] = 0x00ff00
				try:
					self.set_balance_from_d_id(reciever.id, self.get_balance_from_d_id(reciever.id)-amount)
					self.push_transaction_history_from_id(ctx.author.id, "Transfer", -1*amount)
				except Exception as e: l.log(e, l.ERR, l.DISCORD)
				else:self.set_balance_from_d_id(ctx.author.id, self.get_balance_from_d_id(ctx.author.id)+amount)
				self.set_balance_from_d_id(reciever.id, self.get_balance_from_d_id(reciever.id)+amount)
				self.push_transaction_history_from_id(reciever.id, "Transfer", amount)
				l.log(f"Check: {ctx.author.name}#{ctx.author.discriminator} | Amount:${amount} | Reciever:{reciever.name}#{reciever.discriminator} | Status: ACCEPTED,PAID", channel=l.DISCORD)
			elif str(payload.emoji) == "❎":
				embed_dict["title"] = "Check [DECLINED]"
				embed_dict["color"] = 0xff0000
				l.log(f"Check: {ctx.author.name}#{ctx.author.discriminator} | Amount:${amount} | Reciever:{reciever.name}#{reciever.discriminator} | Status: DECLINED,REFUNDED", channel=l.DISCORD)
				self.set_balance_from_d_id(ctx.author.id, self.get_balance_from_d_id(ctx.author.id)+amount)
			embed_dict["timestamp"] = datetime.datetime.now().isoformat()
			await msg.edit(content=None, embed=discord.Embed.from_dict(embed_dict))
			try: await msg.clear_reactions()
			except Exception as e: l.log(e, l.WRN, l.DISCORD)
		else:
			l.log(f"Check: {ctx.author.name}#{ctx.author.discriminator} | Amount:${amount} | Reciever:{reciever.name}#{reciever.discriminator} | Status: BANK DECLINED", channel=l.DISCORD)
			await ctx.send(f"{ctx.author.mention}, you only have ${self.get_balance_from_d_id(ctx.author.id)}")
	
	
	@commands.command(name="request", aliases=["req"], usage=f"{prefix}request <sender:user> [amount:float=50] [message:str]", brief="Request money from another user")
	async def request(self, ctx, sender: discord.Member, amount: float = 50, *, message: str = None):
		"""
		Request money from another user

		Args:
			sender (`discord.Member`): User you want money from
			amount (`float`, optional): Amount to request. Defaults to `50`.
			message (`str`, optional): Message to user. Defaults to `None`.
		"""
		if sender == ctx.author:
			await ctx.send(f"{ctx.author.mention}, you cannot request money from yourself")
			return
		if self.can_pay_amount(sender.id, amount):
			l.log(f"Money Request: {ctx.author.name}#{ctx.author.discriminator} | Amount:${amount} | Payer:{sender.name}#{sender.discriminator} | Status: APPROVED,PENDING", channel=l.DISCORD)
			embed_dict = {
				"title":"Money Request [PENDING]",
				"type": "rich",
				"timestamp": datetime.datetime.now().isoformat(),
				"color": 0xff8800,
				"fields": [
					{"name": "Pay To:", "value": u.discordify(ctx.author.name)+"#"+ctx.author.discriminator, "inline":True},
					{"name": "Balance:", "value": "$"+str(amount), "inline":True},
					{"name": "From:", "value": u.discordify(sender.name)+"#"+sender.discriminator, "inline":True},
				]
			}
			if message: embed_dict["fields"].append({"name": "Message:", "value": message})
			
			embed = discord.Embed.from_dict(embed_dict)
			msg: dicsord.Message = await ctx.send(sender.mention,embed=embed)
			await msg.add_reaction("✅")
			await msg.add_reaction("❎")
			
			await sleep(0.3)
			def check(payload: discord.RawReactionActionEvent): return payload.member == sender and str(payload.emoji) in ["✅", "❎"] and payload.message_id == msg.id
			payload = await self.bot.wait_for("raw_reaction_add", check=check)
			
			if str(payload.emoji) == "✅":
				embed_dict["title"] = "Money Request [ACCEPTED]"
				embed_dict["color"] = 0x00ff00
				try:
					self.set_balance_from_d_id(sender.id, self.get_balance_from_d_id(sender.id)-amount)
					self.push_transaction_history_from_id(sender.id, "Transfer", amount*-1)
				except Exception as e: l.log(e, l.ERR, l.DISCORD)
				else: self.set_balance_from_d_id(ctx.author.id, self.get_balance_from_d_id(ctx.author.id)+amount)
				self.push_transaction_history_from_id(ctx.author.id, "Transfer", amount)
				l.log(f"Money Request: {ctx.author.display_name}#{ctx.author.discriminator} | Amount:${amount} | Payer:{sender.display_name}#{sender.discriminator} | Status: ACCEPTED,PAID", channel=l.DISCORD)
			elif str(payload.emoji) == "❎":
				embed_dict["title"] = "Money Request [DECLINED]"
				embed_dict["color"] = 0xff0000
				l.log(f"Money Request: {ctx.author.display_name}#{ctx.author.discriminator} | Amount:${amount} | Payer:{sender.display_name}#{sender.discriminator} | Status: DECLINED,REFUNDED", channel=l.DISCORD)
				self.set_balance_from_d_id(sender.id, self.get_balance_from_d_id(sender.id)+amount)
			embed_dict["timestamp"] = datetime.datetime.now().isoformat()
			await msg.edit(content=None, embed=discord.Embed.from_dict(embed_dict))
			try: await msg.clear_reactions()
			except Exception as e: l.log(e, l.WRN, l.DISCORD)
		else:
			l.log(f"Money Request: {ctx.author.display_name}#{ctx.author.discriminator} | Amount:${amount} | Payer:{sender.display_name}#{sender.discriminator} | Status: DECLINED", channel=l.DISCORD)
			await ctx.send(f"{ctx.author.mention}, that user has insufficient funds!")
	
	
	@commands.command(name="go_broke", aliases=["0"], usage=f"{prefix}go_broke", brief="Go broke")
	async def go_broke(self, ctx):
		"""
		Go broke
		"""
		try:
			self.set_balance_from_d_id(ctx.author.id, 0)
			self.clear_transaction_history_from_id(ctx.author.id)
		except Exception as e: l.log(e, l.ERR, l.DISCORD)
		else: await ctx.send(f"{ctx.author.mention}, congrats you're broke...")
	
	
	#ANCHOR admin commands
	
	@commands.command(name="set_balance", hidden=True)
	@u.is_admin()
	async def set_balance(self, ctx, user: discord.Member, amount: float = 0):
		"""Set the given user's balance to amount"""
		try:
			self.set_balance_from_d_id(user.id, amount)
			self.clear_transaction_history_from_id(user.id)
			self.push_transaction_history_from_id(user.id, "Admin Set Amount", amount)
		except Exception as e: l.log(e, l.ERR, l.DISCORD)
		else: await ctx.send(f"{ctx.author.mention}, {user.mention}'s balance is now ${amount}")
	@set_balance.error
	async def set_balance_error(self, ctx, error):
		if isinstance(error, commands.CheckFailure):
			await ctx.send(f"{ctx.author.mention}, this command can only be used by admins")
	
	
	@commands.command(name="add_balance", hidden=True)
	@u.is_admin()
	async def add_balance(self, ctx, user: discord.Member, amount: float):
		"""Add an amount to the given user's balance"""
		try: 
			self.set_balance_from_d_id(user.id, self.get_balance_from_d_id(user.id) + amount)
			self.push_transaction_history_from_id(ctx.author.id, "Admin Added Amount", amount)
		except Exception as e: l.log(e, l.ERR, l.DISCORD)
		else: await ctx.send(f"{ctx.author.mention}, {user.mention}'s balance is now ${self.get_balance_from_d_id(user.id)}")
	@add_balance.error
	async def add_balance_error(self, ctx, error):
		if isinstance(error, commands.CheckFailure):
			await ctx.send(f"{ctx.author.mention}, this command can only be used by admins")
	
	
	@commands.command(name="sub_balance", hidden=True)
	@u.is_admin()
	async def sub_balance(self, ctx, user: discord.Member, amount: float):
		"""Subtract an amount from the given user's balance"""
		try:
			self.set_balance_from_d_id(user.id, self.get_balance_from_d_id(user.id) - amount)
			self.push_transaction_history_from_id(ctx.author.id, "Admin Removed Amount", amount*-1)
		except Exception as e: l.log(e, l.ERR, l.DISCORD)
		else: await ctx.send(f"{ctx.author.mention}, {user.mention}'s balance is now ${self.get_balance_from_d_id(user.id)}")
	@sub_balance.error
	async def sub_balance_error(self, ctx, error):
		if isinstance(error, commands.CheckFailure):
			await ctx.send(f"{ctx.author.mention}, this command can only be used by admins")
	
	


def setup(bot):
	bot.add_cog(economy(bot))
