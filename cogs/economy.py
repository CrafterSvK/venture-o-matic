import discord
from discord.ext import commands
from discord import app_commands
from sqlalchemy import select

from loader import DATA, t
from db import SessionLocal
from models import Character, Inventory

async def shop_autocomplete(interaction: discord.Interaction, current: str):
    async with SessionLocal() as session:
        character_location = await session.scalar(
            select(Character.location)
            .where(Character.user_id == interaction.user.id)
        )

        shops = list(DATA.locations.locations[character_location].shops)
        matches = [
            app_commands.Choice(name=t(f"shop.{shop}"), value=shop)
            for shop in shops
            if current.lower() in t(f"shop.{shop}").lower()
        ]
        return matches[:25]

class Economy(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="shop", description="Browse a shop")
    async def shop(self, interaction: discord.Interaction, shop: str):
        if shop not in DATA.shops:
            return await interaction.response.send_message(t("shop.not_found"))

        shop_data = DATA.shops[shop]

        item_ids = shop_data["sells"]

        items_text = "\n".join(f"- " + t(f"item.{item_id}") for item_id in item_ids)

        await interaction.response.send_message(
            f"**{shop_data['name']}** sells:\n{items_text}"
        )

    @app_commands.command(name="buy", description="Buy an item from a shop")
    async def buy(self, interaction: discord.Interaction, shop: str, item: str):
        if DATA.shops.get(shop) is None:
            return await interaction.response.send_message(t("shop.not_found"))

        shop_data = DATA.shops.get(shop)

        if item not in shop_data['sells']:
            return await interaction.response.send_message(t("shop.not_found"))

        price = DATA.items.items[item].base_value

        async with SessionLocal() as session:
            char = await session.scalar(select(Character).where(Character.user_id == interaction.user.id))
            if not char:
                return await interaction.response.send_message(t("general.no_character"))

            if char.gold < price:
                return await interaction.response.send_message(t("shop.no_gold"))

            char.gold -= price

            inv = await session.scalar(
                select(Inventory).where(
                    (Inventory.character_id == char.id) &
                    (Inventory.template_id == item)
                )
            )

            if inv:
                inv.amount += 1
            else:
                inv = Inventory(character_id=char.id, template_id=item, amount=1)
                session.add(inv)

            await session.commit()

        await interaction.response.send_message(
            t("shop.bought", item=t(f"item.{item}"), price=price)
        )

async def setup(bot):
    await bot.add_cog(Economy(bot))
