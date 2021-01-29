import discord
import requests
import modules.utilities as utils

from discord.ext.commands	import Context
from discord.ext			import commands, tasks
from modules				import db, u
from ext					import Extension

class Twitch(Extension):
	"""Twitch Extension - ylcb-devs"""
	def __init__(self, bot: commands.Bot):
		"""Twitch(bot)"""
		super().__init__(
			bot,
			config=	utils.Config(f"exts/twitch.json")
		)
	
	
	def cog_unload(self):
		self.printer.cancel()
	
	
	""" TODO 
		generalize database entry code
		with the entry of extensions and the attempt to let anyone make extensions the database is no longer just for streamers
	"""
	@commands.command(name="streamer")
	async def streamer(self, ctx, _user: discord.Member = None, _username: str = None):
		"""Adds twitch username to the database"""
		u.log(ctx)
		if not u.admin(ctx.author):
			await ctx.send(f"{ctx.author.mention}, only admins can use this command.")
			return
		if not _user:
			await ctx.send(f"{ctx.author.mention}, please tag a user to make them a streamer.")
			return
		if not _username:
			await ctx.send(f"{ctx.author.mention}, please specify the user\'s Twitch username.")
			return
		if u.streamer(_user) or db.find_one({"discord_id": str(_user.id)}):
			await ctx.send(f"{ctx.author.mention}, that user is already a streamer.")
			return
		
		await _user.add_roles(self.streamerRole)
		##ANCHOR layout of the database
		db.insert_one({
			"twitch_username": _username,	#str
			"message_id": None,				#int
			"discord_id": str(_user.id),	#int
			"response": {},					#json
			"custom_stream_url": None,		#str
			"balance": 0,					#int
		})
		await ctx.send(f"{_user.mention}, {ctx.author.mention} has made you a streamer!")
	
	
	@commands.command()
	async def raid(self, ctx: Context, twitchChannel: str = None):
		"""Gives specified use a shoutout"""
		u.log(ctx)
		if not u.admin(ctx.author):
			await ctx.send(f"{ctx.author.mention}, only admins can use this command.")
			return
		if not twitchChannel:
			await ctx.send(f"{ctx.author.mention}, please specify a channel name.")
			return
		
		await ctx.send(f"@everyone we're raiding https://twitch.tv/{twitchChannel}")
	
	
	@commands.command()
	async def link(self, ctx, url: str = None):
		"""Adds custom streaming link"""
		u.log(ctx)
		if not self.config.data["enable_custom_links"]: 
			await ctx.send(f"{ctx.author.mention}, this command has been disabled by a moderator")
			return
		if not url:
			write = True
		else:
			if not url.startswith("https://") or not url.startswith("http://"):
				url = "https://" + url
			write = False
		
		if write:
			current_user = db.find_one({"discord_id": ctx.author.id}) #ANCHOR db entry
			current_user["custom_url"] = url
			param = {"discord_id": str(ctx.author.id)}
			param2 = {"$set": current_user}
			db.update_one(param, param2)
			await ctx.send(f"{ctx.author.mention}, your custom link has been set!")
			return
		await ctx.send(f"{ctx.author.mention}, your custom link is {db.find_one({'discord_id': ctx.author.id})}")
	
	
	##ANCHOR check if streamer is live
	async def check(self, streamerChannel: discord.TextChannel):
		return #!NOTE TEMPORARY LINE DONT FORGET TO REMOVE FOR PRODUCTION
		
		for streamer in self.db.find(): #ANCHOR db entry
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
				self.db.update_one({"twitch_username": username}, {"$set": streamer}) #ANCHOR db entry
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
					self.db.update_one({"twitch_username": username}, {"$set": streamer}) #ANCHOR db entry
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
			
			self.db.update_one({"twitch_username": username}, {"$set": streamer}) #ANCHOR db entry
	
	
	@tasks.loop(seconds=60)
	async def printer(self):
		u.log("Checking twitch...")
		await self.check(self.bot.get_channel(utils.ylcb_config.data["discord"]["announcement_channel_id"]))
	
	
	@printer.before_loop
	async def before_printer(self):
		print('waiting...')
		await self.bot.wait_until_ready()


def setup(bot):
	bot.add_cog(Twitch(bot))
