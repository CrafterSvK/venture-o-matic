import discord
from discord.ext import commands
from discord import app_commands
from sqlalchemy import select

from db import SessionLocal
from loader import t
from models import Character

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
            )

        if not result:
            return await interaction.response.send_message(t("general.no_character"))

        embed = discord.Embed(title=t("character.profile", name=result.name))
        # embed.add_field(name="Level", value=result.level)
        # embed.add_field(name="HP", value=result.hp)
        embed.add_field(name=t("general.location"), value=result.location)
        embed.add_field(name=t("general.gold"), value=result.gold)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Characters(bot))
