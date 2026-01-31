import discord
from discord import app_commands
from discord.ext import commands

from fisher_bot import FisherBot
from models.fish import Fish
from models.fuser import FUser
from models.rod import Rod
from util.paginator_view import PaginatorView


class InventoryPaginator(PaginatorView):
  def __init__(self, data, rod: Rod, per_page=5, timeout=60):
    super().__init__(data, per_page=per_page, timeout=timeout, title="Inventory")
    self.rod = rod


  async def format_page(self, entries):
    embed = discord.Embed(title = "Inventory", colour=discord.Colour.blue())

    desc = ''
    for i, fish_data in enumerate(entries):
      desc += f'{fish_data[0].name.title()} x{fish_data[1]} (value of {fish_data[0].base_value})\n'

    embed.add_field(
      name=f'Current rod: {self.rod.name}',
      value=f'Fish range: ({self.rod.min_catch}, {self.rod.max_catch})\nLine Break Chance: 1/{self.rod.line_break_chance}{("Value: {self.rod.value}\n" if self.rod.value != 0 else '')}',
      inline=False
    )

    embed.description = desc

    embed.set_footer(text=f"Page {self.current_page + 1}/{self.total_pages}")
    return embed


class FishingActions(commands.Cog):
  def __init__(self, bot: FisherBot):
    self.bot = bot

  @app_commands.command(name='inventory', description='Look at your fish and rod!')
  async def inventory(self, interaction: discord.Interaction):
    guildid = interaction.guild_id
    memberid = interaction.user.id

    self.bot.db.ensure_guild(guildid)

    _ = self.bot.db.ensure_user(guildid, memberid)

    rod: Rod = self.bot.db.get_user_rod(guildid, memberid)
    fish: list[(Fish, int)] = self.bot.db.get_all_user_fish(guildid, memberid)

    paginator = InventoryPaginator(data=fish, rod=rod)
    first_page_entries = paginator.get_current_page_data()
    first_embed = await paginator.format_page(first_page_entries)

    await interaction.response.send_message(embed=first_embed, view=paginator)


async def setup(bot: commands.Bot):
  await bot.add_cog(FishingActions(bot))
