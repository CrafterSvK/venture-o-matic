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


async def craftable_item_autocomplete(_: discord.Interaction, current: str):
    craftable_items = list(DATA.crafting.keys())
    matches = [
        app_commands.Choice(name=t(f"item.{item}"), value=item)
        for item in craftable_items
        if current.lower() in t(f"item.{item}").lower()
    ]
    return matches[:25]


class Crafting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="craft", description="Craft an item")
    @app_commands.autocomplete(
        item=craftable_item_autocomplete
    )
    async def craft(self, interaction: discord.Interaction, item: str):
        if item not in DATA.crafting:
            return await interaction.response.send_message(t("crafting.unknown"))

        recipe = DATA.crafting[item]
        template = DATA.items.items[item]
        affix_data = DATA.affixes

        async with SessionLocal() as session:
            char = await session.scalar(
                select(Character).where(Character.user_id == interaction.user.id)
            )

            if not char:
                return await interaction.response.send_message(t("general.no_character"))

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
                return await interaction.response.send_message(t('crafting.missing_items', items=", ".join(missing)))

            for req_item, amount in recipe["requires"].items():
                inv = await session.scalar(
                    select(Inventory).where(
                        (Inventory.character_id == char.id)
                        & (Inventory.template_id == req_item)
                    )
                )
                inv.amount -= amount

            type_roll_table = DATA.rarity_rolls["crafting"][template.type]
            rolled_rarity = weighted_choice(type_roll_table)

            rarity_def = DATA.items.rarities[rolled_rarity]

            final_stats = {}
            base_stats = template.base_stats

            for stat, value in base_stats.items():
                final_stats[stat] = value

            affix_count_min = rarity_def.affix_count.min
            affix_count_max = rarity_def.affix_count.max
            affix_count = random.randint(affix_count_min, affix_count_max)

            prefixes_pool = affix_data["prefixes"]
            suffixes_pool = affix_data["suffixes"]

            affixes = {"prefixes": [], "suffixes": []}
            affix_extra_stats = {}

            for _ in range(affix_count):
                if random.random() < 0.5:
                    affix_name, affix_def = roll_affix(prefixes_pool)
                    affixes["prefixes"].append(affix_name)
                else:
                    affix_name, affix_def = roll_affix(suffixes_pool)
                    affixes["suffixes"].append(affix_name)

                rolled = roll_affix_stats(affix_def)

                for s, v in rolled.items():
                    affix_extra_stats[s] = affix_extra_stats.get(s, 0) + v

            for s, v in affix_extra_stats.items():
                final_stats[s] = final_stats.get(s, 0) + v

            mult = rarity_def.stat_multiplier
            for s in final_stats:
                final_stats[s] = round(final_stats[s] * mult, 2)

            instance = ItemInstance(
                owner_id=char.id,
                template_id=item,
                rarity=rolled_rarity,
                rolled_stats=json.dumps(final_stats),
                affixes=json.dumps(affixes),
            )

            session.add(instance)
            await session.commit()

        result_text = t(
            "crafting.success",
            item=instance,
            stats=f"{"\n".join([f"- {key}: {value}" for key, value in final_stats.items()])}"
        )

        await interaction.response.send_message(result_text)


async def setup(bot):
    await bot.add_cog(Crafting(bot))
