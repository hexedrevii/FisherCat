import discord

from discord.ext import commands
from discord import app_commands

from fisher_bot import FisherBot

from datetime import datetime, timedelta


class UserActions(commands.Cog):
  def __init__(self, bot: FisherBot):
    self.bot = bot

  @app_commands.command(name='stats', description='Show off yout stats!')
  @app_commands.guild_only()
  async def stats(self, interaction: discord.Interaction):
    guild_id, member_id = self.bot.get_guildmember_ids(interaction)

    self.bot.db.ensure_guild(guild_id)

    user = self.bot.db.ensure_user(member_id, guild_id)

    daily_status = 'Ready!'

    if user.lastclaimed:
      now = datetime.now()

      next_claim = user.lastclaimed + timedelta(hours=24)

      if now < next_claim:
        remaining = next_claim - now

        total_seconds = int(remaining.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        daily_status = f'{hours}h {minutes}m {seconds}s'

    embed = discord.Embed(
      title=f'Stats for {interaction.user.name}!', colour=discord.Colour.dark_gold()
    )
    embed.add_field(
      name='XP',
      value=f'Level: {user.level}\nXP: {user.xp}\nXP Step: {user.xp_step}\nXP Next: {user.xp_next}',
      inline=False,
    )
    embed.add_field(
      name='Coins', value=f'Coins: {user.coins}\nDaily: {daily_status}', inline=False
    )

    embed.set_footer(
      text=f'Requested by {interaction.user.name}', icon_url=interaction.user.avatar
    )
    embed.timestamp = datetime.now()

    await interaction.response.send_message(embed=embed)

  @app_commands.command(name='daily', description='Claim your daily reward!')
  @app_commands.guild_only()
  async def daily(self, interaction: discord.Interaction):
    guild_id, member_id = self.bot.get_guildmember_ids(interaction)

    self.bot.db.ensure_guild(guild_id)

    user = self.bot.db.ensure_user(member_id=member_id, guild_id=guild_id)

    # Check if ready
    now = datetime.now()
    next_claim = user.lastclaimed + timedelta(hours=24)

    if now < next_claim:
      embed = discord.Embed(
        title='Dailies!',
        description="Hold up!\nYour time isn't up yet!",
        colour=discord.Colour.red(),
      )

      remaining = next_claim - now

      total_seconds = int(remaining.total_seconds())
      hours, remainder = divmod(total_seconds, 3600)
      minutes, seconds = divmod(remainder, 60)

      daily_status = f'{hours}h {minutes}m {seconds}s'
      embed.description = (
        embed.description or ''
      ) + f'\nPlease wait another {daily_status}'

      embed.set_footer(
        text=f'Requested by {interaction.user.name}', icon_url=interaction.user.avatar
      )

      await interaction.response.send_message(embed=embed)

      return

    user.coins = self.bot.db.DAILY_BONUS_COINS

    total_levels, total_coins = self.bot.db.add_xp(
      guild_id=guild_id, member_id=member_id, xp=self.bot.db.DAILY_XP_BONUS, user=user
    )

    user.lastclaimed = datetime.now()

    self.bot.db.update_user(guild_id=guild_id, member_id=member_id, user=user)

    embed = discord.Embed(
      title='Dailies!',
      description="Here's your daily reward!",
      colour=discord.Colour.green(),
    )
    embed.add_field(
      name='Rewards',
      value=f'Coins: {self.bot.db.DAILY_BONUS_COINS}\nXP: {self.bot.db.DAILY_XP_BONUS}',
    )

    if total_levels != 0:
      embed.add_field(
        name='You leveled up!',
        value=f'Earned Coins: {total_coins}\nEarned Levels: {total_levels}',
      )

    embed.set_footer(
      text=f'Requested by {interaction.user.name}', icon_url=interaction.user.avatar
    )

    await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
  await bot.add_cog(UserActions(bot))  # type: ignore
