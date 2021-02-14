import discord,random,datetime,os

import modules.utilities as utils

from discord.ext.commands 	import Context
from ext 					import Extension
from modules.utilities		import logger as l

class Blackjack:
	deck = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]*4
	playing = True
	
	async def game(self, ctx: Context, ext: Extension, bet: float):
		self.bet = bet
		self.ctx = ctx
		self.ext = ext
		self.dealer_hand = self.deal()
		self.player_hand = self.deal()
		
		self.embed_dict = {
			"title":"Ongoing 21 Game",
			"type": "rich",
			"timestamp": datetime.datetime.now().isoformat(),
			"color": 0xffdd00,
			"fields": [
				{"name": "Bet:", "value": str(self.bet), "inline": True},
				{"name": "Dealer showing:", "value": self.readable_card(self.dealer_hand[0]), "inline": True},
				{"name": "Dealer's value:", "value": self.value(self.dealer_hand[0]), "inline": True},
				{"name": "My hand:", "value": self.readable(self.player_hand), "inline": True},
				{"name": "My value:", "value": self.total(self.player_hand), "inline": True}
			],
			"footer": {"text": "Directions: 🔴: Stand | 🟢: Hit"}
		}
		if self.total(self.dealer_hand) == 21:
			await self.payout(self.dealer_hand, self.player_hand)
		
		self.msg: discord.Message = await ctx.send(embed=discord.Embed.from_dict(self.embed_dict))
		await self.msg.add_reaction("🔴")
		await self.msg.add_reaction("🟢")
		
		while self.playing:
			def check(reaction: discord.Reaction, user: discord.Member): return user == self.ctx.author and (str(reaction.emoji) == "🔴" or str(reaction.emoji) == "🟢")
			reaction, user = await self.ext.bot.wait_for("reaction_add", check=check)
			
			if str(reaction.emoji) == "🟢":
				self.hit(self.player_hand)
				if self.total(self.player_hand) > 21: await self.payout(self.dealer_hand, self.player_hand)
			elif str(reaction.emoji) == "🔴":
				while self.total(self.dealer_hand) < 17:
					self.hit(self.dealer_hand)
				await self.payout(self.dealer_hand, self.player_hand)
			await self.update_embed()
		await self.update_embed()
	
	
	def deal(self) -> list:
		hand = []
		for i in range(2):
			random.shuffle(self.deck)
			card = self.deck.pop()
			hand.append(card)
		return hand
	
	
	@staticmethod
	def total(hand: list) -> int:
		total = 0
		for card in hand:
			if card in [11,12,13]:
				total += 10
			elif card == 1:
				if total >= 11: total += 1
				else: total += 11
			else: total += card
		return total
	
	
	@staticmethod
	def value(card: int) -> int:
		if card in [11,12,13]:
			return 10
		elif card == 1:
			return 11
		else: return card
	
	
	def hit(self, hand: list) -> list:
		card = self.deck.pop()
		hand.append(card)
		return hand
	
	
	@staticmethod
	def readable(hand: list) -> str:
		handStr = ""
		for i, card in enumerate(hand):
			if 	 card == 11:handStr = handStr + "J "
			elif card == 12:handStr = handStr + "Q "
			elif card == 13:handStr = handStr + "K "
			elif card == 1:	handStr = handStr + "A "
			else: handStr = handStr + str(card) + " "
		return handStr
	
	
	@staticmethod
	def readable_card(card: int) -> str:
		if card == 11: return "J"
		if card == 12: return "Q"
		if card == 13: return "K"
		if card == 1: return "A"
		else: return str(card)
	
	
	async def update_embed(self, done: bool = False) -> dict:
		self.embed_dict = {
			"title":"Ongoing 21 Game",
			"type": "rich",
			"timestamp": datetime.datetime.now().isoformat(),
			"color": 0xffdd00,
			"fields": [
				{"name": "Bet:", "value": str(self.bet), "inline": True},
				{"name": "Dealer showing:", "value": self.readable_card(self.dealer_hand[0]), "inline": True},
				{"name": "Dealer's value:", "value": self.value(self.dealer_hand[0]), "inline": True},
				{"name": "My hand:", "value": self.readable(self.player_hand), "inline": True},
				{"name": "My value:", "value": self.total(self.player_hand), "inline": True}
			],
			"footer": {"text": "Directions: 🔴: Stand | 🟢: Hit"}
		}
		if done:
			self.embed_dict["title"] = "Loading results..."
			self.embed_dict["fields"] = [
				{"name": "Bet:", "value": str(self.bet), "inline": True},
				{"name": "Dealer's hand:", "value": self.readable(self.dealer_hand), "inline": True},
				{"name": "Dealer's value:", "value": self.total(self.dealer_hand), "inline": True},
				{"name": "My hand:", "value": self.readable(self.player_hand), "inline": True},
				{"name": "My value:", "value": self.total(self.player_hand), "inline": True}
			]
		await self.msg.edit(embed=discord.Embed.from_dict(self.embed_dict))
		return self.embed_dict
	
	
	async def payout(self, dealer_hand, player_hand) -> dict:
		multiplier = 1
		self.playing = False
		await self.update_embed(True)
		
		if self.total(self.player_hand) > self.total(self.dealer_hand): ## if won
			_cfg = self.ext.config.data["games"]["blackjack"]
			multiplier = _cfg["win_multiplier"]
			if self.total(self.player_hand) == 21: multiplier = _cfg["bj_multiplier"]
			self.ext.econ.set_balance_from_d_id(self.ext.econ.get_bal_from_d_id(self.ctx.author.id) + (self.bet*multiplier), self.ctx.author.id)
			self.embed_dict["color"] = 0x00ff00
			self.embed_dict["title"] = f"You won ${self.bet*multiplier}!"
		elif self.total(self.dealer_hand) > self.total(self.player_hand): ## if lost
			self.embed_dict["color"] = 0xff0000
			self.embed_dict["title"] = f"You lost ${self.bet}!"
		elif self.total(self.player_hand) == self.total(self.dealer_hand): ## if push
			self.embed_dict["title"] = "Push!"
			self.embed_dict["color"] = 0xffdd00
			self.ext.econ.set_balance_from_d_id(self.ext.econ.get_bal_from_d_id(self.ctx.author.id) + self.bet, self.ctx.author.id)
		return self.embed_dict
