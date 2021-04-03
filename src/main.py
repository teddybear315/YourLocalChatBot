import datetime
import json
import os
from asyncio import sleep
from sys import argv
from typing import Optional

import discord
from discord.ext import commands

from modules.utilities import Config, debugging
from modules.utilities import logger as l
from modules.utilities import prefix, secrets
from modules.utilities import utilities as u
from modules.utilities import ylcb_config

## important variables


bot = commands.Bot(
	command_prefix	= prefix,
	case_insensitive= True,
	description		= ylcb_config.data["bot"]["description"],
	owner_ids		= ylcb_config.data["devs"],
	activity		= discord.Activity(type=discord.ActivityType.watching, name="some peoples streams.")
)


bot.load_extension("modules.bot")


async def on_command_error(ctx, error):
	l.log(str(error), l.ERR, l.DISCORD)
	embed = discord.Embed(title="Error!", color=0xff0000, description=f"There was an error proccessing your command!\nReason: {str(error)}")
	embed.timestamp(datetime.datetime)
	await ctx.send(embed=embed)
	return super().cog_command_error(ctx, error)


@bot.command(name="reload", hidden=True)
@u.is_dev()
async def reload_ext(ctx, ext: str):
	"""Reloads an extension"""
	if ext == "all":
		for extension in bot.extensions:
			bot.reload_extension(extension)
		await ctx.send(f"{ctx.author.mention}, all extensions reloaded")
	elif ext == "bot":
		bot.reload_extension("modules.bot")
		await ctx.send(f"{ctx.author.mention}, bot reloaded")
	else:
		bot.reload_extension("ext."+ext)
		await ctx.send(f"{ctx.author.mention}, ext.{ext} reloaded")
@reload_ext.error
async def reload_ext_error(ctx, error):
	if isinstance(error, commands.CheckFailure):
		await ctx.send(f"{ctx.author.mention}, this command can only be used by developers")
	if isinstance(error, commands.ExtensionNotFound) or isinstance(error, commands.ExtensionNotLoaded):
		await ctx.send(f"{ctx.author.mention}, this extension does not exist")


l.log("Starting script...")
if debugging:
	l.log("Debug mode on", l.WRN)
	bot.run(secrets.data["dev_token"])
else:
	bot.run(secrets.data["token"])
