import datetime
import json
import os
from asyncio import sleep
from sys import argv
from typing import Optional

import discord
from discord.ext import commands

import modules.extension as ext
from modules.utilities import Config, debugging
from modules.utilities import logger as l
from modules.utilities import prefix, secrets
from modules.utilities import utilities as u
from modules.utilities import ylcb_config

## important variables
__version__	= ylcb_config.data["meta"]["version"]
build_num	= ylcb_config.data["meta"]["build_number"]

bot = commands.Bot(
	command_prefix	= prefix,
	case_insensitive= True,
	description		= ylcb_config.data["bot"]["description"],
	owner_ids		= ylcb_config.data["devs"],
	activity		= discord.Activity(type=discord.ActivityType.watching, name="some peoples streams.")
)

extensions = Config("./config/extensions.json")

l.log("Removing help command...", channel=l.DISCORD)
bot.remove_command("help")
l.log("Removed help command", channel=l.DISCORD)

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
	l.log("Discord bot ready...", channel=l.DISCORD)
	l.log(f"Running version: {__version__}b{build_num}", channel=l.DISCORD)
	
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
	embed.set_footer(text=f"Build #{build_num}")
	del nt
	
	## if update detected and not debugging
	if __version__ != secrets.data["CACHED_VERSION"] and not debugging:
		secrets.data["CACHED_VERSION"] = __version__
		secrets.data["CACHED_BUILD"] = build_num
		## send new message and update stored message id
		msg = await changelogChannel.send(embed=embed)
		secrets.data["CHANGELOG_MESSAGE_ID"] = msg.id
		## updates secrets
		secrets.updateFile()
	## if new build detected and not debugging
	elif build_num != secrets.data["CACHED_BUILD"] and not debugging:
		secrets.data["CACHED_BUILD"] = build_num
		msg = await changelogChannel.fetch_message(secrets.data["CHANGELOG_MESSAGE_ID"])
		if msg.author != bot.user:
			l.log(f"Changelog message was sent by another user. Changelog message updating won't work until CHANGELOG_MESSAGE_ID in config/secrets.json is updated", l.WRN, l.DISCORD)
		else:
			await msg.edit(embed=embed)
		## updates secrets
		secrets.updateFile()
	
	## for every extension you want to load, load it
	for extension in extensions.data["load"]:
		l.log(f"Loading {extension}...", channel=l.DISCORD)
		loadable = True
		try: ## Try catch allows you to skip setting up a requirements value if no requirement is needed
			for requirement in Config(f"./src/ext/config/{extension}.json").data["requirements"]:
				if not bot._BotBase__extensions.__contains__(f"ext.{requirement}") and requirement != "":
					try: bot.load_extension(f"ext.{requirement}")
					except Exception as e:
						l.log(f"\tCould not load requirement {requirement}", l.ERR, l.DISCORD)
						l.log(f"\t{e}",l.ERR,l.DISCORD)
						bot.remove_cog(extension)
						loadable = False
					else: l.log(f"\tLoaded requirement {requirement}", channel=l.DISCORD)
				else: l.log(f"\tRequirement {requirement} met", channel=l.DISCORD)
		except KeyError: pass
		if loadable:
			try: bot.load_extension(f"ext.{extension}")
			except commands.ExtensionAlreadyLoaded: l.log(f"Already loaded ext.{extension}")
			else: l.log(f"Loaded {extension}", channel=l.DISCORD)


@bot.event
async def on_member_join(user: discord.Member):
	await welcomeChannel.send(f"Welcome to {guild.name}, {user.mention}")
	await user.add_roles(memberRole)


@bot.event
async def on_member_remove(user: discord.Member):
	await welcomeChannel.send(f"We will miss you, {u.discordify(user.display_name)}")


@bot.event
async def on_message(message: discord.Message):
	if message.channel == suggestionChannel:
		embed_dict = {
			"title": "Feature Request",
			"timestamp": datetime.datetime.now().isoformat(),
			"type": "rich",
			"color": 0x8000ff,
			"author": {
				"name": f"{u.discordify(message.author.name)}#{message.author.discriminator}",
				"icon_url": message.author.avatar_url
			},
			"fields": [
				{"name": "Request", "value": message.content} 
			]
		}
		embed = discord.Embed(embed=discord.Embed.from_dict(embed_dict))
		if message.author.id not in ylcb_config.data["devs"]:
			await message.author.send("Your request has been sent to the developers. They will respond as soon as possible. The embed below is what they have recieved.", embed=embed)
		l.log(f"Request from {u.discordify(message.author.name)}#{message.author.discriminator} recieved", channel=l.DISCORD)
		
		for dev in ylcb_config.data["devs"]:
			developer: discord.User = await bot.fetch_user(dev)
			if developer: await developer.send(embed=embed)
			else: l.log(f"Developer with ID {dev} does not exist!", l.ERR, l.DISCORD)
	await bot.process_commands(message)


async def before_invoke(ctx):
	l.log(ctx, channel=l.DISCORD)
bot.before_invoke(before_invoke)


## basic commands


@bot.command(name="version", usage=f"{prefix}version", brief="Tells you what version I'm running")
async def version(ctx):
	"""
	Tells you what version I'm running
	"""
	await ctx.send(f"I'm running version {__version__} build #{build_num}")


@bot.command(name="help", usage=f"{prefix}help [command:str]", brief="This command")
async def help_command(ctx, command: str = None):
	"""
	This command

	Args:
		command (`str`, optional): Command or extension name. Defaults to `None`.
	"""
	fields = []
	if not command:
		for cog in bot.cogs:
			cog: ext.Extension = bot.get_cog(cog)
			fields.append({"name": cog.name, "value": cog.description, "inline": True})
	else:
		if bot._BotBase__extensions.__contains__(f"ext.{command}"):
			cog: commands.Cog = bot.get_cog(command)
			for cmd in cog.get_commands():
				cmd: commands.Command
				if not cmd.hidden: fields.append({"name": cmd.name, "value": cmd.brief, "inline": True})
		elif bot.get_command(command):
			cmd = bot.get_command(command)
			fields.append({"name": cmd.name, "value": cmd.help, "inline": True})
			fields.append({"name": "Usage", "value": f"`{cmd.usage}`", "inline": True})
			if cmd.aliases: fields.append({"name": "Aliases", "value": ", ".join(cmd.aliases), "inline": True})
	
	embed_dict = {
		"title": "Help",
		"description": "`<...>` is a required parameter.\n`[...]` is an optional parameter.\n`:` specifies a type",
		"color": 0x15F3FF,
		"fields": fields,
		"timestamp": datetime.datetime.now().isoformat()
	}
	l.log(embed_dict)
	await ctx.send(embed=discord.Embed.from_dict(embed_dict))


## dev level commands
@bot.command(name="reload", hidden=True)
@u.is_dev()
async def reload_ext(ctx, ext: str):
	"""Reloads an extension"""
	if ext == "all":
		for cog in bot._BotBase__extensions:
			bot.reload_extension(cog)
		await ctx.send(f"{ctx.author.mention}, all extensions reloaded")
		return
	bot.reload_extension("ext."+ext)
	await ctx.send(f"{ctx.author.mention}, ext.{ext} reloaded")
@reload_ext.error
async def reload_ext_error(ctx, error):
	if isinstance(error, commands.CheckFailure):
		await ctx.send(f"{ctx.author.mention}, this command can only be used by developers")
	if isinstance(error, commands.ExtensionNotFound) or isinstance(error, commands.ExtensionNotLoaded):
		await ctx.send(f"{ctx.author.mention}, this extension does not exist")


@bot.command(name="list", hidden=True)
@u.is_dev()
async def list(ctx):
	await ctx.send(", ".join(bot.cogs))


@bot.command(name="dev", hidden=True)
@u.is_dev()
async def dev(ctx, _user: discord.Member = None):
	"""Add a developer to the team"""
	if not _user:
		await ctx.send(f"{ctx.author.mention}, please tag a user to make them a developer.")
		return
	
	if _user.id in ylcb_config.data["devs"]:
		await ctx.send(f"{ctx.author.mention}, that user is already a developer.")
		return
	
	ylcb_config.data["devs"].append(_user.id)
	ylcb_config.updateFile()
	await ctx.send(f"{_user.mention}, {ctx.author.mention} has made you a developer!")
@dev.error
async def dev_error(ctx, error):
	if isinstance(error, commands.CheckFailure):
		await ctx.send(f"{ctx.author.mention}, this command can only be used by developers")


@bot.command(name="stop", hidden=True)
@u.is_dev()
async def stop(ctx):
	"""Safely stop the bot"""
	db = bot.get_cog("database").db
	if db: db.close()
	await ctx.send(f"Goodbye.")
	await bot.close()
	l.log("Successfully logged out and closed. Exiting...", l.FLG, l.DISCORD)
	exit(1)


l.log("Starting script...")
if debugging:
	l.log("Debug mode on", l.FLG)
	bot.run(secrets.data["dev_token"])
else:
	bot.run(secrets.data["token"])
