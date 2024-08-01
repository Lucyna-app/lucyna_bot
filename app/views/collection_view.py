import discord
from discord import Interaction
import aiohttp
from app.config import API_URL
from app.embeds.collection_embed import create_collection_embed


class CollectionView(discord.ui.View):
    def __init__(self, user_id, timeout=60):
        super().__init__(timeout=timeout)
        self.api_url = API_URL
        self.user_id = user_id
        self.page = 1
        self.sort_by = "claim_time"
        self.sort_order = "desc"

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def previous_button(
        self, interaction: Interaction, button: discord.ui.Button
    ):
        if self.page > 1:
            self.page -= 1
            await self.update_collection(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: Interaction, button: discord.ui.Button):
        self.page += 1
        await self.update_collection(interaction)

    @discord.ui.select(
        placeholder="Sort by...",
        options=[
            discord.SelectOption(label="Claim Time", value="claim_time"),
            discord.SelectOption(label="Character Name", value="character_name"),
            discord.SelectOption(label="Series", value="series"),
            discord.SelectOption(label="Rarity", value="rarity"),
        ],
    )
    async def sort_select(self, interaction: Interaction, select: discord.ui.Select):
        self.sort_by = select.values[0]
        self.page = 1
        await self.update_collection(interaction)

    @discord.ui.button(label="↑↓", style=discord.ButtonStyle.primary)
    async def toggle_sort_order(
        self, interaction: Interaction, button: discord.ui.Button
    ):
        self.sort_order = "asc" if self.sort_order == "desc" else "desc"
        await self.update_collection(interaction)

    async def update_collection(self, interaction: Interaction):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_url}/commands/collection",
                params={
                    "user_id": self.user_id,
                    "page": self.page,
                    "sort_by": self.sort_by,
                    "sort_order": self.sort_order,
                },
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    embed = create_collection_embed(data, self.page)
                    await interaction.response.edit_message(embed=embed, view=self)
                else:
                    await interaction.response.send_message(
                        "Failed to fetch collection.", ephemeral=True
                    )
