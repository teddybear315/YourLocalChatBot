import discord,random,datetime,os

import modules.utilities as utils

from discord.ext.commands 	import Context
from ext 					import Extension
from modules.utilities		import logger as l

class Blackjack:
	playing = True
	card_strs = ["alert a developer if you see this", "🇦", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟", "🇯", "🇶", "🇰"]
	
	
	def __init__(self, ctx: Context, parent: Extension, bet: float):
		self.deck = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]*4
		self.bet = bet
		self.ctx = ctx
		self.parent = parent
		self.player = ctx.author
		self.dealer_hand = [1,6]
		self.player_hand = self.deal()
		self.boost = self.parent.bot.get_cog("items").get_boost_from_d_id(self.player.id)
	
	async def game(self):
		self.embed_dict = {
			"title":"Ongoing 21 Game",
			"type": "rich",
			"timestamp": datetime.datetime.now().isoformat(),
			"color": 0xffdd00,
			"author": {
				"name": self.player.display_name,
				"icon_url": str(self.player.avatar_url)
			},
			"fields": [
				{"name": "Bet:", "value": str(self.bet), "inline": True},
				{"name": "Dealer showing:", "value": self.readable_card(self.dealer_hand[0]), "inline": True},
				{"name": "Dealer's value:", "value": self.value(self.dealer_hand[0]), "inline": True},
				{"name": "My hand:", "value": self.readable(self.player_hand), "inline": True},
				{"name": "My value:", "value": self.total(self.player_hand), "inline": True}
			],
			"footer": {"text": "Directions: 🔴: Stand | 🟢: Hit"}
		}
		if self.boost:
			self.embed_dict["footer"] = {"text": f"Directions: 🔴: Stand | 🟢: Hit | {self.boost}x Boost applied"}
		if (self.total(self.dealer_hand) == 21 and len(self.dealer_hand) == 2) or (self.total(self.player_hand) == 21 and len(self.player_hand) == 2):
			self.playing = False
			await self.update_embed(self.dealer_hand, self.player_hand)
		
		self.msg: discord.Message = await self.ctx.send(embed=discord.Embed.from_dict(self.embed_dict))
		if self.playing:
			await self.msg.add_reaction("🔴")
			await self.msg.add_reaction("🟢")
		
		while self.playing:
			def check(payload: discord.RawReactionActionEvent): return payload.user_id == self.player.id and str(payload.emoji) in ["🔴","🟢"] and payload.message_id == self.msg.id
			payload = await self.parent.bot.wait_for("raw_reaction_add", check=check)
			
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
		await self.msg.edit(embed=discord.Embed.from_dict(self.embed_dict))
		await self.msg.clear_reactions()
	
	
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
		return (self.soft_17() and self.parent.config.data["games"]["blackjack"]["hit_on_soft_17"])
	
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
		card = self.deck.pop()
		hand.append(card)
		return hand
	
	
	def readable(self, hand: list) -> str:
		handStr = ""
		for card in hand:
			handStr = handStr + self.readable_card(card) + " "
		return handStr
	
	
	def readable_card(self, card: int) -> str:
		return self.card_strs[card]
	
	
	async def update_embed(self, dealer_hand, player_hand) -> dict:
		if self.playing:
			self.embed_dict["fields"] = [
				{"name": "Bet:", "value": str(self.bet), "inline": True},
				{"name": "Dealer showing:", "value": self.readable_card(self.dealer_hand[0]), "inline": True},
				{"name": "Dealer's value:", "value": self.value(self.dealer_hand[0]), "inline": True},
				{"name": "My hand:", "value": self.readable(self.player_hand), "inline": True},
				{"name": "My value:", "value": self.total(self.player_hand), "inline": True}
			]
			return self.embed_dict
		
		multiplier = 1 + self.boost
		_cfg = self.parent.config.data["games"]["blackjack"]
		
		self.embed_dict["fields"] = [
			{"name": "Bet:", "value": str(self.bet), "inline": True},
			{"name": "Dealer's hand:", "value": self.readable(self.dealer_hand), "inline": True},
			{"name": "Dealer's value:", "value": self.total(self.dealer_hand), "inline": True},
			{"name": "My hand:", "value": self.readable(self.player_hand), "inline": True},
			{"name": "My value:", "value": self.total(self.player_hand), "inline": True}
		]
		
		if self.boost: self.embed_dict["footer"] = {"text": f"{self.boost}x boost used"}
		else: self.embed_dict["footer"] = None
		
		if (self.total(self.player_hand) > self.total(self.dealer_hand) or self.total(self.dealer_hand) > 21) and self.total(self.player_hand) <= 21: ## if won
			multiplier = _cfg["small_multiplier"] + self.boost
			if self.total(self.player_hand) == 21 and len(self.player_hand) == 2: multiplier = _cfg["large_multiplier"] + self.boost
			self.parent.econ.set_balance_from_d_id(self.player.id, self.parent.econ.get_balance_from_d_id(self.player.id) + (self.bet*multiplier))
			self.embed_dict["color"] = 0x00ff00
			self.embed_dict["title"] = f"You won ${self.bet*multiplier}!"
		elif self.total(self.dealer_hand) > self.total(self.player_hand) or self.total(self.player_hand) > 21: ## if lost
			self.embed_dict["color"] = 0xff0000
			self.embed_dict["title"] = f"You lost ${self.bet}!"
		else: ## if push
			self.embed_dict["title"] = "Push!"
			self.embed_dict["color"] = 0xffdd00
			self.parent.econ.set_balance_from_d_id(self.player.id, self.parent.econ.get_balance_from_d_id(self.player.id) + self.bet)
		return self.embed_dict
