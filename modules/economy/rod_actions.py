from typing import List
from discord.ext import commands
from discord import app_commands

from discord import ui

from fisher_bot import FisherBot

import discord

from models.fuser import FUser
from models.rod import Rod


class RodManagerView(ui.View):
  def __init__(
    self,
    bot: FisherBot,
    user: FUser,
    member_id: int,
    rod: Rod,
    data: List[Rod],
    owned_ids: List[int],
  ):
    super().__init__(timeout=60)

    self.bot = bot

    self.user = user
    self.rod = rod

    self.member_id = member_id

    self.current_page = 0
    self.total_pages = len(data)

    self.owned_ids = owned_ids
    self.data = data

    self.update_buttons()

  async def interaction_check(self, interaction: discord.Interaction) -> bool:
    if interaction.user.id != self.member_id:
      await interaction.response.send_message(
        "This isn't your fishing shop! Use the command yourself to browse.",
        ephemeral=True,
      )
      return False
    return True

  def update_buttons(self):
    self.children[0].disabled = self.current_page == 0  # type: ignore
    self.children[1].disabled = self.current_page == self.total_pages - 1  # type: ignore

    current_rod = self.data[self.current_page]
    owned = current_rod.id in self.owned_ids
    is_equipped = self.rod.id == current_rod.id
    too_low_level = self.user.level < current_rod.level_required
    too_low_money = self.user.coins < current_rod.value

    self.children[2].disabled = (not owned) or is_equipped  # type: ignore
    self.children[3].disabled = (owned or too_low_level) or too_low_money  # type: ignore

  async def update_message(self, interaction: discord.Interaction):
    embed = await self.format_page()
    await interaction.response.edit_message(embed=embed, view=self)

  async def format_page(self) -> discord.Embed:
    embed = discord.Embed(title='Rod Management Office!', colour=discord.Colour.green())

    active_rod = self.data[self.current_page]
    owned = active_rod.id in self.owned_ids

    embed.add_field(
      name=f'{active_rod.name} ("{active_rod.description}") {("[owned]" if owned else "")}',
      value=f'Price: {active_rod.value}\nCatch Rate: ({active_rod.min_catch}, {active_rod.max_catch})\nLevel Needed: {active_rod.level_required}\nEscape chance: 1/{active_rod.line_break_chance}\nXP Multiplier: x{active_rod.xp_multiplier}',
    )

    embed.set_footer(text=f'Page {self.current_page + 1}/{self.total_pages}')

    return embed

  @ui.button(label='Previous', style=discord.ButtonStyle.blurple)
  async def prev_button(
    self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    if not await self.interaction_check(interaction):
      return

    self.current_page -= 1
    self.update_buttons()

    await self.update_message(interaction)

  @ui.button(label='Next', style=discord.ButtonStyle.blurple)
  async def next_button(
    self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    if not await self.interaction_check(interaction):
      return

    self.current_page += 1
    self.update_buttons()

    await self.update_message(interaction)

  @ui.button(label='Equip', style=discord.ButtonStyle.red)
  async def equip_button(
    self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    if not await self.interaction_check(interaction):
      return

    if interaction.guild_id is None:
      return

    self.bot.db.equip_rod(
      self.member_id, interaction.guild_id, self.data[self.current_page].id
    )

    self.rod = self.bot.db.get_user_rod(self.member_id, interaction.guild_id)

    self.update_buttons()
    await self.update_message(interaction)

  @ui.button(label='Buy', style=discord.ButtonStyle.green)
  async def buy_button(
    self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    if not await self.interaction_check(interaction):
      return

    if interaction.guild_id is None:
      return

    active_rod = self.data[self.current_page]

    self.user.coins -= active_rod.value
    self.bot.db.update_user(interaction.guild_id, self.member_id, self.user)

    self.bot.db.add_rod(self.member_id, interaction.guild_id, active_rod.id)

    self.update_buttons()
    await self.update_message(interaction)


class RodActions(commands.Cog):
  def __init__(self, bot: FisherBot):
    self.bot = bot

  @app_commands.command(
    name='rodmanager', description='Want a new toy? Check this out!'
  )
  @app_commands.guild_only()
  async def manager(self, interaction: discord.Interaction):
    guild_id, member_id = self.bot.get_guildmember_ids(interaction)

    self.bot.db.ensure_guild(guild_id)

    user = self.bot.db.ensure_user(member_id=member_id, guild_id=guild_id)
    rod = self.bot.db.get_user_rod(member_id=member_id, guild_id=guild_id)

    all_rods = self.bot.db.get_user_rods(member_id=member_id, guild_id=guild_id)
    ids = [rod.id for rod in all_rods]

    manager = RodManagerView(
      self.bot, user, member_id, rod, self.bot.fish_service.rods, ids
    )
    embed = await manager.format_page()

    await interaction.response.send_message(embed=embed, view=manager)


async def setup(bot: commands.Bot):
  await bot.add_cog(RodActions(bot))  # type: ignore
