from discord.ext import commands
from app.views.collection_view import CollectionView
from app.embeds.collection_embed import create_collection_embed
from app.config import API_URL
import aiohttp


class Collection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="c", aliases=["collection"])
    async def collection_command(self, ctx):
        user_id = str(ctx.author.id)

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_URL}/commands/collection", params={"user_id": user_id, "page": 1}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data["total_cards"] == 0:
                        await ctx.send(
                            "You don't have any cards in your collection yet. Try dropping with 'lr'!"
                        )
                    else:
                        embed = create_collection_embed(data, 1)
                        view = CollectionView(user_id)
                        await ctx.send(embed=embed, view=view)
                else:
                    await ctx.send(
                        "Failed to fetch your collection. Please try again later."
                    )


async def setup(bot):
    await bot.add_cog(Collection(bot))
