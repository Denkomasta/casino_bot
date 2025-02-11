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
                        if (not game.banks_changeable and not game.first_round) or game.preset_bank is not None:
                            item.disabled = True
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
    
    @discord.ui.button(label="MY BANK", style=discord.ButtonStyle.grey, row=0)
    async def handle_bank(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await PokerCmdHandler.cmd_bank(self.game, interaction, ["bank"])
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

class PokerSettingsUI(UI):
    def __init__(self, game: Poker):
        super().__init__(game)

    @discord.ui.select(
        placeholder="Choose if new players can join between rounds",
        options=[
            discord.SelectOption(label="Players CAN join between rounds (default)", value=f"true", default=True),
            discord.SelectOption(label="Players can join before the FIRST round ONLY", value=f"false"),
        ],
        row=0
    )
    async def handle_joinable(self, interaction: discord.Interaction, select: discord.ui.Select):
        if select.values[0] is None:
            interaction.response.send_message(f"{interaction.user.mention} Please choose an option!", ephemeral=True, delete_after=5)
            return
        assert(isinstance(self.game, Poker))
        self.game.joinable = True if select.values[0] == "true" else False
        message = "" if self.game.joinable else "not"
        await interaction.response.send_message(f"You set the game to be {message} joinable between rounds", ephemeral=True, delete_after=5)

    @discord.ui.select(
        placeholder="Choose if players can change their banks between rounds",
        options=[
            discord.SelectOption(label="Players CAN change their banks between rounds (default)", value=f"true", default=True),
            discord.SelectOption(label="Players CANNOT change their banks once they join", value=f"false"),
        ],
        row=1
    )
    async def handle_changeable(self, interaction: discord.Interaction, select: discord.ui.Select):
        if select.values[0] is None:
            interaction.response.send_message(f"{interaction.user.mention} Please choose an option!", ephemeral=True, delete_after=5)
            return
        assert(isinstance(self.game, Poker))
        self.game.banks_changeable = True if select.values[0] == "true" else False
        message = "" if self.game.joinable else "not"
        await interaction.response.send_message(f"You set that the players can {message} change their banks between rounds", ephemeral=True, delete_after=5)

    @discord.ui.button(label="BLIND AND BANK SETTINGS", style=discord.ButtonStyle.blurple, row=2)
    async def handle_money_settings(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.send_modal(PokerSettingsModal(self.game))
    
    @discord.ui.button(label="ALL SET! 🚀", style=discord.ButtonStyle.blurple, row=3)
    async def handle_all_set(self, interaction: discord.Interaction, select: discord.ui.Select):
        assert(isinstance(self.game, Poker))
        message = f"User {interaction.user.display_name} created a game of Poker!\n" + 25 * '-' + '\n'
        message += "Players are " + ("NOT " if not self.game.joinable else "") + "able to join this game after the first round\n"
        message += "Players are " + ("NOT " if not self.game.banks_changeable else "") + "able to change their banks after the first round\n"
        message += f"FIRST BIG BLIND: {self.game.blind}\n"
        message += f"BLIND INCREASE: {self.game.blind_increase}\n"
        message += "MANDATORY BANK: " + ("NOT SET" if self.game.preset_bank is None else f"{self.game.preset_bank}") + '\n'
        await interaction.response.send_message(f"```{message}```")
        self.stop()

class PokerSettingsModal(discord.ui.Modal, title="Change your Poker experience!"):
    def __init__(self, game):
        try:
            super().__init__()
            self.game = game

            self.blind_input = discord.ui.TextInput(
                label = "Select first big blind",
                placeholder = "e.g. 20",
                default="20",
                required=True,
                min_length=1
            )
            self.add_item(self.blind_input)

            self.increase_input = discord.ui.TextInput(
                label = "Select how will the big blind increase",
                placeholder = "e.g. 10",
                default="10",
                required=True,
                min_length=1
            )
            self.add_item(self.increase_input)

            self.preset_bank_input = discord.ui.TextInput(
                label = "Select a set bank for players (optional)",
                placeholder = "e.g. 1000",
                default="",
                required=False,
                min_length=1
            )
            self.add_item(self.preset_bank_input)
        except:
            traceback.print_exc()

    async def on_submit(self, interaction: discord.Interaction):
        try:
            start_blind = int(self.blind_input.value)
            increase = int(self.increase_input.value)
            if self.preset_bank_input.value != "":
                preset_bank = int(self.preset_bank_input.value)
            else:
                preset_bank = None
        except ValueError:
            await interaction.response.send_message(f"{interaction.user.mention} All inputs must be numbers only!", ephemeral=True, delete_after=5)
            return
        assert(isinstance(self.game, Poker)) # Needed for highlighting
        if start_blind >= preset_bank:
            await interaction.response.send_message(f"{interaction.user.mention} Mandatory bank must be HIGHER than starting blind!", ephemeral=True, delete_after=5)
            return
        self.game.blind = start_blind
        self.game.blind_increase = increase
        self.game.preset_bank = preset_bank if preset_bank is not None else None
        await interaction.response.send_message(f"You set the starting blind to {self.game.blind}, the blind inrease to {self.game.blind_increase} and the mandatory bank to {self.game.preset_bank}!", ephemeral=True, delete_after=5)