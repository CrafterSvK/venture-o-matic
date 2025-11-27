import discord
from discord.ext import commands
from discord import app_commands
from sqlalchemy import select

from db import SessionLocal
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
                return await interaction.response.send_message("❌ You already have a character.")

            char = Character(
                user_id=interaction.user.id,
                name=name,
            )
            session.add(char)
            await session.commit()

        await interaction.response.send_message(f"✅ Character **{name}** created!")

    @app_commands.command(name="profile", description="Show your RPG character.")
    async def profile(self, interaction: discord.Interaction, user: discord.User | None = None):
        user = user or interaction.user

        async with SessionLocal() as session:
            result: Character | None = await session.scalar(
                select(Character).where(Character.user_id == user.id)
            )

        if not result:
            return await interaction.response.send_message("❌ No character found.")

        embed = discord.Embed(title=f"{result.name}'s Profile")
        # embed.add_field(name="Level", value=result.level)
        # embed.add_field(name="HP", value=result.hp)
        embed.add_field(name="Gold", value=result.gold)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Characters(bot))
