import discord
from discord.ext import commands
from discord import app_commands
from sqlalchemy import select

from loader import DATA, t
from db import SessionLocal
from models import Character, CharacterProfession

class Professions(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="learn", description="Learn a profession")
    async def learn(self, interaction: discord.Interaction, profession: str):
        if DATA.professions.get(profession) is None:
            return await interaction.response.send_message("Unknown profession.")

        async with SessionLocal() as session:
            char = await session.scalar(select(Character).where(Character.user_id == interaction.user.id))
            if not char:
                return await interaction.response.send_message(t("general.no_character"))

            existing = await session.scalar(
                select(CharacterProfession).where(
                    (CharacterProfession.character_id == char.id) &
                    (CharacterProfession.profession_id == profession)
                )
            )

            if existing:
                return await interaction.response.send_message("Already learned.")

            prof = CharacterProfession(character_id=char.id, profession_id=profession)
            session.add(prof)
            await session.commit()

        await interaction.response.send_message(
            t("profession.learned", profession=DATA.professions.get(profession)["name"])
        )

async def setup(bot):
    await bot.add_cog(Professions(bot))
