import discord
from discord import ButtonStyle, Interaction
import aiohttp
from app.config import API_URL


class RollView(discord.ui.View):
    def __init__(self, art_uuid4s, author):
        super().__init__(timeout=60)
        self.api_url = API_URL
        self.art_uuid4s = art_uuid4s
        self.author = author
        self.has_claimed = False

    async def interaction_check(self, interaction: Interaction) -> bool:
        return interaction.user.id == self.author.id

    @discord.ui.button(label="1", style=ButtonStyle.primary, custom_id="button1")
    async def button1_callback(
        self, interaction: Interaction, button: discord.ui.Button
    ):
        await self.button_click(interaction, button, 0)

    @discord.ui.button(label="2", style=ButtonStyle.primary, custom_id="button2")
    async def button2_callback(
        self, interaction: Interaction, button: discord.ui.Button
    ):
        await self.button_click(interaction, button, 1)

    @discord.ui.button(label="3", style=ButtonStyle.primary, custom_id="button3")
    async def button3_callback(
        self, interaction: Interaction, button: discord.ui.Button
    ):
        await self.button_click(interaction, button, 2)

    async def button_click(
        self, interaction: Interaction, button: discord.ui.Button, index: int
    ):
        if self.has_claimed:
            await interaction.response.send_message(
                "You've already claimed a card.", ephemeral=True
            )
            return

        claim_url = f"{self.api_url}/commands/roll/claim"
        async with aiohttp.ClientSession() as session:
            async with session.post(
                claim_url,
                json={
                    "user_id": str(interaction.user.id),
                    "art_uuid4": self.art_uuid4s[index],
                },
            ) as response:
                if response.status == 200:
                    self.has_claimed = True
                    button.style = ButtonStyle.green
                    button.disabled = True
                    button.label = "Claimed"

                    for child in self.children:
                        child.disabled = True

                    await interaction.response.edit_message(view=self)
                    await interaction.followup.send(
                        "You claimed a card ^^", ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        "Failed to process claim.", ephemeral=True
                    )
