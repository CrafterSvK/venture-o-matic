import discord
from discord.ext import commands
from discord import app_commands
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from engine.fight_engine import FightEngine
from loader import t
from db import SessionLocal
from models import Character, EquippedItem

def paginate_rounds(lines: list[str], rounds_per_page: int = 5) -> list[str]:
    pages: list[str] = []

    current_page: list[list[str]] = []
    current_block: list[str] = []

    def finish_block():
        nonlocal current_block, current_page, pages
        if not current_block:
            return

        current_page.append(current_block)
        current_block = []

        if len(current_page) == rounds_per_page:
            flat = [ln for block in current_page for ln in block]
            pages.append("\n".join(flat))
            current_page = []

    for line in lines:
        if line.startswith("**Round"):
            finish_block()
        current_block.append(line)

    finish_block()

    if current_page:
        flat = [ln for block in current_page for ln in block]
        pages.append("\n".join(flat))

    return pages

class LogPagination(discord.ui.View):
    def __init__(self, pages: list[str]):
        super().__init__(timeout=180)
        self.pages = pages
        self.index = 0

    def format_page(self):
        return f"Page {self.index + 1}/{len(self.pages)}\n```ansi\n{self.pages[self.index]}\n```"

    @discord.ui.button(label="◀️ Prev", style=discord.ButtonStyle.primary)
    async def prev(self, interaction: discord.Interaction, _):
        if self.index > 0:
            self.index -= 1
        await interaction.response.edit_message(content=self.format_page(), view=self)

    @discord.ui.button(label="Next ▶️", style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, _):
        if self.index < len(self.pages) - 1:
            self.index += 1
        await interaction.response.edit_message(content=self.format_page(), view=self)

class DuelButtons(discord.ui.View):
    def __init__(self, cog, challenger, challenged):
        super().__init__()
        self.cog = cog
        self.challenger = challenger
        self.challenged = challenged

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, _):
        if interaction.user.id != self.challenged.user_id:
            return await interaction.response.send_message(
                t("pvp.not_your_duel"), ephemeral=True
            )
        await interaction.response.defer()
        await interaction.message.edit(view=None)
        await self.cog.start_duel(interaction, self.challenger, self.challenged)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, _):
        if interaction.user.id != self.challenged.user_id:
            return await interaction.response.send_message(
                t("pvp.not_your_duel"), ephemeral=True
            )

        await interaction.response.send_message(
            f"{self.challenger.name}'s challenge was declined.",
            ephemeral=True
        )
        await interaction.message.edit(view=None)
        self.stop()

class PvP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.engine = FightEngine()

    async def start_duel(self, interaction, challenger, challenged):
        winner, loser, battle_log = self.engine.resolve_duel(challenger, challenged)

        async with SessionLocal() as session:
            await session.execute(
                update(Character)
                .where(Character.id == winner.id)
                .values(gold = winner.gold + 50)
            )
            await session.execute(
                update(Character)
                .where(Character.id == loser.id)
                .values(gold = max(0, loser.gold - 25))
            )
            await session.commit()

        pages = paginate_rounds(battle_log, 5)
        view = LogPagination(pages)

        await interaction.followup.send(
            content=view.format_page(),
            view=view
        )

    @app_commands.command(name="challenge", description="Challenge another player to a duel.")
    async def challenge(self, interaction: discord.Interaction, opponent: discord.User):
        async with SessionLocal() as session:
            challenger = await session.scalar(
                select(Character)
                .where(Character.user_id == interaction.user.id)
                .options(selectinload(Character.equipment).selectinload(EquippedItem.item_instance))
            )

            challenged = await session.scalar(
                select(Character)
                .where(Character.user_id == opponent.id)
                .options(selectinload(Character.equipment).selectinload(EquippedItem.item_instance))
            )

        if not challenger:
            return await interaction.response.send_message(t("general.no_character"))

        if not challenged:
            return await interaction.response.send_message(t("pvp.no_opponent_character"))

        await interaction.response.send_message(
            f"{challenger.name} challenges {challenged.name}!",
            view=DuelButtons(self, challenger, challenged)
        )


async def setup(bot):
    await bot.add_cog(PvP(bot))
