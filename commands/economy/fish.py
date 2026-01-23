from collections import Counter
from discord.ext import commands
from discord import app_commands
import discord

import random

from models.area import Area
from models.fish import Fish
from util.weighted_random import WeightedRandom


class Fishing(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot


  @app_commands.command(name="fish", description="Go fishing to catch some fish!")
  async def fish(self, interaction: discord.Interaction, area: Area):
    guildid: int = interaction.guild.id
    memberid: int = interaction.user.id

    self.bot.db.ensure_guild(guildid)
    self.bot.db.ensure_user(memberid, guildid)

    caught_fish: list[Fish] = []
    fish: WeightedRandom = getattr(self.bot.fish_service, area.name)

    fish_count = random.randint(1, 5)
    for _ in range(fish_count):
      caught_fish.append(fish.get())

    caught_data = [(f.id, f.name) for f in caught_fish]

    ordered_fish_count = Counter(caught_data)

    summary_parts = []
    for (fish_id, fish_name), count in ordered_fish_count.items():
      summary_parts.append(f"{count}x {fish_name}")
      print(fish_id)
      print(fish_name)
      self.bot.db.add_fish(guildid, memberid, fish_id, count)

    summary = ", ".join(summary_parts)

    await interaction.response.send_message(f"You went fishing in the {area.name} and caught: {summary}")


async def setup(bot: commands.Bot):
  await bot.add_cog(Fishing(bot))
