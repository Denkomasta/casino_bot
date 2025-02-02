import discord
from discord.ext import commands
from base_classes import Game
from ui import UI, BetModal, ReadyUI, GameUserInterface
from rng_games.cmd_handler_rng import CoinflipCmdHandler, RollTheDiceCmdHandler
from rng_games.rng_games import Coinflip, RollTheDice, RNGGame
from abc import ABC
from enums import GameType
import traceback

class RNGUserInterface(UI, ABC):
    def __init__(self, game: Coinflip):
        super().__init__(game)
        self.bet_type: str | None = None

    @discord.ui.button(label="READY", style=discord.ButtonStyle.green, row=2)
    async def handle_ready(self, interaction: discord.Interaction, button: discord.ui.Button):
        assert(isinstance(self.game, RNGGame)) # Needed for highlighting
        if not self.game.check_valid_player(interaction.user):
            await interaction.response.send_message(f"{interaction.user.mention} You need to join the game first to place bets!", ephemeral=True, delete_after=10)
            return
        match self.game.type:
            case GameType.COINFLIP:
                await CoinflipCmdHandler.command_ready(self.game, interaction, ["ready"])
            case GameType.ROLLTHEDICE:
                await RollTheDiceCmdHandler.command_ready(self.game, interaction, ["ready"])

    @discord.ui.button(label="NOT READY", style=discord.ButtonStyle.red, row=2)
    async def handle_unready(self, interaction: discord.Interaction, button: discord.ui.Button):
        assert(isinstance(self.game, RNGGame)) # Needed for highlighting
        if not self.game.check_valid_player(interaction.user):
            await interaction.response.send_message(f"{interaction.user.mention} You need to join the game first to place bets!", ephemeral=True, delete_after=10)
            return
        match self.game.type:
            case GameType.COINFLIP:
                await CoinflipCmdHandler.command_unready(self.game, interaction, ["unready"])
            case GameType.ROLLTHEDICE:
                await RollTheDiceCmdHandler.command_unready(self.game, interaction, ["unready"])

    @discord.ui.button(label="STATUS", style=discord.ButtonStyle.gray, row=3)
    async def handle_betlist(self, interaction: discord.Interaction, button: discord.ui.Button):
        assert(isinstance(self.game, RNGGame)) # Needed for highlighting
        if not self.game.check_valid_player(interaction.user):
            await interaction.response.send_message(f"{interaction.user.mention} You need to join the game first to place bets!", ephemeral=True, delete_after=10)
            return
        match self.game.type:
            case GameType.COINFLIP:
                await CoinflipCmdHandler.command_status(self.game, interaction, ["status"])
            case GameType.ROLLTHEDICE:
                await RollTheDiceCmdHandler.command_status(self.game, interaction, ["status"])

    @discord.ui.button(label="BET LIST", style=discord.ButtonStyle.gray, row=3)
    async def handle_bestlist(self, interaction: discord.Interaction, button: discord.ui.Button):
        assert(isinstance(self.game, RNGGame)) # Needed for highlighting
        if not self.game.check_valid_player(interaction.user):
            await interaction.response.send_message(f"{interaction.user.mention} You need to join the game first to place bets!", ephemeral=True, delete_after=10)
            return
        match self.game.type:
            case GameType.COINFLIP:
                await CoinflipCmdHandler.command_betlist(self.game, interaction, ["betlist"])
            case GameType.ROLLTHEDICE:
                await RollTheDiceCmdHandler.command_betlist(self.game, interaction, ["betlist"])

class CoinflipUserInterface(GameUserInterface):
    def __init__(self, game: Game):
        super().__init__(game)
        self.bet_type = None

    @discord.ui.select(
        placeholder="Choose an option to bet on...",
        options=[
            discord.SelectOption(label="Heads", value=f"heads"),
            discord.SelectOption(label="Tails", value=f"tails"),
        ],
        row=0
    )
    async def handle_bet_type(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.bet_type = select.values[0]
        assert(isinstance(self.game, Coinflip)) # Needed for highlighting
        if not self.game.check_valid_player(interaction.user):
            await interaction.response.send_message(f"{interaction.user.mention} You need to join the game first to place bets!", ephemeral=True, delete_after=10)
            return
        await interaction.response.send_message(f"You decided to place your bet on {self.bet_type}! Use the \"SET BET AMOUNT\" interface to set a value and confirm your bet!", ephemeral=True, delete_after=5)
    
    @discord.ui.button(label="SET BET AMOUNT", style=discord.ButtonStyle.blurple, row=1)
    async def handle_bet_amount(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.bet_type is None:
            await interaction.response.send_message(f"Choose an option to bet on!", ephemeral=True, delete_after=5)
            return
        await interaction.response.send_modal(CoinflipBetModal(self.game, self.bet_type))

class RollTheDiceUserInterface(GameUserInterface):
    def __init__(self, game: Game):
        super().__init__(game)
        self.bet_type = None
    
    @discord.ui.select(
        placeholder="Choose an option to bet on...",
        options=[
            discord.SelectOption(label="Sum of dice", value=f"sum"),
            discord.SelectOption(label="Doubles", value=f"doubles"),
        ],
        row=0
    )
    async def handle_bet_type(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.bet_type = select.values[0]
        assert(isinstance(self.game, RollTheDice)) # Needed for highlighting
        if not self.game.check_valid_player(interaction.user):
            await interaction.response.send_message(f"{interaction.user.mention} You need to join the game first to place bets!", ephemeral=True, delete_after=10)
            return
        await interaction.response.send_message(f"You decided to place your bet on {self.bet_type}! Use the \"SET BET AMOUNT\" interface to set a value and confirm your bet!", ephemeral=True, delete_after=5)
    
    @discord.ui.button(label="SET BET AMOUNT", style=discord.ButtonStyle.blurple, row=1)
    async def handle_bet_amount(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if self.bet_type is None:
                await interaction.response.send_message(f"Choose an option to bet on!", ephemeral=True, delete_after=5)
                return
            await interaction.response.send_modal(RTDBetModal(self.game, self.bet_type))
        except Exception as e:
            traceback.print_exc()


class CoinflipBetModal(BetModal):

    def __init__(self, game: Game, type: str):
        super().__init__(game)
        self.bet_type = type
    
    async def on_submit(self, interaction: discord.Interaction):
        await CoinflipCmdHandler.command_bet(self.game, interaction, ["bet", self.bet_type, self.bet_amount.value])

class RTDBetModal(discord.ui.Modal, title="Place your bet"):
    def __init__(self, game, type):
        super().__init__()
        self.game = game
        self.bet_type = type
        self.hint_message = "Place your bet on " + ("DOUBLES" if self.bet_type == "doubles" else "SUM OF DICE")
        self.hint_placeholder = "Enter number between " + ("1 and 6" if self.bet_type == "doubles" else "2 and 12")
        self.max_length = (1 if self.bet_type == "doubles" else 2)

        self.number_input = discord.ui.TextInput(
            label=self.hint_message,
            placeholder=self.hint_placeholder,
            required=True,
            min_length=1,
            max_length=self.max_length
        )
        self.add_item(self.number_input)

        self.amount_input = discord.ui.TextInput(
            label="Enter your bet amount:",
            placeholder="e.g. 100",
            required=True,
            min_length=1,
        )
        self.add_item(self.amount_input)

    async def on_submit(self, interaction: discord.Interaction):
        await RollTheDiceCmdHandler.command_bet(self.game, interaction, ["bet", self.bet_type, self.number_input.value, self.amount_input.value])