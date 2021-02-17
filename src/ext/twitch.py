import discord, requests, sqlite3, requests, datetime
import modules.utilities as utils
from sys import argv

from discord.ext.commands	import Context
from discord.ext			import commands, tasks
from modules.utilities		import logger as l,secrets,ylcb_config, utilities as u, prefix
from ext					import *

class twitch(Extension):
	"""Twitch Integration Extension - ylcb-devs"""
	def __init__(self, bot: commands.Bot):
		"""Twitch(bot)"""
		super().__init__(bot, "ext.twitch")
		self.db = bot.get_cog("database").db
		self.checker.start()
	
	
	def cog_unload(self):
		self.checker.cancel()
	
	
	@commands.command(name="streamer", usage=f"{prefix}streamer <user:user> <twitch_username:str>")
	async def streamer(self, ctx: Context, user: discord.Member = None, twitch_username: str = None):
		"""Adds twitch username to a specified user in the database"""
		if not u.admin(ctx.author):
			await ctx.send(f"{ctx.author.mention}, only admins can use this command.")
			return
		if not user:
			await ctx.send(f"{ctx.author.mention}, please tag a user to make them a streamer.")
			return
		if not twitch_username:
			await ctx.send(f"{ctx.author.mention}, please specify the user\'s Twitch username.")
			return
		if u.streamer(user):
			await ctx.send(f"{ctx.author.mention}, that user is already a streamer.")
			return
		
		guild = await self.bot.fetch_guild(ylcb_config.data["discord"]["guild_id"])
		await user.add_roles(guild.get_role(ylcb_config.data["discord"]["streamer_role_id"]))
		self.db.execute("UPDATE Users SET twitch_username=:user WHERE discord_id=:d_id",{"user": twitch_username, "d_id": user.id})
		self.db.commit()
		await ctx.send(f"{user.mention}, {ctx.author.mention} has made you a streamer!")
	
	
	@commands.command(name="raid", usage=f"{prefix}raid <twitch_channel:str>")
	@u.is_admin()
	async def raid(self, ctx, twitch_channel: str = None):
		"""Gives specified user a shoutout"""
		if not twitch_channel:
			await ctx.send(f"{ctx.author.mention}, please specify a channel name.")
			return
		await ctx.send(f"@everyone we're raiding https://twitch.tv/{twitch_channel}")
	@raid.error
	async def raid_error(self, ctx, error):
		if isinstance(error, commands.CheckFailure):
			await ctx.send(f"{ctx.author.mention}, this command can only be used by admins")
	
	
	async def check(self, streamerChannel: discord.TextChannel) -> bool:
		"""Checks if a streamer is live and if so announces it"""
		for streamer in self.db.cursor().execute("SELECT * FROM Users").fetchall():
			if not streamer[0]:
				continue
			username = streamer[0]
			message_id = streamer[1]
			discord_id = streamer[2]
			response = streamer[3]
			
			l.log(f"\tChecking if {username} is live...")
			
			headers = {
				"User-Agent": "Your user agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36 OPR/63.0.3368.51 (Edition beta)",
				"Client-ID": secrets.data["twitch_client_id"],
				"Authorization": f"Bearer {secrets.data['twitch_secret']}"
				# "Authorization": f"Bearer 2gbdx6oar67tqtcmt49t3wpcgycthx"
			}
			
			r = requests.get(f"https://api.twitch.tv/helix/streams?user_login={username}", headers=headers)
			try: streamData = r.json()["data"]
			except KeyError:
				l.log(f"\t\tTwitch error: {r.json()['error']}: {r.json()['status']}", l.ERR)
				continue
			if type(streamData) == list and streamData:
				streamData = streamData[0]
			r.close()
			
			if streamData:
				r = requests.get(f"https://api.twitch.tv/helix/games?id={streamData['game_id']}", headers=headers)
				gameData = r.json()["data"]
				if type(gameData) == list and gameData:
					gameData = gameData[0]
				r.close()
				
				import time
				
				user: discord.User  = await self.bot.fetch_user(int(streamer[2]))
				embed_dict = {
					"title": streamData["title"],
					"url": f"https://twitch.tv/{username}",
					"type": "url",
					"timestamp": datetime.datetime.fromtimestamp(time.mktime(time.strptime(streamData["started_at"], "%Y-%m-%dT%H:%M:%SZ")), datetime.timezone.utc).isoformat(),
					"footer": {"text": "Started streaming at (UTC):"},
					"color": 0x8000ff,
					"fields": [
						{"name": "Game", "value": gameData["name"], "inline": True},
						{"name": "Viewers", "value": streamData["viewer_count"], "inline": True}
					],
					"author": {
						"name": user.display_name,
						"icon_url": str(user.avatar_url)
					},
					"thumbnail": {
						"url": gameData["box_art_url"].format(width=390, height=519),
						"width": 390,
						"height": 519
					},
					"image": {
						"url": streamData["thumbnail_url"].format(width=1280, height=720),
						"width": 1280,
						"height": 720
					}
				}
				embed = discord.Embed.from_dict(embed_dict)
				
				if not message_id:
					l.log(f"\t\t{username} is now live, announcing stream...")
					if "--debug" not in argv:	msg = await streamerChannel.send(f"@everyone {user.mention} is live!", embed=embed)
					else:						msg = await streamerChannel.send(f"{user.mention} is live!", embed=embed)
					self.db.execute("UPDATE Users SET message_id=:id WHERE twitch_username=:username", {"id":msg.id,"username":username})
					self.db.commit()
				elif response != streamData:
					msg = await streamerChannel.fetch_message(streamer[1])
					l.log(f"\t\tUpdating {username}\'s live message...")
					if "--debug" not in argv:	msg = await msg.edit(content=f"@everyone {user.mention} is live!", embed=embed)
					else:						msg = await msg.edit(content=f"{user.mention} is live!", embed=embed)
					self.db.execute("UPDATE Users SET response=:json WHERE twitch_username=:username", {"json":json.dumps(streamData),"username":username})
					self.db.commit()
			elif streamer[1]:
				l.log(f"\t\t{username} is no longer live, deleting message...")
				msg = await streamerChannel.fetch_message(streamer[1])
				await msg.delete()
				self.db.execute("UPDATE Users SET message_id=:id,response=:json WHERE twitch_username=:username", {"id":None,"json":"{}","username":username})
				self.db.commit()
		return True
	
	
	@tasks.loop(seconds=60)
	async def checker(self):
		l.log("Checking twitch...")
		if await self.check(self.bot.get_channel(utils.ylcb_config.data["discord"]["announcement_channel_id"])):
			l.log("Check Successful")
	
	
	@checker.before_loop
	async def before_checker(self):
		await self.bot.wait_until_ready()


def setup(bot):
	bot.add_cog(twitch(bot))
