import discord


def create_collection_embed(data, page):
    embed = discord.Embed(title="Your Card Collection", color=discord.Color.blue())
    embed.set_footer(text=f"Page {page} | Total Cards: {data['total_cards']}")

    for card in data["cards"]:
        embed.add_field(
            name=f"{card['character_name']} ({card['series']})",
            value=f"Rarity: {card['rarity']}\nClaimed: {card['claim_time']}\nCode: {card['custom_code'] or 'N/A'}",
            inline=False,
        )

    return embed
