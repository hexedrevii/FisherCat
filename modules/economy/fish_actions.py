import discord
import math

from discord import app_commands
from discord.ext import commands

from discord import ui

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
      desc += f'{fish_data[0].name.title()} x{fish_data[1]} (value of {fish_data[0].base_value} coins, {fish_data[0].xp} XP) [{fish_data[0].rarity.name.title()}]\n'

    embed.add_field(
      name=f'Current rod: {self.rod.name} "{self.rod.description}"',
      value=f'Fish range: ({self.rod.min_catch}, {self.rod.max_catch})\nLine Break Chance: 1/{self.rod.line_break_chance}{("Value: {self.rod.value}\n" if self.rod.value != 0 else '')}\nXP Multiplier: {self.rod.xp_multiplier}',
      inline=False
    )

    embed.description = desc

    embed.set_footer(text=f"Page {self.current_page + 1}/{self.total_pages}")
    return embed


class SellingView(ui.View):
  def __init__(self, fish_id: int, member_id: int, guild_id: int, bot: FisherBot, fish_data: tuple[Fish, int], user: FUser):
    super().__init__(timeout=60)

    self.fishid = int(fish_id)
    self.fish_to_sell = 1

    self.fish_data = fish_data

    self.bot = bot
    self.user = user

    self.member_id = member_id
    self.guild_id = guild_id

    self.update_buttons()


  def update_buttons(self):
    self.children[0].disabled = self.fish_to_sell + 1 > self.fish_data[1] # type: ignore
    self.children[1].disabled = self.fish_to_sell + 5 > self.fish_data[1] # type: ignore
    self.children[2].disabled = self.fish_to_sell + 10 > self.fish_data[1] # type: ignore
    self.children[3].disabled = self.fish_to_sell + 50 > self.fish_data[1] # type: ignore
    self.children[4].disabled = self.fish_to_sell + 100 > self.fish_data[1] # type: ignore

    self.children[5].disabled = self.fish_to_sell - 1 < 1 # type: ignore
    self.children[6].disabled = self.fish_to_sell - 5 < 1 # type: ignore
    self.children[7].disabled = self.fish_to_sell - 10 < 1 # type: ignore
    self.children[8].disabled = self.fish_to_sell - 50 < 1 # type: ignore
    self.children[9].disabled = self.fish_to_sell - 100 < 1 # type: ignore


  async def create_embed(self, interaction: discord.Interaction):
    embed = discord.Embed(
      title='Fish MegaMart!',
      description=f'You have a total of {self.fish_data[1]} {self.fish_data[0].name}.\nCurrently on the chopping block: {self.fish_to_sell}',
      colour=discord.Colour.gold()
    )

    await interaction.response.edit_message(embed=embed, view=self)


  @discord.ui.button(label="+1", style=discord.ButtonStyle.blurple)
  async def sell_one(self, interaction: discord.Interaction, button: ui.Button):
    self.fish_to_sell += 1
    self.update_buttons()

    await self.create_embed(interaction)


  @discord.ui.button(label="+5", style=discord.ButtonStyle.blurple)
  async def sell_five(self, interaction: discord.Interaction, button: ui.Button):
    self.fish_to_sell += 5
    self.update_buttons()

    await self.create_embed(interaction)


  @discord.ui.button(label="+10", style=discord.ButtonStyle.blurple)
  async def sell_ten(self, interaction: discord.Interaction, button: ui.Button):
    self.fish_to_sell += 10
    self.update_buttons()

    await self.create_embed(interaction)


  @discord.ui.button(label="+50", style=discord.ButtonStyle.blurple)
  async def sell_fifty(self, interaction: discord.Interaction, button: ui.Button):
    self.fish_to_sell += 50
    self.update_buttons()

    await self.create_embed(interaction)


  @discord.ui.button(label="+100", style=discord.ButtonStyle.blurple)
  async def sell_onehunge(self, interaction: discord.Interaction, button: ui.Button):
    self.fish_to_sell += 100
    self.update_buttons()

    await self.create_embed(interaction)


  @discord.ui.button(label="-1", style=discord.ButtonStyle.blurple)
  async def remove_one(self, interaction: discord.Interaction, button: ui.Button):
    self.fish_to_sell -= 1
    self.update_buttons()

    await self.create_embed(interaction)


  @discord.ui.button(label="-5", style=discord.ButtonStyle.blurple)
  async def remove_five(self, interaction: discord.Interaction, button: ui.Button):
    self.fish_to_sell -= 5
    self.update_buttons()

    await self.create_embed(interaction)


  @discord.ui.button(label="-10", style=discord.ButtonStyle.blurple)
  async def remove_ten(self, interaction: discord.Interaction, button: ui.Button):
    self.fish_to_sell -= 10
    self.update_buttons()

    await self.create_embed(interaction)


  @discord.ui.button(label="-50", style=discord.ButtonStyle.blurple)
  async def remove_fifty(self, interaction: discord.Interaction, button: ui.Button):
    self.fish_to_sell -= 50
    self.update_buttons()

    await self.create_embed(interaction)


  @discord.ui.button(label="-100", style=discord.ButtonStyle.blurple)
  async def remove_onehunge(self, interaction: discord.Interaction, button: ui.Button):
    self.fish_to_sell -= 100
    self.update_buttons()

    await self.create_embed(interaction)


  @discord.ui.button(label='all', style=discord.ButtonStyle.secondary) # type: ignore
  async def add_all(self, interaction: discord.Integration, button: discord.ui.Button):
    self.fish_to_sell = self.fish_data[1]
    self.update_buttons()

    await self.create_embed(interaction) # type: ignore


  @discord.ui.button(label="sell", style=discord.ButtonStyle.green)
  async def finish_transaction(self, interaction: discord.Interaction, button: discord.ui.Button):
    count = self.fish_data[1] - self.fish_to_sell

    self.bot.db.update_user_fish(self.member_id, self.guild_id, self.fishid, count)

    coins_earned = self.fish_data[0].base_value * self.fish_to_sell
    self.user.coins += coins_earned

    rod = self.bot.db.get_user_rod(member_id= self.member_id, guild_id= self.guild_id)
    assert rod is not None

    xp_earned = math.floor(self.fish_data[0].xp * self.fish_to_sell * rod.xp_multiplier)
    total_levels, total_coins = self.bot.db.add_xp(guild_id=self.guild_id, member_id=self.member_id, xp=xp_earned, user=self.user)

    self.bot.db.update_user(self.guild_id, self.member_id, self.user)

    embed = discord.Embed(title='Fish MegaMart!', description=f'You sold {self.fish_to_sell} {self.fish_data[0].name} for {coins_earned} coins and {xp_earned} XP!', colour=discord.Colour.green())

    if total_levels != 0:
      embed.add_field(name='You leveled up!', value=f'Coins Earned: {total_coins}\nLevels Earned: {total_levels}')

    self.stop()
    await interaction.response.edit_message(embed=embed, view=None)


  @discord.ui.button(label="cancel", style=discord.ButtonStyle.red)
  async def cancel_all(self, interaction: discord.Interaction, button: discord.ui.Button):
    embed = discord.Embed(title='You leave the Fish MegaMart with nothing sold...', colour=discord.Colour.red())

    self.stop()
    await interaction.response.edit_message(embed=embed, view=None)


class FishingActions(commands.Cog):
  def __init__(self, bot: FisherBot):
    self.bot = bot

  @app_commands.command(name='inventory', description='Look at your fish and rod!')
  @app_commands.guild_only()
  async def inventory(self, interaction: discord.Interaction):
    guildid = interaction.guild_id
    memberid = interaction.user.id

    assert guildid is not None
    assert memberid is not None

    self.bot.db.ensure_guild(guildid)

    _ = self.bot.db.ensure_user(memberid, guildid)

    rod = self.bot.db.get_user_rod(memberid, guildid)
    assert rod is not None

    fish = self.bot.db.get_all_user_fish(guildid, memberid)

    paginator = InventoryPaginator(data=fish, rod=rod)
    first_page_entries = paginator.get_current_page_data()
    first_embed = await paginator.format_page(first_page_entries)

    await interaction.response.send_message(embed=first_embed, view=paginator)


  async def fish_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    guildid = interaction.guild_id
    memberid = interaction.user.id

    assert guildid is not None
    assert memberid is not None

    inventory = self.bot.db.get_all_user_fish(guildid, memberid)
    assert inventory is not None

    choices = []
    for fish_obj, count in inventory:
      if current.lower() in fish_obj.name.lower():
        choices.append(
          app_commands.Choice(
            name=f"{fish_obj.name.title()} (x{count})",
            value=str(fish_obj.id)
          )
        )

    return choices[:25]


  @app_commands.command(name='sell', description='Sell your unwanted fish!')
  @app_commands.guild_only()
  @app_commands.autocomplete(fish=fish_autocomplete)
  async def sell(self, interaction: discord.Interaction, fish: str):
    guild_id = interaction.guild_id
    member_id = interaction.user.id

    assert guild_id is not None

    self.bot.db.ensure_guild(guild_id)

    user = self.bot.db.ensure_user(member_id, guild_id)
    assert user is not None

    fish_data = self.bot.db.get_user_fish(guild_id, member_id, int(fish))
    assert fish_data is not None

    embed = discord.Embed(
      title='Fish MegaMart!',
      description=f'You have a total of {fish_data[1]} {fish_data[0].name}.\nCurrently on the chopping block: 1',
      colour=discord.Colour.gold()
    )

    view = SellingView(fish_id=int(fish), member_id=member_id, guild_id=guild_id, bot=self.bot, fish_data=fish_data, user=user)

    await interaction.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot):
  await bot.add_cog(FishingActions(bot)) # type: ignore
