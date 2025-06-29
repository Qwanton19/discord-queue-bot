# main.py
import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

# actually hiding token this time
load_dotenv()
TOKEN = os.environ['discord_token']

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')


intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True

# not used but still needed?
bot = commands.Bot(command_prefix="!", intents=intents)


# logging that the bot is starting up and working
@bot.event
async def on_ready():
    """Event that fires when the bot is ready and connected to Discord."""
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    # load cog and sync slash commands
    try:
        await bot.load_extension('cogs.queue_cog')
        print("Queue Cog loaded successfully.")
    except Exception as e:
        print(f"Error loading cog: {e}")

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")


# running the bot
if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)
    else:
        print("Discord token not found.")