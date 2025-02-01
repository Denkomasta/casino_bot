import discord
import traceback
from discord.ext import commands
from base_classes import Game, Player, Bet
from enums import BaccaratBetType, GameType, E, GameState, PlayerState
from baccarat.baccarat import BaccaratPlayer, BaccaratBet
from ui import UI
from blackjack.cmd_handler_blackjack import BlackJackCmdHandler

class BlackJackHitStandUI(UI):
    def __init__(self, game: Game):
        super().__init__(game)

    @discord.ui.button(label="HIT", style=discord.ButtonStyle.green)
    async def handle_hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await BlackJackCmdHandler.cmd_hit(self.game, interaction, ["hit"])
        if self.game.players[interaction.user.id].state == PlayerState.PLAYING:
            await interaction.response.send_message("What si your next move?", view=BlackJackHitStandUI(self.game), ephemeral=True)
        else:
            await interaction.response.send_message("You cannot hit anymore")


    @discord.ui.button(label="STAND", style=discord.ButtonStyle.red)
    async def handle_stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        await BlackJackCmdHandler.cmd_stand(self.game, interaction, ["stand"])
        await interaction.response.send_message("You STAND", ephemeral=True, delete_after=1)