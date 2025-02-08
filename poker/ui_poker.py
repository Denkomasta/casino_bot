import discord
import traceback
from discord.ext import commands
from base_classes import Game, Player, Bet
from enums import BaccaratBetType, GameType, E, GameState, PlayerState, PokerPlayerState
from ui import UI, GameUserInterface, BetUI
from poker.cmd_handler_poker import PokerCmdHandler
from poker.poker import Poker
from math import log10

class PokerUI(BetUI):
    def __init__(self, game: Game):
        super().__init__(game)

class Poker_ingame(UI):
    def __init__(self, game: Game, id: int, is_raised = False):
        super().__init__(game)
        self.on_turn_id = id
        self.value: PokerPlayerState | None = None

        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.label == "CHECK":
                item.label = "CALL" if is_raised else "CHECK"

    @discord.ui.button(label="CHECK", style=discord.ButtonStyle.blurple, row=0)
    async def handle_check(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.on_turn_id:
            await interaction.response.send_message(f"{interaction.user.mention} Please wait for your turn!")
            return
        await PokerCmdHandler.cmd_check(self.game, interaction, ["check"])
        self.value = PokerPlayerState.CHECKED
        self.stop()

    @discord.ui.button(label="RAISE", style=discord.ButtonStyle.green, row=0)
    async def handle_check(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.on_turn_id:
            await interaction.response.send_message(f"{interaction.user.mention} Please wait for your turn!")
            return
        modal = RaiseModal(self.game, interaction.user.id)
        await interaction.response.send_modal(modal)
        await modal.wait()
        self.value = PokerPlayerState.RAISED
        self.stop()

    @discord.ui.button(label="FOLD", style=discord.ButtonStyle.red, row=0)
    async def handle_check(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.on_turn_id:
            await interaction.response.send_message(f"{interaction.user.mention} Please wait for your turn!")
            return
        await PokerCmdHandler.cmd_fold(self.game, interaction, ["fold"])
        self.value = PokerPlayerState.FOLDED
        self.stop()

class RaiseModal(discord.ui.Modal, title="Place Your Bet"):
    def __init__(self, game: Poker, author_id):
        self.game = game
        self.author_id = author_id
        self.hint_message = f"E.g. 100 (max {self.game.players[author_id].bet.value} in your bank)"
        self.max_length = int(log10(self.game.players[author_id].bet.value))

        self.amount_input = discord.ui.TextInput(
            label="Enter an amount you want to raise the bet to:",
            placeholder=self.hint_message,
            required=True,
            min_length=1,
            max_length=self.max_length
        )
        self.add_item(self.amount_input)

    async def on_submit(self, interaction):
        await PokerCmdHandler.cmd_raise(self.game, interaction, ["raise", self.amount_input.value])