import discord
import os

from discord.ext import commands
from dotenv import load_dotenv


load_dotenv()
TOKEN = os.environ['FISHER_TOKEN']

class fisher_bot(commands.Bot):
  def __init__(self):
    intents = discord.Intents.default()
    intents.message_content = True

    super().__init__(command_prefix='!', intents=intents)

  async def on_ready(self):
    print(f'Logged in as {self.user.name} - {self.user.id}')


  async def setup_hook(self):
    for root, dirs, files in os.walk('commands'):
      for file in files:
        if file.endswith('.py'):
          path = os.path.relpath(os.path.join(root, file), 'commands').replace('\\', '.').replace('.py', '')

          if path.startswith('_'):
            continue

          try:
            await self.load_extension(f'commands.{path}')
            print(f'Loaded command: {path}')
          except Exception as e:
            print(f'Failed to load command {path}: {e}')

    print('Syncing.')
    try:
      synced = await self.tree.sync()
      print(f"Synced {len(synced)} command(s) globally.")
    except Exception as e:
      print(f"Failed to sync commands: {e}")


client: fisher_bot = fisher_bot()
client.run(TOKEN)
