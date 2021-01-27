import discord

from discord.ext import commands

from modules import utils as u


class Utilities(commands.Cog):
	def __init__(self, bot):
		self.bot: commands.Bot	  = bot
		self.guild: discord.Guild   = self.bot.get_guild(u.config["discord"]["guild_id"])
		self.vipRole: discord.Role  = self.guild.get_role(u.config["discord"]["vip_role_id"])

	@commands.command(name="vip")
	async def _vip(self, ctx, _user: discord.Member = None):
		u.log(ctx)
		if not u.vip(ctx.author):
			await ctx.send(f"{ctx.author.mention}, only VIPs can use this command.")
			return
		if not _user:
			await ctx.send(f"{ctx.author.mention}, please tag a user to make them a VIP.")
			return
		if u.vip(_user):
			await ctx.send(f"{ctx.author.mention}, that user is already a VIP.")
			return

		await _user.add_roles(self.vipRole)
		await ctx.send(f"{_user.mention}, {ctx.author.mention} has made you a VIP!")

	@commands.command(name="dev")
	async def dev(self, ctx, _user: discord.Member = None):
		u.log(ctx)
		if not u.dev(ctx.author):
			await ctx.send(f"{ctx.author.mention}, only developers can use this command.")
			return
		if not _user:
			await ctx.send(f"{ctx.author.mention}, please tag a user to make them a developer.")
			return

		if _user.id in u.config["devs"]:
			await ctx.send(f"{ctx.author.mention}, that user is already a developer.")
			return

		u.config["devs"].append(_user.id)
		u.editConfig()
		config = u.reloadConfig()
		await ctx.send(f"{_user.mention}, {ctx.author.mention} has made you a developer!")

def setup(bot):
	bot.add_cog(Utilities(bot))