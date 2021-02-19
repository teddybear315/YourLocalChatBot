import discord, datetime

from modules.utilities import logger as l, utilities as u, prefix

from discord.ext import commands
from discord.ext.commands import Context
from ext import Extension


class items(Extension):
	"""Items Extension - ylcb-devs"""
	def __init__(self, bot: commands.Bot):
		"""items(bot)"""
		super().__init__(bot, "ext.items")
		self.db = bot.get_cog("database").db
	
	
	def get_inventory_from_d_id(self, discord_id: int)							-> list	:
		"""Returns given user's inventory"""
		inv = self.db.cursor().execute("SELECT inventory FROM Users WHERE discord_id=:d_id", {"d_id": discord_id}).fetchone()[0]
		inv = [int(x) for x in inv.split(",")]
		l.log(inv, l.FLG, l.DISCORD)
		return inv
	def set_inventory_from_d_id(self, discord_id: int, inventory: list)			-> list	:
		"""Returns and sets the given user's inventory value to inventory"""
		self.db.execute("UPDATE Users SET inventory=:inv WHERE discord_id=:d_id", {"inv": ",".join([str(_item) for _item in inventory]), "d_id": discord_id})
		self.db.commit()
		return inventory
	def get_item_from_id(self, item_id: int)									-> dict	:
		"""Returns an item object from its id"""
		return self.config.data["items"][item_id]
	def add_item_to_inventory_from_d_id(self, discord_id: int, item_id: int)	-> int	:
		"""Returns and adds an item to the given user's inventory"""
		inv: list = self.get_inventory_from_d_id(discord_id).append(item_id)
		self.set_inventory_from_d_id(discord_id, inv)
		return self.get_item_from_id(item_id)
	def trash_item_from_d_id(self, discord_id: int, item_id: int)				-> dict	:
		"""Returns and deletes a given item from a given user's inventory"""
		inv = self.get_inventory_from_d_id(discord_id)
		done = False
		for i,inv_item_id in enumerate(inv):
			if inv_item_id == item_id and not done:
				inv.pop(i)
				done = True
		self.set_inventory_from_d_id(discord_id, inv)
		return self.get_item_from_id(item_id)
	def get_boost_from_d_id(self, discord_id: int)								-> float:
		"""Returns given user's current boost value"""
		return float(self.db.cursor().execute("SELECT boost FROM Users WHERE discord_id=:d_id", {"d_id": discord_id}).fetchone()[0])
	def set_boost_from_d_id(self, discord_id: int, boost_value: int)			-> int	:
		"""Returns and sets given users boost value to boost_value"""
		self.db.cursor().execute("UPDATE Users SET boost=:value WHERE discord_id=:d_id", {"value": boost_value, "d_id": discord_id})
		self.db.commit()
		return boost_value
	def reset_boost_from_d_id(self, discord_id: int)							-> int	:
		"""Returns and sets user's boost value to 0"""
		return self.set_boost_from_d_id(discord_id, 0)
	def inventory_str_to_list(self, inventory_str: str)							-> list	:
		"""Parses and returns inventory object from items"""
		return ",".split(inventory_str)
	
	
	@commands.command(name="give_item", usage=f"{prefix}give <reciever:user> <item_id:int>")
	async def give_item(self, ctx, reciever: discord.Member, item_id): 
		item = self.trash_item_from_d_id(ctx.author.id, item_id)
		self.add_item_to_inventory_from_d_id(reciever.id, item["id"])
		await ctx.send(f"{ctx.author.mention}, you have given {item.name} to {reciever.mention}")
	
	
	@commands.command(name="view", usage=f"{prefix}view <item_id:int>")
	async def view_item(self, ctx, item_id: int):
		"""Inspect an item"""
		item = self.get_item_from_id(item_id)
		embed_dict = {
			"title": item["name"],
			"type": "image",
			"description": item["desc"],
			"image": {"url": item["texture_url"]},
			"timestamp": datetime.datetime.now().isoformat(),
			"color": 0x6275be,
			"author": {
				"name": ctx.author.display_name,
				"icon_url": str(ctx.author.avatar_url)
			}
		}
		await ctx.send(embed=discord.Embed.from_dict(embed_dict))
	
	
	@commands.command(name="boosts", aliases=["boost"], usage=f"{prefix}boosts")
	async def boosts(self, ctx):
		"""See your active boost"""
		boost = self.get_boost_from_d_id(ctx.author.id)
		if boost:
			await ctx.send(f"{ctx.author.mention}, you currently have a {boost}x boost")
			return
		await ctx.send(f"{ctx.author.mention}, you currently have no active boost")
	
	
	@commands.command(name="inventory", aliases=["inv"], usage=f"{prefix}inventory [user:user]")
	async def open_inventory(self, ctx, user: discord.Member = None):
		"""Open your inventory"""
		if not user: user = ctx.author
		inv = self.get_inventory_from_d_id(user.id)
		fields = []
		if not inv:
			fields = [{"name": "Your inventory is empty :(", "value": "Get items from airdrops!"}]
		else:
			for _id in inv:
				item = self.get_item_from_id(_id)
				fields.append({"name": f"{item['name']} [#{_id}]", "value": item["desc"], "inline":True})
		embed_dict = {
			"title":"Inventory",
			"type": "rich",
			"timestamp": datetime.datetime.now().isoformat(),
			"color": 0x6275be,
			"fields": fields,
			"author": {
				"name": user.display_name,
				"icon_url": str(user.avatar_url)
			}
		}
		await ctx.send(embed=discord.Embed.from_dict(embed_dict))
	
	
	@commands.command(name="use", aliases=["activate"], usage=f"{prefix}use")
	async def use_item(self, ctx, item_id: int):
		"""Use a booster if able to boost"""
		boost = self.get_boost_from_d_id(ctx.author.id)
		item = self.get_item_from_id(item_id)
		inv = self.get_inventory_from_d_id(ctx.author.id)
		if item["id"] not in inv:
			await ctx.send(f"{ctx.author.mention}, this item is not in your inventory")
			return
		if boost != 0:
			await ctx.send(f"{ctx.author.mention}, you already have another item being used")
			return
		if item["type"] != "boost":
			await ctx.send(f"{ctx.author.mention}, this item cannot be used")
			return
		self.trash_item_from_d_id(ctx.author.id, item_id)
		self.set_boost_from_d_id(ctx.author.id, item["effect"])
		await ctx.send(f"{ctx.author.mention}, you have used this {item['name']}")
	
	
	#ANCHOR admin commands
	
	@commands.command(name="set_boost", hidden=True)
	@u.is_admin()
	async def set_booster(self, ctx, user: discord.Member, booster_value: int):
		"""Set a user's booster value"""
		try: self.set_boost_from_d_id(user.id, booster_value)
		except Exception as e: l.log(e, l.ERR, l.DISCORD)
		else: await ctx.send(f"{ctx.author.mention}, {user.mention}'s booster value was set to {booster_value}")
	@set_booster.error
	async def set_booster_error(self, ctx, error):
		if isinstance(error, commands.CheckFailure):
			await ctx.send(f"{ctx.author.mention}, this command can only be used by admins")
	
	
	@commands.command(name="set_inventory", hidden=True)
	@u.is_admin()
	async def set_inventory(self, ctx, user: discord.Member, items: str):
		"""Set's a user's inventory value"""
		try: self.set_inventory_from_d_id(user.id, self.inventory_str_to_list(items))
		except Exception as e: l.log(e, l.ERR, l.DISCORD)
		else: await ctx.send(f"{ctx.author.mention}, {user.mention}'s inventory value was set to {items}")
	@set_inventory.error
	async def set_inventory_error(self, ctx, error):
		if isinstance(error, commands.CheckFailure):
			await ctx.send(f"{ctx.author.mention}, this command can only be used by admins")
	
	
	@commands.command(name="add_to_inventory", hidden=True)
	@u.is_admin()
	async def add_to_inventory(self, ctx, user: discord.Member, item_id: int):
		"""Adds item to inventory"""
		try: self.add_item_to_inventory_from_d_id(user.id, item_id)
		except Exception as e: l.log(e, l.ERR, l.DISCORD)
		else: await ctx.send(f"{ctx.author.mention},  {self.get_item_from_id(item_id)['name']} was added to {user.mention}'s inventory")
	@add_to_inventory.error
	async def add_to_inventory_error(self, ctx, error):
		if isinstance(error, commands.CheckFailure):
			await ctx.send(f"{ctx.author.mention}, this command can only be used by admins")
	
	
	@commands.command(name="remove_from_inventory", hidden=True)
	@u.is_admin()
	async def remove_from_inventory(self, ctx, user: discord.Member, item_id: int):
		"""Removes item from inventory"""
		try: self.trash_item_from_d_id(user.id, item_id)
		except Exception as e: l.log(e, l.ERR, l.DISCORD)
		else: await ctx.send(f"{ctx.author.mention},  {self.get_item_from_id(item_id)['name']} was removed from {user.mention}'s inventory")
	@remove_from_inventory.error
	async def remove_from_inventory_error(self, ctx, error):
		if isinstance(error, commands.CheckFailure):
			await ctx.send(f"{ctx.author.mention}, this command can only be used by admins")

def setup(bot):
	bot.add_cog(items(bot))