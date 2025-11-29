import discord
from discord.ext import commands
from discord import app_commands
from sqlalchemy import select, update
from loader import t
from db import SessionLocal
from models import Character


class PvP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="challenge", description="Challenge another player to a duel.")
    async def challenge(self, interaction: discord.Interaction, opponent: discord.User):
        """Allow a player to challenge another player."""
        if opponent.id == interaction.user.id:
            return await interaction.response.send_message(t("pvp.self_challenge"))

        async with SessionLocal() as session:
            # Fetch both players' characters
            challenger = await session.scalar(
                select(Character).where(Character.user_id == interaction.user.id)
            )
            challenged = await session.scalar(
                select(Character).where(Character.user_id == opponent.id)
            )

            if not challenger:
                return await interaction.response.send_message(t("general.no_character"))

            if not challenged:
                return await interaction.response.send_message(t("pvp.no_opponent_character"))

        await interaction.response.send_message(
            t("pvp.challenge_sent", opponent=opponent.mention)
        )

        # Send a follow-up message to confirm the duel using a button
        await self.send_duel_confirmation(interaction, challenger, challenged)

    async def send_duel_confirmation(self, interaction, challenger, challenged):
        """Send a confirmation message for the challenge with accept/decline buttons."""

        class DuelButtons(discord.ui.View):
            def __init__(self, bot, challenger, challenged):
                super().__init__()
                self.bot = bot
                self.challenger = challenger
                self.challenged = challenged

            @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
            async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != self.challenged.user_id:
                    return await interaction.response.send_message(
                        t('pvp.not_your_duel'), ephemeral=True
                    )

                # správna osoba → začať duel
                await interaction.response.defer()
                await interaction.message.edit(view=None)
                await self.start_duel(interaction)

            @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
            async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != self.challenged.user_id:
                    return await interaction.response.send_message(
                        t('pvp.not_your_duel'), ephemeral=True
                    )

                await interaction.response.send_message(
                    t("pvp.challenge_declined", challenger=self.challenger.name), ephemeral=True
                )
                await interaction.message.edit(view=None)
                self.stop()

            async def start_duel(self, interaction: discord.Interaction):
                self.stop()

                # Calculate the outcome of the fight
                winner, loser = self.resolve_duel()

                async with SessionLocal() as session:
                    # Basic reward for winner and punishment for loser
                    session.execute(
                        update(Character)
                        .where(Character.id == winner.id)
                        .values(gold=winner.gold + 50)
                    )
                    session.execute(
                        update(Character)
                        .where(Character.id == loser.id)
                        .values(gold=max(0, loser.gold - 25))
                    )
                    await session.commit()

                await interaction.followup.send(
                    t(
                        "pvp.duel_result",
                        winner=winner.name,
                        loser=loser.name,
                        reward="50 gold",
                        penalty="25 gold",
                    )
                )

            def resolve_duel(self):
                """Simulate the duel using basic logic."""
                challenger_stats = self.challenger.gold  # Example stat (use HP, level, etc.)
                challenged_stats = self.challenged.gold  # Replace with actual stats from DB

                # Determine the winner and loser based on stats
                if challenger_stats >= challenged_stats:
                    return self.challenger, self.challenged
                else:
                    return self.challenged, self.challenger

        # Send the buttons for accept/decline
        view = DuelButtons(self.bot, challenger, challenged)
        await interaction.followup.send(
            t("pvp.confirmation_message", challenger=challenger.name, challenged=challenged.name),
            view=view,
        )


async def setup(bot):
    await bot.add_cog(PvP(bot))
