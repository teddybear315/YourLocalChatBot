from datetime import datetime
from datetime import timezone

import discord
from discord.ext import commands
from modules.extension import Extension
from modules.utilities import logger as l
from modules.utilities import prefix
from modules.utilities import utilities as u
from modules.utilities import ylcb_config


class admin(Extension):
	"""Admin Extension - ylcb-devs"""
	def __init__(self, bot: commands.Bot):
		"""
		admin(bot)
		
		Args:
			bot (`commands.Bot`): `commands.Bot` Instance
		"""
		super().__init__(bot, "admin")
		self.discord_time_format = "%Y-%m-%d %H:%M:%S.%f"
	
	
	@commands.command(name="info", usage=f"{prefix}info [user:user]", brief="Get server or user info")
	async def info(self, ctx, user: discord.Member = None):
		"""
		Get server or user info
		
		Args:
			user (`discord.Member`, optional): If defined gets user info instead of server info. Defaults to `None`.
		"""
		server_mode = True if not user else False
		
		if server_mode:
			perma_link = ""
			for invite in await ctx.guild.invites():
				invite: discord.Invite
				if not invite.revoked and invite.max_age == 0 and not invite.temporary and invite.max_uses == 0:
					perma_link = str(invite)
					break
			owner = await self.bot.fetch_user(ctx.guild.owner_id)
			created = datetime.strptime(str(ctx.guild.created_at), self.discord_time_format)
			embed_dict: dict = {
				"type": "rich",
				"timestamp": datetime.now().isoformat(),
				"color": 0x6495ed,
				"fields": [
					{"name": "Owner", "value": f"{u.discordify(owner.name)}#{owner.discriminator}", "inline": True},
					{"name": "Server Created", "value": created.strftime("%m/%d/%Y %H:%M"), "inline": True},
					{"name": "Members", "value": str(ctx.guild.member_count), "inline": True},
					{"name": "Region", "value": str(ctx.guild.region), "inline": True},
					{"name": "Boosters", "value": str(ctx.guild.premium_subscription_count), "inline": True}
				],
				"author": {
					"name": u.discordify(ctx.guild.name),
					"icon_url": str(ctx.guild.icon_url)
				},
				"footer": {"text": f"ID: {ctx.guild.id}"}
			}
			if ctx.guild.description:
				embed_dict["description"] = ctx.guild.description
			if perma_link:
				embed_dict["fields"].append({"name": "Perma Link", "value": perma_link, "inline": True})
			await ctx.send(embed=discord.Embed.from_dict(embed_dict))
		else:
			embed_dict: dict = {
				"title": f"{u.discordify(user.name)}#{user.discriminator}",
				"type": "rich",
				"color": user.color.value,
				"timestamp": datetime.now().isoformat(),
				"fields": [
					{"name": "Account Created", "value": datetime.strptime(str(user.created_at), self.discord_time_format).strftime("%m/%d/%Y %H:%M"), "inline": True},
					{"name": "Status", "value": user.status[0], "inline": True}
				],
				"author": {
					"name": u.discordify(user.display_name),
					"icon_url": str(user.avatar_url)
				},
				"footer": {"text": f"ID: {user.id}"}
			}
			if user.activity:
				if type(user.activity) == discord.Spotify:
					embed_dict["fields"].append({"name": "Activity", "value": "Spotify", "inline": True})
					embed_dict["fields"].append({"name": "Song", "value": f"{user.activity.title} - {', '.join(user.activity.artists)} - {user.activity.album}", "inline": True})
				else:
					embed_dict["fields"].append({"name": "Activity", "value": user.activity.name, "inline": True})
			if user.premium_since:
				embed_dict["fields"].append({"name": "Nitro Since", "value": datetime.strptime(str(user.premium_since), self.discord_time_format).strftime("%m/%d/%Y %H:%M"), "inline": True})
			
			await ctx.send(embed=discord.Embed.from_dict(embed_dict))
	
	
	@commands.command(name="ban", usage=f"{prefix}ban <user:user> [reason:str]")
	@u.is_admin()
	async def ban(self, ctx, user: discord.Member, reason: str = None):
		"""
		ban command

		Args:
			user (`discord.Member`): User to ban
			reason (`str`, optional): Reason for ban. Defaults to `None`.
		"""


def setup(bot):
	bot.add_cog(admin(bot))
