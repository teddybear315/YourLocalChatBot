import time
import discord
import requests
import discord.ext.commands

from modules import utils as u
from pymongo.collection import Collection

class Twitch:
	"""Twitch integration stuff"""

	config	: dict
	secrets	: dict
	twitch	: Collection
	bot		: discord.Client

	def __init__(self, config: dict, secrets: dict, twitch: Collection, bot: discord.ext.commands.Bot):
		"""Twitch(config, secrets, twitch)"""
		self.config = config
		self.secrets = secrets
		self.twitch = twitch
		self.bot = bot

	async def check(self, streamerChannel: discord.TextChannel):
		return #!NOTE TEMPORARY LINE DONT FORGET TO REMOVE FOR PRODUCTION
		for streamer in self.twitch.find():
			username = streamer["twitch_username"]
			headers = {
				"User-Agent": "Your user agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36 OPR/63.0.3368.51 (Edition beta)",
				"Client-ID": self.secrets["twitch_token"]
			}

			u.log(f"\tChecking if {username} is live...")
			try:
				r = requests.get(f"https://api.twitch.tv/helix/streams?user_login={username}", headers=headers)
				streamData = r.json()
				r.close()
			except requests.ConnectionError as e:
				u.log("You\'re not connected to the Internet:tm:... Aborting", u.ERR)
				self.twitch.update_one({"twitch_username": username}, {"$set": streamer})
				return

			if streamData["data"]:
				try:
					try: streamData = r.json()["data"][0]
					except:
						streamData = r.json()["data"]
						continue
					r = requests.get(f"https://api.twitch.tv/helix/users?id={streamData['user_id']}", headers=headers)
					try: userData = r.json()["data"][0]
					except:
						userData = r.json()["data"]
						continue
					r.close()

					r = requests.get(f"https://api.twitch.tv/helix/games?id={streamData['game_id']}", headers=headers)
					try: gameData = r.json()["data"][0]
					except:
						gameData = r.json()["data"]
						continue
					r.close()

				except requests.ConnectionError as e:
					u.log("You\'re not connected to the Internet:tm:... Aborting", u.ERR)
					self.twitch.update_one({"twitch_username": username}, {"$set": streamer})
					return

				user: discord.User  = await self.bot.fetch_user(int(streamer["discord_id"]))
				embed: discord.Embed
				if (streamer["custom_url"]):
					embed = discord.Embed(title=streamData["title"], url=streamer["custom_url"], color=0x8000ff)
				else:
					embed = discord.Embed(title=streamData["title"], url=f"https://twitch.tv/{username}", color=0x8000ff)

				embed.set_author(name=user.name, icon_url=user.avatar_url)
				embed.set_thumbnail(url=gameData["box_art_url"].format(width=390, height=519))
				embed.set_image(url=streamData["thumbnail_url"].format(width=1280, height=720))
				embed.add_field(name="Game", value=gameData["name"], inline=True)
				embed.add_field(name="Viewers", value=streamData["viewer_count"], inline=True)

				if not streamer["message_id"]:
					u.log(f"\t\t{username} is now live, announcing stream...")
					msg = await streamerChannel.send(f"@everyone {user.mention} is live!", embed=embed)
					streamer["message_id"] = msg.id
				elif streamer["response"] != streamData:
					msg = await streamerChannel.fetch_message(streamer["message_id"])
					u.log(f"\t\tUpdating {username}\'s live message...")
					if msg.author != self.bot.user:
						u.log(f"\t\tCan\'t update {username}\'s live message... Not my message.")
						return
					await msg.edit(content=f"@everyone {user.mention} is live!", embed=embed)
				streamer["response"] = streamData

			else:
				if streamer["message_id"]:
					u.log(f"\t\t{username} is no longer live, deleting message...")
					msg = await streamerChannel.fetch_message(streamer["message_id"])
					await msg.delete()
					streamer["response"] = {}
					streamer["message_id"] = None

			self.twitch.update_one({"twitch_username": username}, {"$set": streamer})
