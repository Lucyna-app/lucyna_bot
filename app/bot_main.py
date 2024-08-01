import os
import discord
import asyncio
from discord.ext import commands
from app.config import COMMAND_PREFIX, BOT_TOKEN


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")


async def load_extensions():
    for filename in os.listdir("./app/cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"app.cogs.{filename[:-3]}")
                print(f"Loaded extension: {filename[:-3]}")
            except Exception as e:
                print(f"Failed to load extension {filename[:-3]}: {str(e)}")


async def main():
    async with bot:
        await load_extensions()
        await bot.start(BOT_TOKEN)


def run_bot():
    asyncio.run(main())
