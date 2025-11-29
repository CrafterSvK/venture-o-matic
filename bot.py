import os

import discord
from discord.ext import commands
import asyncio

import loader
from db import engine
from models import Base

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="~", intents=intents)

initial_cogs = [
    "cogs.adventure",
    "cogs.characters",
    "cogs.crafting",
    "cogs.economy",
    "cogs.equipment",
    "cogs.marketplace",
    "cogs.professions",
    "cogs.pvp",
]

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.tree.error
async def on_app_command_error(interaction, error):
    print("Slash command error:")
    import traceback
    traceback.print_exception(type(error), error, error.__traceback__)

async def main():
    loader.load_all_data()
    loader.load_translations('en')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # temp assurance

    for cog in initial_cogs:
        try:
            await bot.load_extension(cog)
            print(f"[OK] Loaded {cog}")
        except Exception as e:
            print(f"[ERROR] Failed to load {cog}: {e}")

    await bot.start(os.environ["TOKEN"])

if __name__ == "__main__":
    asyncio.run(main())
