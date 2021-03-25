import discord, datetime
from discord.ext.commands import Bot
from asyncio import sleep
from ext import games
from modules.utilities import logger as l

class game_hub:
	def __init__(self, bot: Bot, ctx):
		self.bot = bot
		self.alive = True
		self.msg: typing.Union[discord.Message, None] = None
		self.embed_dict = {
			"title":"Game Hub",
			"type": "rich",
			"timestamp": datetime.datetime.now().isoformat(),
			"color": 0x0000ff,
			"fields": [],
			"author": {
				"name": self.bot.user.display_name,
				"icon_url": str(self.bot.user.avatar_url)
			}
		}
		self.bet: int = 0
		self.prev_bet: int = 0
		self.game_outcome: int = 0
		self.session_outcome: int = 0
		self.ctx = ctx
		self.state = "menu"
		self.emoji: str = ""
		self.parent: games = self.bot.get_cog("games")
		
	async def start(self):
		while self.alive:
			await self.stateManager()
	
	async def stop(self):
		if self.msg: await self.msg.delete()
		self.alive = False
	
	def update_timestamp(self):
		self.embed_dict["timestamp"] = datetime.datetime.now().isoformat()
	
	async def betting_screen(self):
		self.update_timestamp()
		self.embed_dict["title"] = f"Bet: ${str(self.bet)}"
		self.embed_dict["fields"] = [
			{"name": "🔴", "value":"+$1", "inline":True},
			{"name": "🟠", "value":"+$5", "inline":True},
			{"name": "🟡", "value":"+$10", "inline":True},
			{"name": "🟢", "value":"+$50", "inline":True},
			{"name": "🔵", "value":"+$100", "inline":True},
			{"name": "🟣", "value":"+$500", "inline":True},
			{"name": "⚫", "value":"+$1000", "inline":True},
			{"name": "✅", "value":"Start Game", "inline":True},
			{"name": "❌", "value":"Exit Hub", "inline":True}
		]
		if self.prev_bet: self.embed_dict["fields"].append({"name": "⬅️", "value":"Previous Bet", "inline":True})
		await self.msg.edit(embed=discord.Embed.from_dict(self.embed_dict))
	
	async def menu_screen(self):
		self.embed_dict = {
			"title":"Game Hub",
			"color": 0x0000ff,
			"fields": [
				{"name": "🃏", "value": "Blackjack", "inline": True },
				{"name": "🎲", "value": "Chance Roll", "inline": True },
				{"name": "❌", "value":"Exit Hub", "inline":True }
			],
			"author": {
				"name": self.bot.user.display_name,
				"icon_url": str(self.bot.user.avatar_url)
			}
		}
		self.update_timestamp()
		
		if self.emoji:
			self.embed_dict["fields"].append({"name": "⬅️", "value":"Previous Game", "inline":True})
		if self.msg:
			await self.msg.edit(content=None, embed=discord.Embed.from_dict(self.embed_dict))
			await self.msg.clear_reactions()
		else: 
			self.msg = await self.ctx.send(embed=discord.Embed.from_dict(self.embed_dict))
		await self.msg.add_reaction("🃏")
		await self.msg.add_reaction("🎲")
		await self.msg.add_reaction("❌")
		if self.emoji: await self.msg.add_reaction("⬅️")
	
	async def stateManager(self):
		if self.state == "menu":
			await self.menu_screen()
			await sleep(0.3)
			def check(payload: discord.RawReactionActionEvent): return payload.user_id != self.bot.user and str(payload.emoji) in ["🃏","🎲","❌","⬅️"] and payload.message_id == self.msg.id
			response = await self.bot.wait_for("raw_reaction_add", check=check)
			if str(response.emoji) in ["🃏","🎲"]:
				self.emoji = str(response.emoji)
			if str(response.emoji) == "❌":
				await self.stop()
			self.state = "pre_betting"
		
		if self.state == "pre_betting":
			self.prev_bet = self.bet
			self.bet = 0
			await self.betting_screen()
			await self.msg.clear_reactions()
			await self.msg.add_reaction("🔴")
			await self.msg.add_reaction("🟠")
			await self.msg.add_reaction("🟡")
			await self.msg.add_reaction("🟢")
			await self.msg.add_reaction("🔵")
			await self.msg.add_reaction("🟣")
			await self.msg.add_reaction("⚫")
			await self.msg.add_reaction("✅")
			await self.msg.add_reaction("❌")
			if self.prev_bet: await self.msg.add_reaction("⬅️")
			self.state = "betting"
		
		while self.state == "betting":
			await sleep(0.3)
			def check(payload: discord.RawReactionActionEvent): return payload.user_id != self.bot.user and str(payload.emoji) in ["🔴","🟠","🟡","🟢","🔵","🟣","⚫","✅","❌","⬅️"] and payload.message_id == self.msg.id
			response = await self.bot.wait_for("raw_reaction_add", check=check)
			
			if str(response.emoji) == "🔴":
				self.bet += 1
			if str(response.emoji) == "🟠":
				self.bet += 5
			if str(response.emoji) == "🟡":
				self.bet += 10
			if str(response.emoji) == "🟢":
				self.bet += 50
			if str(response.emoji) == "🔵":
				self.bet += 100
			if str(response.emoji) == "🟣":
				self.bet += 500
			if str(response.emoji) == "⚫":
				self.bet += 1000
			if str(response.emoji) == "✅":
				self.state = "game"
			if str(response.emoji) == "❌":
				await self.stop()
			if str(response.emoji) == "⬅️":
				self.bet = self.prev_bet
			await self.betting_screen()
		
		if self.state == "game":
			await self.msg.clear_reactions()
			self.update_timestamp()
			self.embed_dict["fields"] =  [{"name": "Loading...", "value": "Loading game..."}]
			game = None
			if self.emoji == "🃏":
				self.embed_dict["title"] = "Games/21"
				await self.msg.edit(embed=discord.Embed.from_dict(self.embed_dict))
				game = await self.parent.blackjack(self.ctx, self.bet, 4, self.msg)
			if self.emoji == "🎲":
				self.embed_dict["title"] = "Games/Chance Roll"
				await self.msg.edit(embed=discord.Embed.from_dict(self.embed_dict))
				game = await self.parent.chance(self.ctx, self.bet, self.msg)
			if game:
				self.game_outcome = game.outcome
				self.session_outcome += game.outcome
			self.state = "confirm"
		if self.state == "confirm": 
			self.embed_dict = {
				"title":"Game/Outcome",
				"color": 0x0000ff,
				"fields": [
					{"name": "Game Outcome", "value": f"${self.game_outcome}", "inline": True },
					{"name": "Session Outcome", "value": f"${self.session_outcome}", "inline": True },
					{"name": "Current Balance", "value": f"${self.parent.econ.get_balance_from_d_id(self.ctx.author.id)}", "inline": True },
					{"name": "✅", "value":"Menu Hub", "inline":True },
					{"name": "❌", "value":"Exit Hub", "inline":True }
				],
				"author": {
					"name": self.bot.user.display_name,
					"icon_url": str(self.bot.user.avatar_url)
				}
			}
			await self.msg.edit(embed=discord.Embed.from_dict(self.embed_dict))
			await self.msg.add_reaction("✅")
			await self.msg.add_reaction("❌")
			
			await sleep(0.3)
			def check(payload: discord.RawReactionActionEvent): return payload.user_id != self.bot.user and str(payload.emoji) in ["✅","❌"] and payload.message_id == self.msg.id
			response = await self.bot.wait_for("raw_reaction_add", check=check)
			
			if str(response.emoji) == "✅":
				self.state = "menu"
			if str(response.emoji) == "❌":
				await self.stop()