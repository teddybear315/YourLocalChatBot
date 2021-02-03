import discord, discord.errors
import json
import os

from sys import argv
from asyncio import sleep
from discord.ext.commands import Bot

## importing local modules
import ext
from modules.utilities import ylcb_config,secrets
from modules.utilities import utilities as u

## important variables
__version__	= ylcb_config.data["meta"]["version"]
__build__	= ylcb_config.data["meta"]["build_number"]
__authors__	= ["D Dot#5610", "_Potato_#6072"]

if __debug__:
	prefix = ylcb_config.data["bot"]["dev_prefix"]
else:
	prefix = ylcb_config.data["bot"]["prefix"]


bot = Bot(	
	command_prefix	= prefix,
	case_insensitive= True,
	description		= ylcb_config.data["bot"]["description"],
	owner_ids		= ylcb_config.data["devs"],
	activity		= discord.Activity(
	type			= discord.ActivityType.watching, name="some peoples streams.")
)

guild: discord.Guild

# roles
memberRole	: discord.Role
streamerRole: discord.Role

# channels
welcomeChannel	  	: discord.TextChannel
changelogChannel	: discord.TextChannel
suggestionChannel   : discord.TextChannel
announcementChannel	: discord.TextChannel


@bot.event
async def on_ready():
	u.log("Bot ready...")
	u.log(f"Running version: {__version__}b{__build__}")
	
	global guild
	global secrets
	global memberRole
	global streamerRole
	global welcomeChannel
	global changelogChannel
	global suggestionChannel
	global announcementChannel
	
	## server
	guild = bot.get_guild(ylcb_config.data["discord"]["guild_id"])
	
	## roles
	memberRole 	= guild.get_role(ylcb_config.data["discord"]["member_role_id"])
	streamerRole= guild.get_role(ylcb_config.data["discord"]["streamer_role_id"])
	
	## channels
	welcomeChannel 		= bot.get_channel(ylcb_config.data["discord"]["welcome_channel_id"])
	changelogChannel	= bot.get_channel(ylcb_config.data["discord"]["changelog_channel_id"])
	suggestionChannel	= bot.get_channel(ylcb_config.data["discord"]["suggestion_channel_id"])
	announcementChannel	= bot.get_channel(ylcb_config.data["discord"]["announcement_channel_id"])
	
	## changelog message update
	nt = "\n\t- "
	embed = discord.Embed(title=f"Local Chat Bot v{__version__}", color=0xff6000)
	embed.set_author(name=f"Your Local Chat Bot", icon_url=bot.user.avatar_url)
	embed.add_field(name="Changelog", value=f"\t- {nt.join(ylcb_config.data['meta']['changelog'])}")
	embed.set_footer(text=f"Build #{__build__}")
	del nt
	
	## if update detected and not debugging
	if __version__ != secrets.data["CACHED_VERSION"] and not __debug__:
		secrets.data["CACHED_VERSION"] = __version__
		secrets.data["CACHED_BUILD"] = __build__
		## send new message and update stored message id
		msg = await changelogChannel.send(embed=embed)
		secrets.data["CHANGELOG_MESSAGE_ID"] = msg.id
		## updates ylcb_config
		secrets = u.reloadylcb_config(secrets, "secrets.json")
	## if new build detected and not debugging 
	elif __build__ != secrets.data["CACHED_BUILD"] and not __debug__:
		msg = await changelogChannel.fetch_message(secrets.data["CHANGELOG_MESSAGE_ID"])
		if msg.author != bot.user:
			u.log(f"Changelog message was sent by another user. Changelog message updating won't work until CHANGELOG_MESSAGE_ID in config/secrets.json is updated", u.WRN)
		else:
			await msg.edit(embed=embed)
	
	##ANCHOR for every extension you want to load, load it
	for extension in ext.extensions.data["load"]:
		bot.load_extension(f"ext.{extension}")
		u.log(f"Loading {extension}...")
		loaded = True
		for requirement in bot.get_cog(extension).requirements:
			if not bot._BotBase__extensions.__contains__(f"ext.{requirement}"):
				try: bot.load_extension(f"ext.{requirement}")
				except Exception as e: 
					u.log(f"Could not load requirement {requirement} for {extension}, removing extension {extension}",u.ERR)
					u.log(e,u.ERR)
					bot.remove_cog(f"ext.{extension}")
					loaded = False
				else: u.log(f"Loaded requirement {requirement}")
			else: u.log(f"Requirement {requirement} met")
		if loaded: u.log(f"Loaded {extension}")
	
	u.log("YLCB logged in")


@bot.event
async def on_member_join(user: discord.Member):
	await welcomeChannel.send(f"Welcome to {guild.name}, {user.mention}")
	await user.add_roles(memberRole)


@bot.event
async def on_member_remove(user: discord.Member):
	await welcomeChannel.send(f"We will miss you, {user.name}")


@bot.event
async def on_message(message: discord.Message):
	global suggestionChannel
	
	if message.channel == suggestionChannel:
		embed = discord.Embed(title="New Feature Request!", color=0x8000ff)
		embed.set_author(name=f"{message.author.name}#{message.author.discriminator}", icon_url=message.author.avatar_url)
		embed.add_field(name="Request", value=message.content, inline=True)
		if message.author.id not in ylcb_config.data["devs"]:
			await message.author.send("Your request has been sent to the developers. They will respond as soon as possible. The embed below is what they have recieved.", embed=embed)
		u.log(f"Request from {message.author.name}#{message.author.discriminator} recieved")
		
		for dev in ylcb_config.data["devs"]:
			developer: discord.User = await bot.fetch_user(dev)
			if developer: await developer.send(embed=embed)
			else: u.log(f"Developer with ID {dev} does not exist!", u.ERR)
	await bot.process_commands(message)


## basic commands

@bot.command()
async def version(ctx):
	u.log(ctx)
	await ctx.send(f"I'm running version {__version__} build #{__build__}")


## dev level commands

@bot.command()
async def dev(self, ctx, _user: discord.Member = None):
	"""Add a developer to the team"""
	#global ylcb_config
	u.log(ctx)
	if not u.dev(ctx.author):
		await ctx.send(f"{ctx.author.mention}, only developers can use this command.")
		return
	if not _user:
		await ctx.send(f"{ctx.author.mention}, please tag a user to make them a developer.")
		return
	
	if _user.id in ylcb_config.data["devs"]:
		await ctx.send(f"{ctx.author.mention}, that user is already a developer.")
		return
	
	
	ylcb_config.data["devs"].append(_user.id)
	ylcb_config.updateFile()
	await ctx.send(f"{_user.mention}, {ctx.author.mention} has made you a developer!")


@bot.command()
async def stop(ctx):
	"""Safely  the bot"""
	if not u.dev(ctx.author):
		await ctx.send(f"{ctx.author.mention}, only developers can use this command.")
		return
	
	u.log("Developer initiated logout...", u.FLG)
	await ctx.send(f"Goodbye.")
	await bot.close()
	u.log("Successfully logged out and closed. Exiting...", u.FLG)
	exit(1)

u.log("Starting script...")
if __debug__:
	u.log("Debug mode on", u.FLG)
	bot.run(secrets.data["dev_token"])
else:
	bot.run(secrets.data["token"])