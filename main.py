import os
from dotenv import load_dotenv

from fisher_bot import FisherBot


load_dotenv()
TOKEN: str = os.environ['FISHER_TOKEN']

client = FisherBot(os.environ['FISHER_DATABASE'])
client.run(TOKEN)
