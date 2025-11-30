import discord
from discord.ext import commands
from discord import app_commands

from sqlalchemy import select

from db import SessionLocal
from loader import t, DATA
from models import Character


async def location_autocomplete(_: discord.Interaction, current: str):
    locations = list(DATA.locations.locations.keys())
    matches = [
        app_commands.Choice(name=t(f"location.{location}"), value=location)
        for location in locations
        if current.lower() in t(f"location.{location}").lower()
    ]
    return matches[:25]


class Location(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="travel", description="Travel to another location.")
    @app_commands.autocomplete(
        location=location_autocomplete
    )
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

    @app_commands.command(name="look_around", description="Look around you.")
    async def look_around(self, interaction: discord.Interaction):
        async with SessionLocal() as session:
            character = await session.scalar(
                select(Character).where(Character.user_id == interaction.user.id)
            )

            if not character:
                return await interaction.response.send_message(t("general.no_character"))

            if character.location == "spawn":
                return await interaction.response.send_message("Limbo")

            embed = discord.Embed(title=t(f'location.{character.location}'))
            embed.add_field(name=t("location.features"), value="\n".join([t(feature) for feature in DATA.locations.locations[character.location].features]))
            embed.add_field(name=t("location.features"), value="\n".join([t(shop) for shop in DATA.locations.locations[character.location].shops]))

            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Location(bot))
