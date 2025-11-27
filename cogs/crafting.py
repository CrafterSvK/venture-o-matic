import json
import random
import discord

from discord.ext import commands
from discord import app_commands
from sqlalchemy import select

from loader import DATA, weighted_choice, t
from db import SessionLocal
from models import Character, ItemInstance, Inventory


def roll_affix(affix_pool: dict):
    """Weighted random pick of an affix."""
    total = sum(a["weight"] for a in affix_pool.values())
    r = random.uniform(0, total)
    s = 0
    for name, aff in affix_pool.items():
        s += aff["weight"]
        if r <= s:
            return name, aff
    return list(affix_pool.items())[-1]


def roll_affix_stats(affix_def: dict):
    """Return rolled stats for a single affix, ex: {'attack': 2.5}"""
    rolled = {}
    if "stats" not in affix_def:
        return rolled

    for stat, range_def in affix_def["stats"].items():
        min_v = range_def["min"]
        max_v = range_def["max"]
        rolled[stat] = round(random.uniform(min_v, max_v), 2)

    return rolled


class Crafting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="craft", description="Craft an item")
    async def craft(self, interaction: discord.Interaction, item: str):

        # --- BASIC VALIDATION -------------------------------------------------
        if item not in DATA["crafting"]:
            return await interaction.response.send_message("Unknown craft item.")

        recipe = DATA["crafting"][item]
        template = DATA["items"]["items"][item]
        affix_data = DATA["affixes"]

        # --- DB SESSION -------------------------------------------------------
        async with SessionLocal() as session:

            # LOAD CHARACTER
            char = await session.scalar(
                select(Character).where(Character.user_id == interaction.user.id)
            )

            if not char:
                return await interaction.response.send_message("No character.")

            # CHECK MATERIALS
            missing = []
            for req_item, amount in recipe["requires"].items():
                inv = await session.scalar(
                    select(Inventory).where(
                        (Inventory.character_id == char.id)
                        & (Inventory.template_id == req_item)
                    )
                )
                if not inv or inv.amount < amount:
                    missing.append(req_item)

            if missing:
                return await interaction.response.send_message(f"Missing: {missing}")

            # CONSUME MATERIALS
            for req_item, amount in recipe["requires"].items():
                inv = await session.scalar(
                    select(Inventory).where(
                        (Inventory.character_id == char.id)
                        & (Inventory.template_id == req_item)
                    )
                )
                inv.amount -= amount

            # --- RARITY ROLL ---------------------------------------------------
            type_roll_table = DATA["rarity_rolls"]["crafting"][template["type"]]
            rolled_rarity = weighted_choice(type_roll_table)

            rarity_def = DATA["items"]["rarities"][rolled_rarity]

            # --- BASE STATS ----------------------------------------------------
            final_stats = {}
            base_stats = template.get("base_stats", {})

            for stat, value in base_stats.items():
                final_stats[stat] = value

            # --- AFFIX ROLLING -------------------------------------------------
            affix_count_min = rarity_def["affix_count"]["min"]
            affix_count_max = rarity_def["affix_count"]["max"]
            affix_count = random.randint(affix_count_min, affix_count_max)

            prefixes_pool = affix_data["prefixes"]
            suffixes_pool = affix_data["suffixes"]

            affixes = {"prefixes": [], "suffixes": []}
            affix_extra_stats = {}

            for _ in range(affix_count):
                # 50% chance prefix vs suffix
                if random.random() < 0.5:
                    affix_name, affix_def = roll_affix(prefixes_pool)
                    affixes["prefixes"].append(affix_name)
                else:
                    affix_name, affix_def = roll_affix(suffixes_pool)
                    affixes["suffixes"].append(affix_name)

                rolled = roll_affix_stats(affix_def)

                for s, v in rolled.items():
                    affix_extra_stats[s] = affix_extra_stats.get(s, 0) + v

            # ADD AFFIX STATS TO TOTAL
            for s, v in affix_extra_stats.items():
                final_stats[s] = final_stats.get(s, 0) + v

            # APPLY RARITY MULTIPLIER
            mult = rarity_def["stat_multiplier"]
            for s in final_stats:
                final_stats[s] = round(final_stats[s] * mult, 2)

            # --- SAVE ITEM INSTANCE -------------------------------------------
            instance = ItemInstance(
                owner_id=char.id,
                template_id=item,
                rarity=rolled_rarity,
                rolled_stats=json.dumps(final_stats),
                affixes=json.dumps(affixes),
            )

            session.add(instance)
            await session.commit()

        # --- RESPONSE ---------------------------------------------------------
        result_text = (
            f"You crafted **{t(f"items.{item}")}**\n"
            f"Rarity: **{rolled_rarity}**\n"
            f"Affixes: {affixes}\n"
            f"Stats: {final_stats}"
        )

        await interaction.response.send_message(result_text)


async def setup(bot):
    await bot.add_cog(Crafting(bot))
