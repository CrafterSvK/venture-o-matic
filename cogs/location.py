import discord
from discord.ext import commands
from discord import app_commands
import random

from sqlalchemy import select

from db import SessionLocal
from loader import t, DATA
from models import Character

class Location(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="travel", description="Travel to another location.")
    async def adventure(self, interaction: discord.Interaction, location: str):
        if location not in DATA.locations.locations.keys():
            return await interaction.response.send_message(t("general.no_location"))

        async with SessionLocal() as session:
            char = await session.scalar(
                select(Character).where(Character.user_id == interaction.user.id)
            )

            if not char:
                return await interaction.response.send_message(t("general.no_character"))

            char.location = location

            await session.commit()

        await interaction.response.send_message(t("general.traveled_to_location", location=t(f"location.{location}")))

async def setup(bot):
    await bot.add_cog(Location(bot))
