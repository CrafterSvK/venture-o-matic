import discord
from discord.ext import commands
from discord import app_commands
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from loader import DATA, t
from db import SessionLocal
from models import Character, EquippedItem, ItemInstance

async def equip_autocomplete(interaction: discord.Interaction, current: str):
    async with SessionLocal() as session:
        character = await session.scalar(
            select(Character)
            .where(Character.user_id == interaction.user.id)
            .options(selectinload(Character.item_instances))
        )

        matches = [
            app_commands.Choice(name=f"{equip.id} {equip.name()}", value=equip.id)
            for equip in character.item_instances
            if current.lower() in f"{equip.id} {equip.name()}".lower()
        ]

        return matches[:25]


class Equipment(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="equip", description="Equip an item from your inventory.")
    @app_commands.autocomplete(
        item=equip_autocomplete
    )
    async def equip(self, interaction: discord.Interaction, item: int):
        async with SessionLocal() as session:
            char = await session.scalar(select(Character).where(Character.user_id == interaction.user.id))
            if not char:
                return await interaction.response.send_message(t("general.no_character"))

            inst: ItemInstance | None = await session.scalar(
                select(ItemInstance).where(ItemInstance.owner_id == char.id).where(ItemInstance.id == item)
            )

            if not inst:
                return await interaction.response.send_message(t("character.not_owned_item"))

            if inst.is_listed:
                return await interaction.response.send_message(f"You cannot equip listed item")

            item_type = DATA.items.items[inst.template_id].type
            slot_name = None
            for name, slot in DATA.character.slots.items():
                if item_type in slot.holds:
                    slot_name = name
                    break

            if slot_name is None:
                return await interaction.response.send_message(f"You cannot equip this")

            # Unequip existing item in same slot
            existing = await session.scalar(
                select(EquippedItem).where(
                    (EquippedItem.character_id == char.id) &
                    (EquippedItem.slot == slot_name)
                )
            )
            if existing:
                await session.delete(existing)

            equip = EquippedItem(
                character_id=char.id,
                item_instance=inst,
                slot=slot_name
            )
            session.add(equip)
            await session.commit()

        return await interaction.response.send_message(
            f"Equipped {inst}"
        )

    @app_commands.command(name="unequip", description="Unequip an item")
    async def unequip(self, interaction: discord.Interaction, slot: str):
        if slot not in DATA.character.slots:
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
                .options(selectinload(EquippedItem.item_instance))
            )

            if not eq:
                return await interaction.response.send_message(t("character.nothing_equipped"))

            await session.delete(eq)
            await session.commit()

            return await interaction.response.send_message(t("character.unequipped", slot=slot, item=eq.item_instance))

async def setup(bot):
    await bot.add_cog(Equipment(bot))
