import discord
from discord.ext import commands
from discord import app_commands
import random

from sqlalchemy import select

from db import SessionLocal
from loader import t
from models import Character

class Adventure(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="adventure", description="Go on a short adventure.")
    async def adventure(self, interaction: discord.Interaction):
        async with SessionLocal() as session:
            char = await session.scalar(
                select(Character).where(Character.user_id == interaction.user.id)
            )

            if not char:
                return await interaction.response.send_message(t("general.no_character"))

            reward = random.randint(1, 10)
            char.gold += reward

            await session.commit()

        await interaction.response.send_message(f"🗺️ You earned **{reward} gold**!")

async def setup(bot):
    await bot.add_cog(Adventure(bot))
