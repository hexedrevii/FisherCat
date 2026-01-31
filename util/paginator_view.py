from typing import Any
from discord import ui
from discord.ext import commands
import discord


class PaginatorView(ui.View):
  def __init__(self, data, per_page = 5, timeout = 60, title = 'results'):
    super().__init__(timeout= timeout)

    self.data = data
    self.per_page = per_page
    self.timeout = timeout
    self.title = title

    self.current_page = 0
    self.total_pages = (len(data) + self.per_page - 1) // self.per_page

    self.update_buttons()


  def update_buttons(self):
    self.children[0].disabled = (self.current_page == 0)
    self.children[1].disabled = (self.current_page == self.total_pages - 1)


  async def update_message(self, interaction: discord.Interaction):
    entries = self.get_current_page_data()
    embed = await self.format_page(entries)
    await interaction.response.edit_message(embed=embed, view=self)


  def get_current_page_data(self) -> list[Any]:
    start = self.current_page * self.per_page
    end = start + self.per_page
    return self.data[start:end]


  async def format_page(self, entries: list[Any]) -> discord.Embed:
    embed = discord.Embed(title=f"{self.title} (Page {self.current_page + 1}/{self.total_pages})")
    description = "\n".join(str(x) for x in entries)
    embed.description = description
    return embed


  @ui.button(label="Previous", style=discord.ButtonStyle.blurple)
  async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
    self.current_page -= 1
    self.update_buttons()
    await self.update_message(interaction)


  @ui.button(label="Next", style=discord.ButtonStyle.blurple)
  async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
    self.current_page += 1
    self.update_buttons()
    await self.update_message(interaction)
