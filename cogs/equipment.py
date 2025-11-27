import discord
from discord.ext import commands
from discord import app_commands
from sqlalchemy import select

from loader import DATA, t
from db import SessionLocal
from models import Character, Inventory, EquippedItem

class Equipment(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="equip", description="Equip an item from your inventory.")
    async def equip(self, interaction: discord.Interaction, item: str):
        if DATA.items.items.get(item) is None:
            return await interaction.response.send_message("Unknown item.")

        item_data = DATA.items.items.get(item)

        if item_data.slot is None:
            return await interaction.response.send_message("You cannot equip this item.")

        async with SessionLocal() as session:
            char = await session.scalar(select(Character).where(Character.user_id == interaction.user.id))
            if not char:
                return await interaction.response.send_message(t("general.no_character"))

            inv = await session.scalar(
                select(Inventory).where(
                    (Inventory.character_id == char.id) &
                    (Inventory.template_id == item) &
                    (Inventory.amount > 0)
                )
            )
            if not inv:
                return await interaction.response.send_message("You do not own this item.")

            # Unequip existing item in same slot
            existing = await session.scalar(
                select(EquippedItem).where(
                    (EquippedItem.character_id == char.id) &
                    (EquippedItem.slot == item_data.slot)
                )
            )
            if existing:
                session.delete(existing)

            equip = EquippedItem(
                character_id=char.id,
                item_instance=item, # todo
                slot=item_data.slot
            )
            session.add(equip)
            await session.commit()

        await interaction.response.send_message(
            f"Equipped **{item_data['name']}** in **{item_data.slot}** slot."
        )

    @app_commands.command(name="unequip", description="Unequip an item")
    async def unequip(self, interaction: discord.Interaction, slot: str):
        async with SessionLocal() as session:
            char = await session.scalar(select(Character).where(Character.user_id == interaction.user.id))
            if not char:
                return await interaction.response.send_message(t("general.no_character"))

            eq = await session.scalar(
                select(EquippedItem).where(
                    (EquippedItem.character_id == char.id) &
                    (EquippedItem.slot == slot)
                )
            )

            if not eq:
                return await interaction.response.send_message("Nothing equipped in that slot.")

            session.delete(eq)
            await session.commit()

        await interaction.response.send_message(f"Unequipped item from slot **{slot}**.")

async def setup(bot):
    await bot.add_cog(Equipment(bot))
