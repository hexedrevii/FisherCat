from collections import Counter
from discord.ext import commands
from discord import app_commands
import discord

import random

from datetime import datetime
import datetime

from models.area import Area
from models.fish import Fish
from util.weighted_random import WeightedRandom


class Fishing(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot

    self.user_cooldowns = []


  @app_commands.command(name="fish", description="Go fishing to catch some fish!")
  async def fish(self, interaction: discord.Interaction, area: Area):
    guildid: int = interaction.guild.id
    memberid: int = interaction.user.id

    self.bot.db.ensure_guild(guildid)
    user = self.bot.db.ensure_user(memberid, guildid)

    user_found = False
    for (id, stamp) in self.user_cooldowns:
      if id == memberid:
        user_found = True

        # Check if cooldown is gone.
        if datetime.datetime.now() < stamp + datetime.timedelta(seconds=user.fishing_cooldown):
          await interaction.response.send_message(f"You are still recovering from your last fishing trip! Please wait {user.fishing_cooldown}s before going fishing again.", ephemeral=True)
          return
        else:
          self.user_cooldowns.remove((id, stamp))
          user_found = False
          break

    if not user_found:
      self.user_cooldowns.append((memberid, datetime.datetime.now()))

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
      self.bot.db.add_fish(guildid, memberid, fish_id, count)

    summary = "\n".join(summary_parts)

    summary_embed = discord.Embed(
      colour=discord.Colour.blue(),
      title=f"You cast your line into the {area.name}...",
      description=f"You caught:\n{summary}"
    )
    summary_embed.timestamp = datetime.datetime.now()
    summary_embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.display_avatar.url)

    await interaction.response.send_message(embed=summary_embed)


async def setup(bot: commands.Bot):
  await bot.add_cog(Fishing(bot))
