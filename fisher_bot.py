import datetime
import discord
import os
import sys
import math

from discord.ext import commands

from services.db import DbService

from models.fuser import FUser

import sqlite3

from services.fish_service import FishService


# Set to True to drop all tables and reinitialize the database on startup.
DELETE_DEFAULTS: bool = False

LEVEL_INCREASE: float = 0.15
LEVEL_GAP: float = 2.0

COIN_REWARD: int = 50
COIN_REWARD_INCREASE: float = 12.7


class FisherBot(commands.Bot):
  def __init__(self, dbpath):
    intents = discord.Intents.default()
    intents.message_content = True

    super().__init__(command_prefix='!', intents=intents)

    self.fish_service = FishService()

    self.message_cooldowns = []
    self.message_cooldown_time = 2

    print("Connecting to database.")
    self.connection = sqlite3.connect(dbpath)
    self.connection.row_factory = sqlite3.Row

    if DELETE_DEFAULTS:
      from services.db_init import drop_tables, initialize_database, import_fish, import_rods

      if drop_tables(self.connection):
        print("Dropped existing tables.")
      else:
        sys.exit(1)

      if initialize_database(self.connection):
        print("Initialized database.")
      else:
        sys.exit(1)

      if not import_fish(self.connection, self.fish_service): sys.exit(1)
      if not import_rods(self.connection, self.fish_service): sys.exit(1)
    else:
      from services.db_init import load_existing_fish, load_existing_rods
      if not load_existing_fish(self.connection, self.fish_service): sys.exit(1)
      if not load_existing_rods(self.connection, self.fish_service): sys.exit(1)

    self.db = DbService(self.connection)


  async def on_ready(self):
    print(f'Logged in as {self.user.name} - {self.user.id}')


  async def on_message(self, message: discord.Message):
    if message.author.bot: return
    if not message.guild: return

    self.db.ensure_guild(message.guild.id)

    user: FUser = self.db.ensure_user(message.author.id, message.guild.id)

    user_found = False
    for (id, stamp) in self.message_cooldowns:
      if id == message.author.id:
        user_found = True
        if datetime.datetime.now() < stamp + datetime.timedelta(seconds=self.message_cooldown_time):
          return # User is on cooldown
        else:
          user_found = False
          self.message_cooldowns.remove((id, stamp))
          break

    if not user_found:
      self.message_cooldowns.append((message.author.id, datetime.datetime.now()))

    user.xp += user.xp_step
    if user.xp >= user.xp_next:
      total_coins = 0
      while user.xp >= user.xp_next:
        user.xp -= user.xp_next

        user.level += 1

        reward = math.floor(COIN_REWARD + (user.level * COIN_REWARD_INCREASE))

        total_coins += reward
        user.coins += reward

        if user.level % 5 == 0:
          user.xp_step += 5

        user.xp_next = math.floor(math.pow(user.level / LEVEL_INCREASE, LEVEL_GAP))

      await message.channel.send(f"Congrats, {message.author.mention}! You leveled up and earned {total_coins} coins!")

    self.db.update_user(message.guild.id, message.author.id, user)


  async def setup_hook(self):
    for root, dirs, files in os.walk('modules'):
      for file in files:
        if file.endswith('.py'):
          path = os.path.relpath(os.path.join(root, file), 'modules').replace('\\', '.').replace('.py', '')

          if path.startswith('_'):
            continue

          try:
            await self.load_extension(f'modules.{path}')
            print(f'Loaded module: {path}')
          except Exception as e:
            print(f'Failed to load module {path}: {e}')

    print('Syncing.')
    try:
      synced = await self.tree.sync()
      print(f"Synced {len(synced)} command(s) globally.")
    except Exception as e:
      print(f"Failed to sync commands: {e}")
