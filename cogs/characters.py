import json

import discord
from discord.ext import commands
from discord import app_commands
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from db import SessionLocal
from loader import t, DATA
from models import Character, EquippedItem


class Characters(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="create", description="Create your RPG character.")
    async def create(self, interaction: discord.Interaction, name: str):
        async with SessionLocal() as session:
            exists = await session.scalar(
                select(Character).where(Character.user_id == interaction.user.id)
            )

            if exists:
                return await interaction.response.send_message(t("general.already_character"))

            char = Character(
                user_id=interaction.user.id,
                name=name,
            )
            session.add(char)
            await session.commit()

        await interaction.response.send_message(t("general.char_created", name=name))

    @app_commands.command(name="profile", description="Show your RPG character.")
    async def profile(self, interaction: discord.Interaction, user: discord.User | None = None):
        user = user or interaction.user
        assert user

        async with SessionLocal() as session:
            result: Character | None = await session.scalar(
                select(Character).where(Character.user_id == user.id)
                .options(selectinload(Character.equipment).selectinload(EquippedItem.item_instance))
            )

        if not result:
            return await interaction.response.send_message(t("general.no_character"), ephemeral=True)

        embed = discord.Embed(title=t("character.profile", name=result.name))
        embed.add_field(name="Level", value=result.level)
        embed.add_field(name="XP", value=result.xp)
        embed.add_field(name=t("general.location"), value=result.location)
        embed.add_field(name=t("general.gold"), value=result.gold)
        embed.add_field(name=t("general.combat_stats"), value="\n".join([f"{t(k)}: {v}" for k, v in result.combat_stats().items()]))

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="inventory", description="Show items in inventory")
    async def inventory(self, interaction: discord.Interaction):
        async with SessionLocal() as session:
            result: Character | None = await session.scalar(
                select(Character).where(Character.user_id == interaction.user.id)
                .options(selectinload(Character.inventory))
                .options(selectinload(Character.item_instances))
                .options(selectinload(Character.equipment).selectinload(EquippedItem.item_instance))
            )

            if not result:
                return await interaction.response.send_message(t("general.no_character"), ephemeral=True)

            embed = discord.Embed(title=t("character.inventory"))

            for slots in DATA.character.slots:
                item = None
                for inst in result.equipment:
                    if inst.slot == slots:
                        item = inst.item_instance
                        break

                embed.add_field(
                    name=t(f"slots.{slots}"),
                    value=item or t("general.empty")
                )

            embed.add_field(name=t("general.gold"), value=result.gold)
            embed.add_field(name=t("general.items"), value="\n".join(str(item) for item in result.inventory))
            embed.add_field(name=t("general.equipable_items"), value="\n".join(str(item) for item in result.item_instances))

            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Characters(bot))
