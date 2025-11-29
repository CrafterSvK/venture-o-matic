import discord
from discord.ext import commands
from discord import app_commands
from sqlalchemy import select

from generated.character_schema import CharacterData
from loader import DATA, t
from db import SessionLocal
from models import Character, Inventory, EquippedItem

class Equipment(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="equip", description="Equip an item from your inventory.")
    async def equip(self, interaction: discord.Interaction, item: str):
        if DATA.items.items.get(item) is None:
            return await interaction.response.send_message(t("crafting.unknown"))

        item_data = DATA.items.items.get(item)

        if item_data.slot is None:
            return await interaction.response.send_message(t("character.cannot_equip"))

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
                return await interaction.response.send_message(t("character.not_owned_item"))

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

        return await interaction.response.send_message(
            f"Equipped **{item_data['name']}** in **{item_data.slot}** slot."
        )

    @app_commands.command(name="unequip", description="Unequip an item")
    async def unequip(self, interaction: discord.Interaction, slot: str):
        if slot not in CharacterData.slots:
            return await interaction.response.send_message(t("character.invalid_slot"))

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
                return await interaction.response.send_message(t("character.nothing_equipped"))

            session.delete(eq)
            await session.commit()

        return await interaction.response.send_message(t("character.unequipped", slot=slot, item=eq.item_instance))

async def setup(bot):
    await bot.add_cog(Equipment(bot))
