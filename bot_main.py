import os
import discord
from discord.ext import commands
from discord import ButtonStyle, Interaction
from datetime import datetime, timedelta
import aiohttp
import io
import base64


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


class RollView(discord.ui.View):
    def __init__(self, api_url, art_uuid4s, author):
        super().__init__(timeout=60)
        self.api_url = api_url
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

        claim_url = f"{self.api_url}/claim"
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

                    # Disable all buttons
                    for child in self.children:
                        child.disabled = True

                    await interaction.response.edit_message(view=self)
                    result = await response.json()
                    await interaction.followup.send(
                        f"You claimed a card ^^",
                        ephemeral=True,
                    )
                else:
                    await interaction.response.send_message(
                        "Failed to process claim.", ephemeral=True
                    )


@client.command(name="r", aliases=["roll", "R", "ROLL"])
@commands.cooldown(1, 120, commands.BucketType.user)
async def roll_command(ctx):
    roll_url = "http://127.0.0.1:8000/bot/commands/roll"

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
                    view = RollView(roll_url, art_uuid4s, ctx.author)
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
        print(f"An error occured: {str(e)}")
        await ctx.message.reply("An error occurred while processing your request.")


@roll_command.error
async def roll_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        # Calculate remaining time
        minutes, seconds = divmod(error.retry_after, 60)
        hours, minutes = divmod(minutes, 60)

        # Formatting time string
        time_str = ""
        if hours > 0:
            time_str += f"**{int(hours)}h** "
        if minutes > 0:
            time_str += f"**{int(minutes)}m** "
        time_str += f"**{int(seconds)}s**"

        await ctx.send(f"Woah there. You can roll again in {time_str}.")
    else:
        await ctx.send(f"An error occurred: {str(error)}")


class CollectionView(discord.ui.View):
    def __init__(self, api_url, user_id, timeout=60):
        super().__init__(timeout=timeout)
        self.api_url = api_url
        self.user_id = user_id
        self.page = 1
        self.sort_by = "claim_time"
        self.sort_order = "desc"

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def previous_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if self.page > 1:
            self.page -= 1
            await self.update_collection(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
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
    async def sort_select(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        self.sort_by = select.values[0]
        self.page = 1
        await self.update_collection(interaction)

    @discord.ui.button(label="↑↓", style=discord.ButtonStyle.primary)
    async def toggle_sort_order(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.sort_order = "asc" if self.sort_order == "desc" else "desc"
        await self.update_collection(interaction)

    async def update_collection(self, interaction: discord.Interaction):
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


def create_collection_embed(data, page):
    embed = discord.Embed(title="Your Card Collection", color=discord.Color.blue())
    embed.set_footer(text=f"Page {page} | Total Cards: {data['total_cards']}")

    for card in data["cards"]:
        embed.add_field(
            name=f"{card['character_name']} ({card['series']})",
            # value=f"Rarity: {card['rarity']}\nClaimed: {card['claim_time']}\nCode: {card['custom_code'] or 'N/A'}",
            value="",
            inline=False,
        )

    return embed


@client.command(name="c", aliases=["collection"])
async def collection_command(ctx):
    user_id = str(ctx.author.id)

    api_url = "http://127.0.0.1:8000/bot"

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{api_url}/commands/collection", params={"user_id": user_id, "page": 1}
        ) as response:
            if response.status == 200:
                data = await response.json()
                if data["total_cards"] == 0:
                    await ctx.send(
                        "You don't have any cards in your collection yet. Try dropping with 'lr'!"
                    )
                else:
                    embed = create_collection_embed(data, 1)
                    view = CollectionView(api_url, user_id)
                    await ctx.send(embed=embed, view=view)
            else:
                await ctx.send(
                    "Failed to fetch your collection. Please try again later."
                )


botToken = os.getenv("LUCYNA_BOT_TOKEN")
client.run(botToken)
