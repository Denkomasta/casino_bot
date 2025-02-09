import discord
import traceback
from discord.ext import commands
from base_classes import Game, Player, Bet
from enums import BaccaratBetType, GameType, E, GameState, PlayerState, PokerPlayerState
from ui import UI, GameUserInterface, BetUI
from poker.cmd_handler_poker import PokerCmdHandler
from poker.poker import Poker
from math import log10

class PokerBetUI(BetUI):
    def __init__(self, game: Poker):
        super().__init__(game)
        for item in self.children:
            if isinstance(item, discord.ui.Button) and game.type == GameType.POKER:
                match item.label:
                    case "SET BET AMOUNT":
                        item.label = "CHOOSE IN-GAME BANK"
                    case "STATUS":
                        item.label = "PLAYERS AND BANKS"
                    case "BET LIST":
                        item.label = "MY BANK"
        

class Poker_ingame(UI):
    def __init__(self, game: Poker, id: int):
        super().__init__(game)
        self.on_turn_id = id
        self.value: PokerPlayerState | None = None

        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.label == "CHECK":
                item.label = f"CALL TO {game.round_bet}" if game.round_bet > game.players[id].round_bet else "CHECK"
                if item.label == "CHECK":
                    for item in self.children:
                        if isinstance(item, discord.ui.Button) and item.label == "FOLD":
                            item.disabled = True

    @discord.ui.button(label="CHECK", style=discord.ButtonStyle.blurple, row=0)
    async def handle_check(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.on_turn_id:
            await interaction.response.send_message(f"{interaction.user.mention} Please wait for your turn!", ephemeral=True, delete_after=5)
            return
        if self.game.round_bet > self.game.players[self.on_turn_id].round_bet:
            await PokerCmdHandler.cmd_call(self.game, interaction, ["call"])
            self.value = PokerPlayerState.CALLED
        else:
            await PokerCmdHandler.cmd_check(self.game, interaction, ["check"])
            self.value = PokerPlayerState.CHECKED
        self.stop()

    @discord.ui.button(label="RAISE", style=discord.ButtonStyle.green, row=0)
    async def handle_raise(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if interaction.user.id != self.on_turn_id:
                await interaction.response.send_message(f"{interaction.user.mention} Please wait for your turn!", ephemeral=True, delete_after=5)
                return
            if self.game.players[interaction.user.id].bet.value <= self.game.round_bet:
                await interaction.response.send_message(f"You don't have enough in your bank to RAISE")
                return
            modal = RaiseModal(self.game, interaction.user.id)
            await interaction.response.send_modal(modal)
            await modal.wait()
            if (self.game.players[interaction.user.id].state != PokerPlayerState.RAISED and self.game.players[interaction.user.id].state != PokerPlayerState.ALL_IN_RAISED):
                return
            self.value = PokerPlayerState.RAISED
            self.stop()
        except:
            traceback.print_exc()

    @discord.ui.button(label="FOLD", style=discord.ButtonStyle.red, row=0)
    async def handle_fold(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.on_turn_id:
            await interaction.response.send_message(f"{interaction.user.mention} Please wait for your turn!", ephemeral=True, delete_after=5)
            return
        await PokerCmdHandler.cmd_fold(self.game, interaction, ["fold"])
        self.value = PokerPlayerState.FOLDED
        self.stop()

    @discord.ui.button(label="CARDS", style=discord.ButtonStyle.grey, row=0)
    async def handle_cards(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await PokerCmdHandler.cmd_show_cards(self.game, interaction, ["fold"])
        except:
            traceback.print_exc()

class RaiseModal(discord.ui.Modal, title="Place Your Bet"):
    def __init__(self, game: Poker, author_id: int):
        super().__init__()
        self.game = game
        self.author_id = author_id
        self.hint_message = f"e. g. 100 ({game.round_bet + 1} - {self.game.players[author_id].bet.value})"
        self.max_length = int(log10(max(1,self.game.players[author_id].bet.value))) + 1

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