import discord
import traceback
from discord.ext import commands
from base_classes import Game, Player, Bet
from enums import BaccaratBetType, GameType, E, GameState, PlayerState
from baccarat.baccarat import BaccaratPlayer, BaccaratBet
from baccarat.cmd_handler_baccarat import BaccaratCmdHandler
from ui import UI, ReadyUI, BetModal

class BaccaratBetUI(UI):

    def __init__(self, game: Game):
        super().__init__(game)
        self.bet_type: str | None = None
        
    @discord.ui.select(
        placeholder="Choose your bet type...",
        options=[
            discord.SelectOption(label="Player", value=f"player"),
            discord.SelectOption(label="Banker", value=f"banker"),
            discord.SelectOption(label="Tie", value=f"tie"),
        ],
    )
    async def handle_bet_type(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.bet_type = select.values[0]
        if interaction.user.id in self.game.players.keys():
            await BaccaratCmdHandler.cmd_bet(self.game, interaction, ["bet", f"{self.game.players[interaction.user.id].bet.value}", self.bet_type])
        await interaction.response.send_message("Selected succesfully", ephemeral=True, delete_after=1)

    
    @discord.ui.button(label="SET BET AMOUNT", style=discord.ButtonStyle.blurple)
    async def handle_bet_amount(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.bet_type is None:
            await interaction.response.send_message(f"Choose a bet type!", ephemeral=True)
            return
        await interaction.response.send_modal(BaccaratBetModal(self.game, self.bet_type))


class BaccaratBetModal(BetModal):

    def __init__(self, game: Game, type: str):
        super().__init__(game)
        self.bet_type = type
    
    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id not in self.game.players.keys():
            await BaccaratCmdHandler.cmd_join(self.game, interaction, ["join", self.bet_amount.value, self.bet_type])
            await interaction.response.send_message(view=ReadyUI(self.game), ephemeral=True)
        else:
            await BaccaratCmdHandler.cmd_bet(self.game, interaction, ["join", self.bet_amount.value, self.bet_type])
