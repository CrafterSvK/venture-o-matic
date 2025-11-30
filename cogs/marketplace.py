import json
import discord
from discord.ext import commands
from discord import app_commands
from sqlalchemy import select

from db import SessionLocal
from models import Character, ItemInstance
from loader import t


class Marketplace(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="market_list")
    async def market_list(self, interaction, item_id: int, price: int):
        async with SessionLocal() as session:
            item = await session.get(ItemInstance, item_id)
            if not item:
                return await interaction.response.send_message("Invalid item.")

            if item.owner_id != (
                    await session.scalar(select(Character).where(Character.user_id == interaction.user.id))
            ).id:
                return await interaction.response.send_message("You don't own this item.")

            item.is_listed = True
            item.list_price = price

            await session.commit()
            return await interaction.response.send_message(f"Item listed for {price} gold.")

    @app_commands.command(name="market_browse")
    async def market_browse(self, interaction):
        async with SessionLocal() as session:
            listed = await session.execute(
                select(ItemInstance).where(ItemInstance.is_listed == True)
            )
            listed = listed.scalars()

            if not listed:
                return await interaction.response.send_message("No items on the market.")

            embed = discord.Embed(title="Marketplace")

            for inst in listed:
                stats = json.loads(inst.rolled_stats)

                embed.add_field(
                    name=f"Item #{inst.id}",
                    value=t("market.entry", item=inst, stats=stats, price=inst.list_price),
                    inline=False,
                )

        return await interaction.response.send_message(embed=embed)

    @app_commands.command(name="market_buy")
    async def market_buy(self, interaction, listing_id: int):
        async with SessionLocal() as session:
            buyer = await session.scalar(select(Character).where(Character.user_id == interaction.user.id))

            item = await session.get(ItemInstance, listing_id)
            if not item or not item.is_listed:
                return await interaction.response.send_message("Listing not found.")

            if buyer.gold < item.list_price:
                return await interaction.response.send_message("Not enough gold.")

            seller = await session.get(Character, item.owner_id)

            # money transfer
            buyer.gold -= item.list_price
            seller.gold += item.list_price

            # change item ownership
            item.owner_id = buyer.id
            item.is_listed = False
            item.list_price = 0

            await session.commit()

        return await interaction.response.send_message("Purchase successful!")

async def setup(bot):
    await bot.add_cog(Marketplace(bot))
