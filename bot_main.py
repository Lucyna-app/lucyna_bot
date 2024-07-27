import os
import discord
from discord.ext import commands
import aiohttp
import io


intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix=["l", "L"], intents=intents)


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith("$hello"):
        await message.channel.send("Hello!")

    # This is crucial for both on_message and commands to work
    await client.process_commands(message)


@client.command(name="r", aliases=["roll"])
async def roll_command(ctx):
    roll_url = "http://127.0.0.1:8000/bot/commands/roll"

    async with aiohttp.ClientSession() as session:
        async with session.get(roll_url) as response:
            if response.status == 200:
                # Read image data
                image_data = await response.read()

                image_file = discord.File(io.BytesIO(image_data), filename="roll.png")

                await ctx.message.reply(
                    f"{ctx.author.mention} rolled some cards ^^", file=image_file
                )
            else:
                await ctx.message.reply(
                    "Sorry, I couldn't get the roll image. Please try again later D:"
                )


botToken = os.getenv("LUCYNA_BOT_TOKEN")
client.run(botToken)
