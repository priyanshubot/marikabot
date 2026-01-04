import discord
import os
import asyncio
import logging
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TERMINAL_LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", 0))
PREFIX = os.getenv("COMMAND_PREFIX", "!")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger("marika_main")

class DiscordLogHandler(logging.Handler):
    def __init__(self, bot_instance, channel_id):
        super().__init__()
        self.bot = bot_instance
        self.channel_id = channel_id
        self.setFormatter(logging.Formatter('`%(asctime)s` **%(levelname)s**: %(message)s', datefmt='%H:%M:%S'))

    def emit(self, record):
        if "discord" in record.name or "http" in record.name: return
        log_entry = self.format(record)
        if self.bot and self.bot.loop.is_running():
            self.bot.loop.create_task(self.send_log(log_entry))

    async def send_log(self, text):
        try:
            channel = self.bot.get_channel(self.channel_id)
            if channel: await channel.send(text[:2000])
        except: pass

intents = discord.Intents.default()
intents.message_content = True 
intents.members = True 
intents.voice_states = True

class MarikaBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=PREFIX, intents=intents, help_command=None)
        self.log = log

    async def setup_hook(self):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
                print(f"Loaded: {filename}")
        print(f"Slash Commands ready. Use {PREFIX}sync to force update if needed.")

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print(f"Active Prefix: {self.command_prefix}")
        if TERMINAL_LOG_CHANNEL_ID:
            self.log.addHandler(DiscordLogHandler(self, TERMINAL_LOG_CHANNEL_ID))
        self.log.info("System Online. The Golden Order is restored.")

bot = MarikaBot()

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)