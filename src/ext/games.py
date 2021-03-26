import datetime
import os
import random
from asyncio import sleep
from sys import argv
from typing import Union

import discord
import modules.utilities as utils
from discord.ext import commands, tasks
from ext import Extension
from modules.utilities import logger as l
from modules.utilities import prefix, secrets
from modules.utilities import utilities as u
from modules.utilities import ylcb_config

class games(Extension):
	"""Games Extension - ylcb-devs"""
	def __init__(self, bot: commands.Bot):
		"""Games(bot)"""
		super().__init__(bot, "ext.games")
		self.econ = bot.get_cog("economy")
		self.db = bot.get_cog("database").db
		self.items = bot.get_cog("items")
		self.airdrop_spawner.start()
	
	
	def cog_unload(self):
		self.airdrop_spawner.cancel()
	
	
	@tasks.loop(hours=1)
	async def airdrop_spawner(self):
		if "--debug" in argv:
			return
		chance = random.randint(1,100)
		if chance < 60:
			l.log("Airdrop Spawned")
			money = random.randint(10,1000)
			embed_dict = {
				"title":"Airdrop!",
				"type": "rich",
				"timestamp": datetime.datetime.now().isoformat(),
				"color": 0xff8800,
				"fields": [
					{"name": "Money:", "value": "$"+str(money)}
				],
				"author": {
					"name": self.bot.user.display_name,
					"icon_url": str(self.bot.user.avatar_url)
				}
			}
			
			rand_id = random.randint(1,10)
			try: item = self.items.get_item_from_id(rand_id)
			except: item = None
			if item: embed_dict["fields"].append({"name": "Contains:", "value": "1x "+item["name"]})
			
			embed = discord.Embed.from_dict(embed_dict)
			channel = await self.bot.fetch_channel(ylcb_config.data["discord"]["event_channel_id"])
			
			msg: discord.Message = await channel.send("@here", embed=embed)
			await msg.add_reaction("🛄")
			await sleep(0.3)
			def check(payload: discord.RawReactionActionEvent): return payload.user_id != self.bot.user and str(payload.emoji) == "🛄" and payload.message_id == msg.id
			payload = await self.bot.wait_for("raw_reaction_add", check=check)
			claimed = False
			user = await self.bot.fetch_user(payload.user_id)
			try:
				self.econ.set_balance_from_d_id(payload.user_id, self.econ.get_balance_from_d_id(payload.user_id) + money)
				self.econ.push_transaction_history_from_id(payload.user_id, "Airdrop", money)
				if item: self.items.add_item_to_inventory_from_d_id(payload.user_id, item["id"])
			except: claimed = False
			else:
				claimed = True
				l.log(f"{user.display_name}#{user.discriminator} claimed an airdrop worth ${money}", channel=l.DISCORD)
			
			if claimed:
				embed_dict["title"] = "Claimed!"
				embed_dict["timestamp"] = datetime.datetime.now().isoformat()
				embed_dict["color"] = 0x00ff00
				embed_dict["author"] = {
					"name": user.display_name,
					"icon_url": str(user.avatar_url)
				}
			else:
				embed_dict["title"] = "Error!"
				embed_dict["timestamp"] = datetime.datetime.now().isoformat()
				embed_dict["color"] = 0xff0000
				embed_dict["fields"] = [{
					"name": "Error:", "value": "There was an error collecting airdrop rewards"
				}]
			embed = discord.Embed.from_dict(embed_dict)
			await msg.edit(content=None, embed=embed)
	
	
	@airdrop_spawner.before_loop
	async def before_airdrop_spawner(self):
		await self.bot.wait_until_ready()
	
	
	
	@commands.command(name="hub", aliases=["games"], usage=f"{prefix}hub")
	async def hub(self, ctx):
		hub = Hub(self.bot, ctx)
		await hub.start()
		del hub
	
	
	@commands.command(name="chance", usage=f"{prefix}chance <bet:float>")
	async def chance(self, ctx, bet: float = None):
		game = Dice(self.bot,ctx,bet)
		await game.start()
		del game
	
	@commands.command(name="21", aliases=["bj", "blackjack"], usage=f"{prefix}21 <bet:float> [decks:int]")
	async def blackjack(self, ctx, bet: float = 0, decks: int = 4):
		game = Blackjack(self.bot,ctx,bet,decks=decks)
		await game.start()
		del game
	
	async def can_user_play(self, ctx, _cfg: dict, bet: float, points: float, msg):
		bet = round(bet, 2)
		if not self.config.data["enabled"] or not _cfg["enabled"]:
			await ctx.send(f"{ctx.author.mention}, this game has been disabled by an admin.")
			return False
		if points < bet:
			if not msg: await ctx.send(f"{ctx.author.mention}, you only have ${points} to bet!")
			if msg: await msg.edit(f"{ctx.author.mention}, you only have ${points} to bet")
			return False
		if _cfg["min_bet"] < 1:
			_cfg["min_bet"] = 1
			self.config.updateFile()
			l.log("min_bet was lower than 1, min_bet was set to 1", l.FLG)
		if bet > _cfg["max_bet"] and _cfg["max_bet"] != 0:
			await ctx.send(f"{ctx.author.mention}, the max bet is {_cfg['max_bet']}")
			return False
		return True


def setup(bot):
	bot.add_cog(games(bot))


class StateManager:
	def __init__(self, states: list, state: tuple):
		self.states = states
		self.state = state
		# 	self.game = ["checks", "game", "check_failed", "error", "outcome"]
		# 	self.hub = [State("menu"), "betting", "game", "error", "outcome"]
	def set_state(self, new_state):
		for old_state in self.states:
			if old_state == new_state:
				l.log(f"Set State:{self.state}<-{new_state}")
				self.state = new_state
	def get_state(self):
		return self.state


class Hub:
	def __init__(self, bot, ctx):
		self.bot = bot
		self.alive = True
		self.msg = None
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
		self.bet: float = 0
		self.prev_bet: float = 0
		self.game_outcome: float = 0
		self.session_outcome: float = 0
		self.games_played = 0
		self.ctx = ctx
		self.player = ctx.author
		
		self.emoji: str = ""
		self.cog: games = self.bot.get_cog("games")
		
		self.state_menu = "menu", self.menu
		self.state_betting = "betting", self.betting
		self.state_game = "game", self.m_game
		self.state_error = "error", self.error
		self.state_outcome = "outcome", self.m_outcome
		self.state_exit = "exit", self.m_exit
		
		self.gsm: StateManager = StateManager([self.state_menu, self.state_betting, self.state_game, self.state_error, self.state_outcome, self.state_exit], self.state_menu)
	
	
	async def start(self):
		while self.alive:
			await self.gsm.get_state()[1]()
	
	
	async def stop(self):
		self.alive = False
	
	
	async def m_exit(self):
		self.embed_dict = {
			"title":"Game/Session",
			"color": 0x00ff00,
			"fields": [
				{"name": "Games Played", "value": f"{self.games_played}", "inline": True },
				{"name": "Session Outcome", "value": f"${self.session_outcome}", "inline": True },
				{"name": "Avg. $ per Game", "value": f"${(self.session_outcome/(self.games_played if self.games_played else 1))}", "inline": True },
				{"name": "Current Balance", "value": f"${self.cog.econ.get_balance_from_d_id(self.player.id)}", "inline": True },
			],
			"author": {
				"name": self.player.display_name,
				"icon_url": str(self.player.avatar_url)
			},
		}
		await self.msg.edit(embed=discord.Embed.from_dict(self.embed_dict))
		await self.msg.clear_reactions()
		await self.gsm.get_state()[1]()
		await self.stop()
	
	
	def update_timestamp(self):
		self.embed_dict["timestamp"] = datetime.datetime.now().isoformat()
	
	
	async def betting_screen(self):
		self.update_timestamp()
		self.embed_dict = {
			"title": f"Bet: ${str(self.bet)}",
			"color": 0x0000ff,
			"fields": [
				{"name": "🔴", "value":"+$1", "inline":True},
				{"name": "🟠", "value":"+$5", "inline":True},
				{"name": "🟡", "value":"+$10", "inline":True},
				{"name": "🟢", "value":"+$50", "inline":True},
				{"name": "🔵", "value":"+$100", "inline":True},
				{"name": "🟣", "value":"+$500", "inline":True},
				{"name": "⚫", "value":"+$1000", "inline":True},
				{"name": "✅", "value":"Start Game", "inline":True},
			],
			"author": {
				"name": self.bot.user.display_name,
				"icon_url": str(self.bot.user.avatar_url)
			}
		}
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
		else: 
			self.msg = await self.ctx.send(embed=discord.Embed.from_dict(self.embed_dict))
		await self.msg.clear_reactions()
		await self.msg.add_reaction("🃏")
		await self.msg.add_reaction("🎲")
		await self.msg.add_reaction("❌")
		if self.emoji: await self.msg.add_reaction("⬅️")
	
	
	async def menu(self):
		await self.menu_screen()
		await sleep(0.3)
		def check(payload: discord.RawReactionActionEvent): return payload.user_id != self.bot.user and str(payload.emoji) in ["🃏","🎲","❌","⬅️"] and payload.message_id == self.msg.id
		response = await self.bot.wait_for("raw_reaction_add", check=check)
		if str(response.emoji) in ["🃏","🎲"]:
			self.emoji = str(response.emoji)
		if str(response.emoji) == "❌":
			self.gsm.set_state(self.state_exit)
		else:
			self.gsm.set_state(self.state_betting)
	
	
	async def betting(self):
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
		if self.prev_bet: await self.msg.add_reaction("⬅️")
		
		await sleep(0.3)
		betting = True
		while betting:
			def check(payload: discord.RawReactionActionEvent): return payload.user_id != self.bot.user and str(payload.emoji) in ["🔴","🟠","🟡","🟢","🔵","🟣","⚫","✅","❌","⬅️"] and payload.message_id == self.msg.id
			response = await self.bot.wait_for("raw_reaction_add", check=check)
			
			if str(response.emoji) == "🔴": self.bet += 1
			if str(response.emoji) == "🟠": self.bet += 5
			if str(response.emoji) == "🟡": self.bet += 10
			if str(response.emoji) == "🟢": self.bet += 50
			if str(response.emoji) == "🔵": self.bet += 100
			if str(response.emoji) == "🟣": self.bet += 500
			if str(response.emoji) == "⚫": self.bet += 1000
			if str(response.emoji) == "✅": betting = False
			if str(response.emoji) == "⬅️": self.bet = self.prev_bet
			await self.betting_screen()
		self.games_played += 1
		self.gsm.set_state(self.state_game)
	
	
	async def m_game(self):
		await self.msg.clear_reactions()
		self.update_timestamp()
		self.embed_dict["fields"] =  [{"name": "Loading...", "value": "Loading game..."}]
		game = None
		if self.emoji == "🃏":
			self.embed_dict["title"] = "Games/21"
			await self.msg.edit(embed=discord.Embed.from_dict(self.embed_dict))
			game = Blackjack(self.bot,self.ctx,self.bet,self,self.msg)
		if self.emoji == "🎲":
			self.embed_dict["title"] = "Games/Chance Roll"
			await self.msg.edit(embed=discord.Embed.from_dict(self.embed_dict))
			game = Dice(self.bot,self.ctx,self.bet,self,self.msg)
		if game:
			await game.start()
			self.game_outcome = game.outcome
			self.session_outcome += game.outcome
		else:
			self.gsm.set_state(self.state_error)
		self.gsm.set_state(self.state_outcome)
	
	
	async def m_outcome(self):
		self.embed_dict = {
			"title":"Game/Outcome",
			"color": 0x00ff00,
			"fields": [
				{"name": "Game Outcome", "value": f"${self.game_outcome}", "inline": True },
				{"name": "Session Outcome", "value": f"${self.session_outcome}", "inline": True },
				{"name": "Current Balance", "value": f"${self.cog.econ.get_balance_from_d_id(self.player.id)}", "inline": True },
			],
			"author": {
				"name": self.player.display_name,
				"icon_url": str(self.player.avatar_url)
			},
			"footer": {"text": "Directions: ✅: Home | ❌: Exit"}
		}
		await self.msg.edit(embed=discord.Embed.from_dict(self.embed_dict))
		await self.msg.add_reaction("✅")
		await self.msg.add_reaction("❌")
		
		await sleep(0.3)
		def check(payload: discord.RawReactionActionEvent): return payload.user_id != self.bot.user and str(payload.emoji) in ["✅","❌"] and payload.message_id == self.msg.id
		response = await self.bot.wait_for("raw_reaction_add", check=check)
		
		if str(response.emoji) == "✅":
			self.gsm.set_state(self.state_menu)
		if str(response.emoji) == "❌":
			self.gsm.set_state(self.state_exit)
	
	
	async def error(self):
		self.embed_dict = {
			"title":"Game Hub/Error",
			"type": "rich",
			"timestamp": datetime.datetime.now().isoformat(),
			"color": 0xff0000,
			"fields": [
				{"name": "Error", "value": "It appears your game has errored...", "inline": True}
			],
			"author": {
				"name": self.bot.user.display_name,
				"icon_url": str(self.bot.user.avatar_url)
			},
			"footer": {"text": "Directions: ⬅️: Home | ❌: Exit"}
		}
		
		await self.msg.edit(embed=discord.Embed.from_dict(self.embed_dict))
		await self.msg.clear_reactions()
		await self.msg.add_reaction("⬅️")
		await self.msg.add_reaction("❌")
		
		await sleep(0.3)
		def check(payload: discord.RawReactionActionEvent): return payload.user_id != self.bot.user and str(payload.emoji) in ["🔴","🟠","🟡","🟢","🔵","🟣","⚫","✅","❌","⬅️"] and payload.message_id == self.msg.id
		response = await self.bot.wait_for("raw_reaction_add", check=check)
		
		if str(response.emoji) == "⬅️":
			self.gsm.set_state(self.state_menu)
		if str(response.emoji) == "❌":
			self.gsm.set_state(self.state_exit)


class Game:
	def __init__(self, bot, ctx, bet: float, hub: Hub = None, msg: discord.Message = None):
		self.outcome = 0
		self.bet = bet
		self.bot = bot
		self.hub = hub
		self.ctx = ctx
		self.alive = True
		self.playing = False
		self.player = ctx.author
		self.econ = bot.get_cog("economy")
		if hub: 
			self.in_hub = True
			self.msg = msg
		else:
			self.in_hub = False
			self.msg = None
		self.boost = self.bot.get_cog("items").get_boost_from_d_id(self.player.id)
		self.cog: game_cog = self.bot.get_cog("games")


class CardGame(Game):
	def __init__(self, bot, ctx, bet: float, hub: Hub = None, msg = None, decks: int = 4):
		super().__init__(bot, ctx, bet, hub, msg)
		self.card_strs = ["alert a developer if you see this", "🇦", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟", "🇯", "🇶", "🇰"]
		self.decks = decks
		self.deck = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]*decks


class Blackjack(CardGame):
	def __init__(self, bot, ctx, bet: float, hub: Hub = None, msg = None, decks: int = 4): 
		super().__init__(bot, ctx, bet, hub, msg, decks)
		self.dealer_hand = self.deal()
		self.player_hand = self.deal()
		
		self.alive = True
		
		self.state_check = "check", self.check
		self.state_game = "game", self.game
		self.state_check_failed = "check_failed", self.check_failed
		self.state_error = "error", self.error
		self.state_outcome = "outcome", self.outcome_func
		
		self.gsm: StateManager = StateManager([self.state_check, self.state_game, self.state_check_failed, self.state_error, self.state_outcome], self.state_check)
	
	
	async def start(self):
		while self.alive:
			await self.gsm.get_state()[1]()
	
	
	async def stop(self):
		self.alive = False
	
	
	async def check(self):
		if not (self.bet or self.decks or self.hub):
			self.ctx.send(f"{self.player.mention}, please specify a bet or decks")
			self.gsm.set_state(self.state_check_failed)
			return
		if not await self.cog.can_user_play(self.ctx, self.cog.config.data["games"]["blackjack"], self.bet, self.cog.econ.get_balance_from_d_id(self.player.id), self.msg):
			self.gsm.set_state(self.state_check_failed)
			return
		self.gsm.set_state(self.state_game)
	
	
	async def check_failed(self):
		if self.in_hub: await self.hub.state_check_failed[1]()
		else: await self.stop()
	
	
	async def error(self):
		if self.in_hub: await self.hub.state_error[1]()
		else: await self.stop()
	
	
	async def game(self):
		self.econ.set_balance_from_d_id(self.player.id, self.econ.get_balance_from_d_id(self.player.id) - self.bet)
		l.log(f"Blackjack start: {self.player.display_name}#{self.player.discriminator} | Bet:${self.bet}", channel=l.DISCORD)
		self.playing = True
		self.embed_dict = {
			"title":"Ongoing 21 Game",
			"type": "rich",
			"color": 0xffdd00,
			"author": {
				"name": self.player.display_name,
				"icon_url": str(self.player.avatar_url)
			},
			"footer": {"text": "Directions: 🔴: Stand | 🟢: Hit"}
		}
		if self.boost: self.embed_dict["footer"] = {"text": f"Directions: 🔴: Stand | 🟢: Hit | {self.boost}x Boost applied"}
		await self.update_embed(self.dealer_hand, self.player_hand)
		if (self.total(self.dealer_hand) == 21 and len(self.dealer_hand) == 2) or (self.total(self.player_hand) == 21 and len(self.player_hand) == 2):
			self.playing = False
			self.gsm.set_state(self.state_outcome)
			return
		
		if not self.in_hub: self.msg = await self.ctx.send(embed=discord.Embed.from_dict(self.embed_dict))
		else: await self.msg.edit(embed=discord.Embed.from_dict(self.embed_dict))
		
		await self.msg.add_reaction("🔴")
		await self.msg.add_reaction("🟢")
		
		while self.playing:
			await sleep(0.3)
			def check(payload: discord.RawReactionActionEvent): return payload.user_id == self.player.id and str(payload.emoji) in ["🔴","🟢"] and payload.message_id == self.msg.id
			payload = await self.bot.wait_for("raw_reaction_add", check=check)
			
			if str(payload.emoji) == "🟢":
				self.hit(self.player_hand)
				if self.total(self.player_hand) > 21: 
					self.playing = False
					await self.update_embed(self.dealer_hand, self.player_hand)
			elif str(payload.emoji) == "🔴":
				self.playing = False
				while self.total(self.dealer_hand) < 17 or self.s17_hit():
					self.hit(self.dealer_hand)
			await self.update_embed(self.dealer_hand, self.player_hand)
			await self.msg.edit(embed=discord.Embed.from_dict(self.embed_dict))
		await self.msg.clear_reactions()
		self.gsm.set_state(self.state_outcome)
	
	
	async def outcome_func(self):
		self.multiplier = 1 + self.boost
		_cfg = self.cog.config.data["games"]["blackjack"]
		
		self.embed_dict["fields"] = [
			{"name": "Dealer's hand:", "value": self.readable(self.dealer_hand), "inline": True},
			{"name": "Dealer's value:", "value": self.total(self.dealer_hand), "inline": True},
			{"name": "Bet:", "value": f"${self.bet}", "inline": True},
			{"name": "My hand:", "value": self.readable(self.player_hand), "inline": True},
			{"name": "My value:", "value": self.total(self.player_hand), "inline": True}
		]
		
		if self.boost: self.embed_dict["footer"] = {"text": f"{self.boost}x boost used"}
		else: self.embed_dict["footer"] = None
		
		if (self.total(self.player_hand) > self.total(self.dealer_hand) or self.total(self.dealer_hand) > 21) and self.total(self.player_hand) <= 21: ## if won
			self.multiplier = _cfg["small_multiplier"] + self.boost
			if self.total(self.player_hand) == 21 and len(self.player_hand) == 2: self.multiplier = _cfg["large_multiplier"] + self.boost
			payout = self.bet * self.multiplier
			self.outcome = payout - self.bet
			self.cog.econ.set_balance_from_d_id(self.player.id, self.cog.econ.get_balance_from_d_id(self.player.id) + payout)
			self.cog.econ.push_transaction_history_from_id(self.player.id, "Blackjack", payout)
			if not self.in_hub:
				self.embed_dict["color"] = 0x00ff00
				self.embed_dict["title"] = f"You won ${payout}!"
		elif self.total(self.dealer_hand) > self.total(self.player_hand) or self.total(self.player_hand) > 21: ## if lost
			self.outcome = self.bet*-1
			self.cog.econ.push_transaction_history_from_id(self.player.id, "Blackjack", self.outcome)
			if not self.in_hub:
				self.embed_dict["color"] = 0xff0000
				self.embed_dict["title"] = f"You lost ${self.bet}!"
		else: ## if push
			self.outcome = 0
			self.cog.econ.set_balance_from_d_id(self.player.id, self.cog.econ.get_balance_from_d_id(self.player.id) + self.bet)
			if not self.in_hub:
				self.embed_dict["title"] = "Push!"
				self.embed_dict["color"] = 0xffdd00
		
		self.cog.items.reset_boost_from_d_id(self.player.id)
		l.log(f"Blackjack outcome: {self.player.display_name}#{self.player.discriminator}:{Blackjack.total(self.player_hand)} | Bet:${self.bet} | Multiplier:{self.multiplier}x ({self.boost}) | CPU:{Blackjack.total(self.dealer_hand)}", channel=l.DISCORD)
		if not self.in_hub: 
			try: await self.msg.edit(embed=discord.Embed.from_dict(self.embed_dict))
			except: self.msg = self.ctx.send(embed=discord.Embed.from_dict(self.embed_dict))
		await self.stop()
	
	
	def deal(self) -> list:
		hand = []
		for i in range(2):
			random.shuffle(self.deck)
			card = self.deck.pop()
			hand.append(card)
		return hand
	
	
	def soft_17(self) -> bool:
		return (1 in self.dealer_hand and self.total(self.dealer_hand) == 17)
	
	
	def s17_hit(self) -> bool:
		return (self.soft_17() and self.cog.config.data["games"]["blackjack"]["hit_on_soft_17"])
	
	
	@staticmethod
	def total(hand: list) -> int:
		aces = Blackjack.check_for_ace(hand)
		total = 0
		for card in hand:
			if card in [11,12,13]:
				total += 10
			elif card == 1:
				if total >= 11: total += 1
				else: total += 11
			else: total += card
		while aces > 1 and total > 21:
			total -= 10
			aces -= 1
		return total
	
	
	@staticmethod
	def value(card: int) -> int:
		if card in [11,12,13]:
			return 10
		elif card == 1:
			return 11
		else: return card
	
	
	@staticmethod
	def check_for_ace(hand) -> int:
		"""Returns number of aces in hand"""
		aces = 0
		for i in hand: 
			if i == 1: aces += 1
		return aces
	
	
	def hit(self, hand: list) -> list:
		"""Adds card to a hand"""
		card = self.deck.pop()
		hand.append(card)
		return hand
	
	
	def readable(self, hand: list) -> str:
		"""Makes hand printable"""
		handStr = ""
		for card in hand:
			handStr = handStr + self.readable_card(card) + " "
		return handStr
	
	
	def readable_card(self, card: int) -> str:
		"""Makes card printable"""
		return self.card_strs[card]
	
	
	async def update_embed(self, dealer_hand, player_hand) -> dict:
		self.embed_dict["fields"] = [
			{"name": "Dealer showing:", "value": self.readable_card(self.dealer_hand[0]), "inline": True},
			{"name": "Dealer's value:", "value": self.value(self.dealer_hand[0]), "inline": True},
			{"name": "Bet:", "value": f"${self.bet}", "inline": True},
			{"name": "My hand:", "value": self.readable(self.player_hand), "inline": True},
			{"name": "My value:", "value": self.total(self.player_hand), "inline": True}
		]
		return self.embed_dict


class Dice(Game):
	def __init__(self, bot, ctx, bet: float, hub: Hub = None, msg = None): 
		super().__init__(bot, ctx, bet, hub, msg)
		
		self.state_check = "check", self.check
		self.state_game = "game", self.game
		self.state_check_failed = "check_failed", self.check_failed
		self.state_error = "error", self.error
		self.state_outcome = "outcome", self.outcome_func
		
		self.gsm: StateManager = StateManager([self.state_check, self.state_game, self.state_check_failed, self.state_error, self.state_outcome], self.state_check)
	
	
	async def start(self):
		while self.alive:
			await self.gsm.get_state()[1]()
	
	
	async def stop(self):
		self.alive = False
	
	
	async def check(self):
		if not (self.bet or self.hub):
			await self.ctx.send(f"{self.player.mention}, please specify a bet")
			self.gsm.set_state(self.state_check_failed)
			return
		if not await self.cog.can_user_play(self.ctx, self.cog.config.data["games"]["blackjack"], self.bet, self.cog.econ.get_balance_from_d_id(self.player.id), self.msg):
			self.gsm.set_state(self.state_check_failed)
			return
		self.gsm.set_state(self.state_game)
	
	
	async def check_failed(self):
		if self.in_hub: await self.hub.state_check_failed[1]()
		else: await self.stop()
	
	
	async def error(self):
		if self.in_hub: await self.hub.state_error[1]()
		else: await self.stop()
	
	
	async def game(self):
		self.econ.set_balance_from_d_id(self.player.id, self.econ.get_balance_from_d_id(self.player.id) - self.bet)
		l.log(f"Chance start: {self.player.name}#{self.player.discriminator} | Bet:${self.bet}", channel=l.DISCORD)
		self.playing = True
		self.p_score   = random.randint(2,12)
		self.cpu_score = random.randint(2,12)
		self.gsm.set_state(self.state_outcome)
	
	
	async def outcome_func(self):
		points = self.cog.econ.get_balance_from_d_id(self.player.id)
		_cfg = self.cog.config.data["games"]["chance"]
		embed_dict = {
			"title":"It\'s a push!",
			"type": "rich",
			"timestamp": datetime.datetime.now().isoformat(),
			"color": 0xffdd00,
			"fields": [
				{"name": "You scored:", "value": self.p_score, "inline": True},
				{"name": "I scored:", "value": self.cpu_score, "inline": True}
			]
		}
		
		self.boost = self.cog.items.get_boost_from_d_id(self.player.id)
		multiplier = 1 + self.boost
		if self.p_score > self.cpu_score:
			multiplier = _cfg["small_multiplier"] + self.boost
			if self.p_score == 2: multiplier = _cfg["large_multiplier"] + self.boost
			payout = self.bet*multiplier
			self.outcome = payout - self.bet
			self.cog.econ.set_balance_from_d_id(self.player.id, points + payout)
			self.cog.econ.push_transaction_history_from_id(self.player.id, "Chance Roll", self.outcome)
			if not self.in_hub:
				embed_dict["color"] = 0x00ff00
				embed_dict["title"] = f"You won ${payout}!"
		elif self.cpu_score > self.p_score:
			self.outcome = self.bet*-1
			if not self.in_hub:
				embed_dict["color"] = 0xff0000
				embed_dict["title"] = f"You lost ${self.bet}!"
			self.cog.econ.push_transaction_history_from_id(self.player.id, "Chance Roll", self.outcome)
		elif self.cpu_score == self.p_score:
			self.cog.econ.set_balance_from_d_id(self.player.id, points + self.bet)
		l.log(f"Chance outcome: {self.player.name}#{self.player.discriminator}:{self.p_score} | Bet:${self.bet} | Multiplier:{multiplier}x ({self.boost}) | CPU:{self.cpu_score}", channel=l.DISCORD)
		if not self.in_hub:
			try: await self.msg.edit(embed=discord.Embed.from_dict(embed_dict))
			except: self.msg = self.ctx.send(embed=discord.Embed.from_dict(embed_dict))
		await self.stop()