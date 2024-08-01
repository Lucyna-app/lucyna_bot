from discord.ext import commands
import discord
from app.views.roll_view import RollView
from app.config import API_URL
import aiohttp
import io
import base64


class Roll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="r", aliases=["roll", "R", "ROLL"])
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def roll_command(self, ctx):
        roll_url = f"{API_URL}/commands/roll"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(roll_url) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        image_data = base64.b64decode(response_data["image"])
                        art_uuid4s = response_data["art_uuid4s"]

                        image_file = discord.File(
                            io.BytesIO(image_data), filename="roll.png"
                        )
                        view = RollView(art_uuid4s, ctx.author)
                        await ctx.message.reply(
                            f"{ctx.author.mention} rolled some cards ^^",
                            file=image_file,
                            view=view,
                        )
                    else:
                        await ctx.message.reply(
                            "Sorry, I couldn't get the roll image. Please try again later D:"
                        )
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            await ctx.message.reply("An error occurred while processing your request.")

    @roll_command.error
    async def roll_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            minutes, seconds = divmod(error.retry_after, 60)
            hours, minutes = divmod(minutes, 60)
            time_str = ""
            if hours > 0:
                time_str += f"**{int(hours)}h** "
            if minutes > 0:
                time_str += f"**{int(minutes)}m** "
            time_str += f"**{int(seconds)}s**"
            await ctx.send(f"Woah there. You can roll again in {time_str}.")
        else:
            await ctx.send(f"An error occurred: {str(error)}")


async def setup(bot):
    await bot.add_cog(Roll(bot))
