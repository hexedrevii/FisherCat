from discord.ext import commands
from discord import app_commands

import discord


class maintenance(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot


  @app_commands.command(name="ping", description="Check the bot's latency.")
  async def ping(self, interaction: discord.Interaction):
    latency = round(self.bot.latency * 1000)
    await interaction.response.send_message(f'Pong! Latency: {latency}ms')


async def setup(bot: commands.Bot):
  await bot.add_cog(maintenance(bot))
