import discord
import traceback
from discord.ext import commands
from base_classes import Game, Player, Bet
from enums import BaccaratBetType, GameType, E, GameState, PlayerState
from baccarat.baccarat import BaccaratPlayer, BaccaratBet
from cmd_handler import CommandHandler
from blackjack.cmd_handler_blackjack import BlackJackCmdHandler
from baccarat.cmd_handler_baccarat import BaccaratCmdHandler
from database import Database

class UI(discord.ui.View):
    game: Game

    def __init__(self, game: Game):
        super().__init__()
        self.game = game

class JoinUI(UI):

    def __init__(self, game: Game, type: GameType):
            super().__init__(game)
            self.type = type


    @discord.ui.button(label="JOIN", style=discord.ButtonStyle.blurple)
    async def handle_join(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            bet_ui: BetUI
            match self.type:
                case GameType.BACCARAT:
                    from baccarat.ui_baccarat import BaccaratBetUI
                    bet_ui = BaccaratBetUI(self.game, True)
                case _:
                    bet_ui = BetUI(self.game, True)
            await CommandHandler.cmd_join(self.game, interaction, ["join"])
            await interaction.response.send_message(view=bet_ui, ephemeral=True)
        except Exception as e:
            print("Exception:", e)
            traceback.print_exc()

class JoinLeaveUI(JoinUI):
    def __init__(self, game: Game, type: GameType):
            super().__init__(game, type)

    @discord.ui.button(label="LEAVE", style=discord.ButtonStyle.blurple)
    async def handle_leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        match self.type:
            case _:
                await CommandHandler.cmd_leave(self.game, interaction, ["leave"])

class ReadyUI(UI):
    def __init__(self, game: Game):
        super().__init__(game)


    @discord.ui.button(label="READY", style=discord.ButtonStyle.green)
    async def handle_ready(self, interaction: discord.Interaction, button: discord.ui.Button):
        await BaccaratCmdHandler.cmd_ready(self.game, interaction, ["ready"])

    @discord.ui.button(label="UNREADY", style=discord.ButtonStyle.red)
    async def handle_unready(self, interaction: discord.Interaction, button: discord.ui.Button):
        await BaccaratCmdHandler.cmd_unready(self.game, interaction, ["unready"])


class StartUI(UI):
        
    def __init__(self, game: Game):
        super().__init__(game)


    @discord.ui.button(label="START", style=discord.ButtonStyle.blurple)
    async def handle_ready(self, interaction: discord.Interaction, button: discord.ui.Button):
        match self.game.type:
            case GameType.BACCARAT:
                await BaccaratCmdHandler.cmd_start(self.game, interaction, ["start"])
            case GameType.BLACKJACK:
                await BlackJackCmdHandler.cmd_start(self.game, interaction, ["start"])
        await interaction.response.send_message("Game started succesfully", delete_after=0)

class CreateUI(discord.ui.View):
    def __init__(self, games: dict[(int, int), Game], data: Database, options=[], channel_id=0):
        super().__init__()
        self.games = games
        self.data = data

        if len(options) == 0:
            options = [discord.SelectOption(label=GameType(type).name, value=f"{type}") for type in GameType if (channel_id, type) not in games.keys()]
            
        select: discord.ui.Select = discord.ui.Select(
                options=options,
                placeholder="Choose game to create"
            )
        
        async def select_callback( interaction: discord.Interaction):
            type = int(select.values[0])  # Get the selected value
            await CommandHandler.cmd_create(interaction, self.games, self.data, type)

        select.callback = select_callback
        self.add_item(select)


class PlayUI(discord.ui.View):
    def __init__(self, games: dict[tuple[int, int], Game], options=[], channel_id=0):
        super().__init__()
        self.games = games

        if len(options) == 0:
            options = [discord.SelectOption(label=GameType(type).name, value=f"{type}") for id, type in games.keys() if id == channel_id]
        
        select: discord.ui.Select = discord.ui.Select(
                options=options,
                placeholder="Choose game you want to play"
            )
        

        async def select_callback(interaction: discord.Interaction):
            try:
                type = int(select.values[0])  # Get the selected value
                await interaction.response.send_message(view=JoinUI(self.games[(interaction.channel.id, type)], GameType(type)), ephemeral=True)
            except Exception as e:
                traceback.print_exc()
        
        select.callback = select_callback
        self.add_item(select)

class BetUI(UI):

    def __init__(self, game: Game, is_new: bool):
        super().__init__(game)
        self.is_new = is_new

    @discord.ui.button(label="SET BET AMOUNT", style=discord.ButtonStyle.blurple)
    async def handle_bet_amount(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BetModal(self.game, self.is_new))
    

class BetModal(discord.ui.Modal, title="Place Your Bet"):

    def __init__(self, game: Game, is_new: bool):
        super().__init__(title="Place your bet")
        self.game = game
        self.is_new = is_new

        self.bet_amount: discord.ui.TextInput = discord.ui.TextInput(
            label=f"Enter your bet amount",
            placeholder="e.g. 100",
            required=True
        )
        self.add_item(self.bet_amount)

    async def on_submit(self, interaction: discord.Interaction):
        if self.is_new:
            await interaction.response.send_message(view=ReadyUI(self.game), ephemeral=True)
        await CommandHandler.cmd_bet(self.game, interaction, ["join", self.bet_amount.value])
        
