import discord

from sys import argv
from asyncio import sleep
from discord.ext.commands import Bot

## importing extensions
import ext

## importing local modules
from modules import utils as u
from modules.twitch_integration import Twitch
from modules import db, config, secrets

## important variables
__version__ = config["meta"]["version"]
__build__ = config["meta"]["build_number"]
__authors__ = ["D Dot#5610", "_Potato_#6072"]

if __debug__:
	prefix = config["bot"]["dev_prefix"]
else:
	prefix = config["bot"]["prefix"]

bot = Bot(	
	command_prefix	= prefix,
	case_insensitive= True,
	description		= config["bot"]["description"],
	owner_ids		= config["devs"],
	activity		= discord.Activity(
	type			= discord.ActivityType.watching, name="some peoples streams.")
)

t = Twitch(config, secrets, db, bot)
guild: discord.Guild

# roles
vipRole		: discord.Role
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
	global vipRole
	global memberRole
	global streamerRole
	global welcomeChannel
	global changelogChannel
	global suggestionChannel
	global announcementChannel

	guild = bot.get_guild(config["discord"]["guild_id"])

	## roles
	vipRole 	= guild.get_role(config["discord"]["vip_role_id"])
	memberRole 	= guild.get_role(config["discord"]["member_role_id"])
	streamerRole= guild.get_role(config["discord"]["streamer_role_id"])

	## channels
	welcomeChannel 		= bot.get_channel(config["discord"]["welcome_channel_id"])
	changelogChannel	= bot.get_channel(config["discord"]["changelog_channel_id"])
	suggestionChannel	= bot.get_channel(config["discord"]["suggestion_channel_id"])
	announcementChannel	= bot.get_channel(config["discord"]["announcement_channel_id"])

	## changelog message update
	nt = "\n\t- "
	embed = discord.Embed(title=f"Local Chat Bot v{__version__}", color=0xff6000)
	embed.set_author(name=f"Your Local Chat Bot", icon_url=bot.user.avatar_url)
	embed.add_field(name="Changelog", value=f"\t- {nt.join(config['meta']['changelog'])}")
	embed.set_footer(text=f"Build #{__build__}")
	del nt

	## if update detected and not debugging
	if __version__ != secrets["CACHED_VERSION"] and not __debug__:
		secrets["CACHED_VERSION"] = __version__
		secrets["CACHED_BUILD"] = __build__

		msg = await changelogChannel.send(embed=embed)
		secrets["CHANGELOG_MESSAGE_ID"] = msg.id
		
		u.editConfig("secrets.json", secrets)
		secrets = u.reloadConfig("secrets.json")

	## if new build detected and not debugging 
	elif __build__ != secrets["CACHED_BUILD"] and not __debug__:
		msg = await changelogChannel.fetch_message(secrets["CHANGELOG_MESSAGE_ID"])
		if msg.author != bot.user:
			u.log(f"Changelog message was sent by another user. Changelog message updating won't work until CHANGELOG_MESSAGE_ID in ./config/secrets.json is updated", u.WRN)
		else:
			await msg.edit(embed=embed)

	## for every extension you want to load, load it
	for extension in ext.desired_extensions:
		bot.load_extension(f"ext.{extension}")
		u.log(f"Loaded {extension}")
	
	u.log("YLCB logged in")


@bot.event
async def on_member_join(user: discord.Member):
	await welcomeChannel.send(f"Welcome to {guild.name}, {user.mention}")
	await user.add_roles(memberRole)
	# TODO make a database entry for new member


@bot.event
async def on_member_remove(user: discord.Member):
	await welcomeChannel.send(f"We will miss you, {user.name}")
	if db.find({"discord_id": str(user.id)}):
		db.delete_one({"discord_id": str(user.id)})


@bot.event
async def on_message(message: discord.Message):
	global suggestionChannel

	if message.channel == suggestionChannel:
		embed = discord.Embed(title="New Feature Request!", color=0x8000ff)
		embed.set_author(name=f"{message.author.name}#{message.author.discriminator}", icon_url=message.author.avatar_url)
		embed.add_field(name="Request", value=message.content, inline=True)
		if message.author.id not in config["devs"]:
			await message.author.send("Your request has been sent to the developers. They will respond as soon as possible. The embed below is what they have recieved.", embed=embed)
		u.log(f"Request from {message.author.name}#{message.author.discriminator} recieved")

		for dev in config["devs"]:
			developer: discord.User = await bot.fetch_user(dev)
			if developer: await developer.send(embed=embed)
			else: u.log(f"Developer with ID {dev} does not exist!", u.ERR)
	await bot.process_commands(message)


async def background_loop():
	await sleep(10) #!NOTE used to ensure everything initiates, if you find things saying they werent initiated when they were please increase the sleep time
	await bot.wait_until_ready()

	while not bot.is_closed():
		u.log("Checking twitch...")
		await t.check(announcementChannel)
		await sleep(60)


# dev level commands

@bot.command()
async def reload(ctx):
	u.log(ctx)

	if not u.dev(ctx.author):
		await ctx.send(f"{ctx.author.mention}, only developers can use this command.")
		return

	global config
	config = u.reloadConfig()
	await ctx.send(f"{ctx.author.mention}, reloaded config!")
	return


@bot.command()
async def stop(ctx):
	if not u.dev(ctx.author):
		await ctx.send(f"{ctx.author.mention}, only developers can use this command.")
		return

	u.log("Developer initiated logout...")
	await ctx.send(f"Goodbye.")
	await bot.logout()
	await bot.close()
	exit(1)

u.log("Starting script...")
bot.loop.create_task(background_loop())
if __debug__:
	bot.run(secrets["dev_token"])
else:
	bot.run(secrets["token"])
