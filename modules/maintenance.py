from discord.ext import commands
from discord import app_commands

import discord

from fisher_bot import FisherBot


class Maintenance(commands.Cog):
  def __init__(self, bot: FisherBot):
    self.bot = bot

  @app_commands.command(name='ping', description="Check the bot's latency.")
  @app_commands.guild_only()
  async def ping(self, interaction: discord.Interaction):
    latency = round(self.bot.latency * 1000)
    await interaction.response.send_message(f'Pong! Latency: {latency}ms')


async def setup(bot: commands.Bot):
  await bot.add_cog(Maintenance(bot))  # type: ignore
