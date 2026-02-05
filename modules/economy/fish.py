from collections import Counter
from discord.ext import commands
from discord import app_commands
import discord

import random

from datetime import datetime
import datetime

from fisher_bot import FisherBot
from models.area import Area
from models.fish import Fish
from models.rod import Rod
from util.weighted_random import WeightedRandom


class Fishing(commands.Cog):
  def __init__(self, bot: FisherBot):
    self.bot = bot

    self.user_cooldowns = []


  @app_commands.command(name="fish", description="Go fishing to catch some fish!")
  @app_commands.guild_only()
  async def fish(self, interaction: discord.Interaction, area: Area):
    guild_id, member_id = self.bot.get_guildmember_ids(interaction)


    self.bot.db.ensure_guild(guild_id)
    user = self.bot.db.ensure_user(member_id, guild_id)

    user_found = False
    for (id, stamp) in self.user_cooldowns:
      if id == member_id:
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
      self.user_cooldowns.append((member_id, datetime.datetime.now()))

    caught_fish: list[Fish] = []
    fish: WeightedRandom = getattr(self.bot.fish_service, area.name)

    rod = self.bot.db.get_user_rod(member_id, guild_id)

    fish_count = random.randint(rod.min_catch, rod.max_catch)
    escaped = 0
    for _ in range(fish_count):
      if random.randint(1, rod.line_break_chance) == 1:
        escaped += 1
        continue

      caught_fish.append(fish.get())

    caught_data = [(f.id, f.name, f.rarity) for f in caught_fish]

    ordered_fish_count = Counter(caught_data)

    summary_parts = []
    for (fish_id, fish_name, fish_rarity), count in ordered_fish_count.items():
      summary_parts.append(f"{count}x {fish_name} ({fish_rarity.name.title()})")
      self.bot.db.add_fish(guild_id, member_id, fish_id, count)

    summary = "\n".join(summary_parts)
    if escaped != 0:
      summary += f"\nOops! {escaped} fish escaped!"

    summary_embed = discord.Embed(
      colour=discord.Colour.blue(),
      title=f"You cast your line into the {area.name}...",
      description=f"You caught:\n{summary}"
    )
    summary_embed.timestamp = datetime.datetime.now()
    summary_embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.display_avatar.url)

    await interaction.response.send_message(embed=summary_embed)


async def setup(bot: commands.Bot):
  await bot.add_cog(Fishing(bot)) # type: ignore
