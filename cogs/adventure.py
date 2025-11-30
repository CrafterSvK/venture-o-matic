import discord
from discord.ext import commands
from discord import app_commands
import random

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from cogs.pvp import paginate_rounds, LogPagination
from db import SessionLocal
from engine.creature_engine import Creature
from engine.fight_engine import FightEngine
from loader import t
from models import Character, EquippedItem


class Adventure(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="adventure", description="Go on a short adventure.")
    async def adventure(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        async with SessionLocal() as session:
            char = await session.scalar(
                select(Character)
                .where(Character.user_id == interaction.user.id)
                .options(selectinload(Character.equipment).selectinload(EquippedItem.item_instance))
            )

            if not char:
                return await interaction.followup.send(t("general.no_character"), ephemeral=True)

            if random.randint(1, 6) == 6:
                reward = random.randint(1, 10)
                char.gold += reward

                await session.commit()

                return await interaction.followup.send(t(f"adventure.reward", reward=reward), ephemeral=True)

            creature_lvl = char.level + random.uniform(-10, 10)
            creature = Creature(name="Demon", level=1 if creature_lvl < 0 else creature_lvl)

            fight_engine = FightEngine()

            winner, loser, battle_log = fight_engine.resolve_duel(char, creature)

            pages = paginate_rounds(battle_log, 5)
            view = LogPagination(pages)

            if winner is char:
                reward = random.randint(1, 10)
                char.gold += reward
                char.add_xp(10)

                await session.commit()

            await interaction.followup.send(
                content=view.format_page(),
                view=view
            )

async def setup(bot):
    await bot.add_cog(Adventure(bot))
