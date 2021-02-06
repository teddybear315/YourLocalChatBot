import discord,datetime

import modules.utilities as utils

from discord.ext 			import commands
from ext 					import Extension
from modules.utilities		import logger as l


class economy(Extension):
	"""Economy Extension - ylcb-devs"""
	def __init__(self, bot: commands.Bot):
		"""Economy(bot)"""
		super().__init__(bot, "ext.economy")
		self.requirements = self.config.data["requirements"]
		self.db = bot.get_cog("database").db
	
	
	def get_bal_from_d_id(self, discord_id) -> float:
		return self.db.cursor().execute("SELECT balance FROM Users WHERE discord_id=:d_id", {"d_id": discord_id}).fetchone()[0]
	def get_bal_from_username(self, username) -> float:
		return self.db.cursor().execute("SELECT balance FROM Users WHERE username=:username", {"username": username}).fetchone()[0]
	def set_balance_from_d_id(self, bal, discord_id):
		self.db.execute("UPDATE Users SET balance=:bal WHERE discord_id=:d_id", {"bal": bal, "d_id": discord_id})
		self.db.commit()
	def set_balance_from_username(self, bal, username):
		self.db.execute("UPDATE Users SET balance=:bal WHERE username=:username", {"bal": bal, "username": username})
		self.db.commit()
	def can_pay_amount(self, sender: discord.Member, amount) -> bool:
		"""Returns if balance was paid"""
		snd_bal = self.get_bal_from_d_id(sender.id)
		if snd_bal < amount:
			return False
		return True
	
	
	@commands.command(name="balance")
	async def balance(self,ctx, user: discord.Member = None):
		l.log(ctx)
		if not user: user = ctx.author
		points = self.get_bal_from_d_id(user.id)
		embed_dict = {
			"title":"Bank",
			"type": "rich",
			"timestamp": datetime.datetime.now().isoformat(),
			"color": 0x00ff00,
			"fields": [
				{"name": "Balance", "value": "$"+str(points)}
			],
			"author": {
				"name": user.display_name,
				"icon_url": str(user.avatar_url)
			}
		}
		embed = discord.Embed.from_dict(embed_dict)
		await ctx.send(embed=embed)
	
	
	@commands.command(name="pay")
	async def pay(self,ctx,payee: discord.Member, amount: float = 50, *, message: str = None):
		l.log(ctx)
		amount = round(amount, 2)
		if self.can_pay_amount(ctx.author, amount):
			l.log(f"Check: {ctx.author.display_name}#{ctx.author.discriminator} | Amount:${amount} | Reciever:{payee.display_name}#{payee.discriminator} | Status: AWAITING APPROVAL")
			snd_bal = self.get_bal_from_d_id(ctx.author.id)
			self.set_balance_from_d_id(snd_bal-amount, ctx.author.id)
			embed_dict = {
				"title":"Check [AWAITING APPROVAL]",
				"type": "rich",
				"timestamp": datetime.datetime.now().isoformat(),
				"color": 0xff8800,
				"fields": [
					{"name": "Pay To:", "value": payee.display_name+"#"+payee.discriminator, "inline":True},
					{"name": "Balance:", "value": "$"+str(amount), "inline":True},
					{"name": "From:", "value": ctx.author.display_name+"#"+ctx.author.discriminator, "inline":True},
				]
			}
			if message: embed_dict["fields"].append({"name": "Message:", "value": message})
			
			embed = discord.Embed.from_dict(embed_dict)
			msg: dicsord.Message = await ctx.send(f"Are you sure you want to pay this user ${amount}",embed=embed)
			await msg.add_reaction("✅")
			await msg.add_reaction("❎")
			def check(reaction: discord.Reaction, user: discord.Member): return user == ctx.author and str(reaction.emoji) in ["✅", "❎"]
			reaction, user = await self.bot.wait_for("reaction_add", check=check)
			
			if str(reaction.emoji) == "✅":
				embed_dict["title"] = "Check [PENDING]"
				l.log(f"Check: {ctx.author.display_name}#{ctx.author.discriminator} | Amount:${amount} | Reciever:{payee.display_name}#{payee.discriminator} | Status: APPROVED,PENDING")
			elif str(reaction.emoji) == "❎":
				await msg.delete()
				await ctx.delete()
				snd_bal = self.get_bal_from_d_id(ctx.author.id)
				self.set_balance_from_d_id(snd_bal+amount, ctx.author.id)
				l.log(f"Check: {ctx.author.display_name}#{ctx.author.discriminator} | Amount:${amount} | Reciever:{payee.display_name}#{payee.discriminator} | Status: CANCELED")
			
			embed = discord.Embed.from_dict(embed_dict)
			await msg.edit(content=payee.mention,embed=embed)
			def check(reaction: discord.Reaction, user: discord.Member): return user == payee and str(reaction.emoji) in ["✅", "❎"]
			reaction, user = await self.bot.wait_for("reaction_add", check=check)
			
			if str(reaction.emoji) == "✅":
				embed_dict["title"] = "Check [ACCEPTED]"
				embed_dict["color"] = 0x00ff00
				rec_bal = self.get_bal_from_d_id(payee.id)
				self.set_balance_from_d_id(rec_bal+amount, payee.id)
				l.log(f"Check: {ctx.author.display_name}#{ctx.author.discriminator} | Amount:${amount} | Reciever:{payee.display_name}#{payee.discriminator} | Status: ACCEPTED,PAID")
			elif str(reaction.emoji) == "❎":
				embed_dict["title"] = "Check [DECLINED]"
				embed_dict["color"] = 0xff0000
				l.log(f"Check: {ctx.author.display_name}#{ctx.author.discriminator} | Amount:${amount} | Reciever:{payee.display_name}#{payee.discriminator} | Status: DECLINED,REFUNDED")
				snd_bal = self.get_bal_from_d_id(ctx.author.id)
				self.set_balance_from_d_id(snd_bal+amount, ctx.author.id)
		else:
			l.log(f"Check: {ctx.author.display_name}#{ctx.author.discriminator} | Amount:${amount} | Reciever:{payee.display_name}#{payee.discriminator} | Status: BANK DECLINED")
			await ctx.send(f"{ctx.author.mention}, you only have ${self.get_bal_from_d_id(ctx.author.id)}")
		embed_dict["timestamp"] = datetime.datetime.now().isoformat()
		await msg.edit(content=None, embed=discord.Embed.from_dict(embed_dict))
		try: await msg.clear_reactions()
		except Exception as e: l.log(e, l.WRN)
	
	
	@commands.command(name="request")
	async def request(self,ctx,sender: discord.Member, amount: float = 50, *, message: str = None):
		l.log(ctx)
		if self.can_pay_amount(sender, amount):
			l.log(f"Money Request: {ctx.author.display_name}#{ctx.author.discriminator} | Amount:${amount} | Payer:{sender.display_name}#{sender.discriminator} | Status: APPROVED,PENDING")
			embed_dict = {
				"title":"Money Request [PENDING]",
				"type": "rich",
				"timestamp": datetime.datetime.now().isoformat(),
				"color": 0xff8800,
				"fields": [
					{"name": "Pay To:", "value": ctx.author.display_name+"#"+ctx.author.discriminator, "inline":True},
					{"name": "Balance:", "value": "$"+str(amount), "inline":True},
					{"name": "From:", "value": sender.display_name+"#"+sender.discriminator, "inline":True},
				]
			}
			if message: embed_dict["fields"].append({"name": "Message:", "value": message})
			
			embed = discord.Embed.from_dict(embed_dict)
			msg: dicsord.Message = await ctx.send(sender.mention,embed=embed)
			await msg.add_reaction("✅")
			await msg.add_reaction("❎")
			def check(reaction: discord.Reaction, user: discord.Member): return user == sender and str(reaction.emoji) in ["✅", "❎"]
			reaction, user = await self.bot.wait_for("reaction_add", check=check)
			
			if str(reaction.emoji) == "✅":
				embed_dict["title"] = "Money Request [ACCEPTED]"
				embed_dict["color"] = 0x00ff00
				rec_bal = self.get_bal_from_d_id(ctx.author.id)
				self.set_balance_from_d_id(rec_bal+amount, ctx.author.id)
				l.log(f"Money Request: {ctx.author.display_name}#{ctx.author.discriminator} | Amount:${amount} | Payer:{sender.display_name}#{sender.discriminator} | Status: ACCEPTED,PAID")
			elif str(reaction.emoji) == "❎":
				embed_dict["title"] = "Money Request [DECLINED]"
				embed_dict["color"] = 0xff0000
				l.log(f"Money Request: {ctx.author.display_name}#{ctx.author.discriminator} | Amount:${amount} | Payer:{sender.display_name}#{sender.discriminator} | Status: DECLINED,REFUNDED")
				snd_bal = self.get_bal_from_d_id(sender.id)
				self.set_balance_from_d_id(snd_bal+amount, sender.id)
		else:
			l.log(f"Money Request: {ctx.author.display_name}#{ctx.author.discriminator} | Amount:${amount} | Payer:{sender.display_name}#{sender.discriminator} | Status: DECLINED")
			await ctx.send(f"{ctx.author.mention}, that user has insufficient funds!")
		embed_dict["timestamp"] = datetime.datetime.now().isoformat()
		await msg.edit(content=None, embed=discord.Embed.from_dict(embed_dict))
		try: await msg.clear_reactions()
		except Exception as e: l.log(e, l.WRN)


def setup(bot):
	bot.add_cog(economy(bot))