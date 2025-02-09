import discord
import traceback
from discord.ext import commands
from base_classes import Game, Player, Bet
from enums import BaccaratBetType, GameType, E, GameState, PlayerState
from baccarat.baccarat import BaccaratPlayer, BaccaratBet
from cmd_handler import CommandHandler
from blackjack.cmd_handler_blackjack import BlackJackCmdHandler
from baccarat.cmd_handler_baccarat import BaccaratCmdHandler
from rng_games.cmd_handler_rng import CoinflipCmdHandler, RollTheDiceCmdHandler, GuessNumberCmdHandler
from rng_games.rng_games import Coinflip, RollTheDice, RNGGame
from poker.cmd_handler_poker import PokerCmdHandler
from database import Database
from abc import ABC

class UI(discord.ui.View):
    game: Game

    def __init__(self, game: Game):
        super().__init__()
        self.game = game

class JoinUI(UI):

    def __init__(self, game: Game, type: GameType):
            super().__init__(game)
            self.type = type
            for item in self.children:
                if isinstance(item, discord.ui.Button) and item.label == "JOIN":
                    item.label = f"JOIN A GAME OF {GameType(type).name}"

    @discord.ui.button(label="JOIN", style=discord.ButtonStyle.blurple)
    async def handle_join(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            bet_ui: GameUserInterface
            match self.type:
                case GameType.BACCARAT:
                    from baccarat.ui_baccarat import BaccaratBetUI
                    bet_ui = BaccaratBetUI(self.game)
                case GameType.COINFLIP:
                    from rng_games.ui_rng import CoinflipUserInterface
                    bet_ui = CoinflipUserInterface(self.game)
                case GameType.ROLLTHEDICE:
                    from rng_games.ui_rng import RollTheDiceUserInterface
                    bet_ui = RollTheDiceUserInterface(self.game)
                case GameType.GUESSNUMBER:
                    from rng_games.ui_rng import GuessNumberUserInterface
                    bet_ui = GuessNumberUserInterface(self.game)
                case GameType.POKER:
                    from poker.ui_poker import PokerBetUI
                    bet_ui = PokerBetUI(self.game)
                case _:
                    bet_ui = BetUI(self.game)
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
        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.label == "START":
                item.label = f"START THE GAME OF {GameType(game.type).name}"

    @discord.ui.button(label="START", style=discord.ButtonStyle.blurple)
    async def handle_ready(self, interaction: discord.Interaction, button: discord.ui.Button):
        match self.game.type:
            case GameType.BACCARAT:
                await BaccaratCmdHandler.cmd_start(self.game, interaction, ["start"])
            case GameType.BLACKJACK:
                await BlackJackCmdHandler.cmd_start(self.game, interaction, ["start"])
            case GameType.COINFLIP:
                await self.game.channel.send("All players are ready! Rolling!")
                await CoinflipCmdHandler.subcommand_roll(self.game, interaction, ["start"])
            case GameType.ROLLTHEDICE:
                await self.game.channel.send("All players are ready! Rolling!")
                await RollTheDiceCmdHandler.subcommand_roll(self.game, interaction, ["start"])
            case GameType.GUESSNUMBER:
                await self.game.channel.send("All players are ready! Evaluating!")
                await GuessNumberCmdHandler.subcommand_roll(self.game, interaction, ["start"])
            case GameType.POKER:
                await self.game.channel.send("All players are ready! The game starts!")
                try:
                    await PokerCmdHandler.cmd_start(self.game, interaction, ["start"])
                except:
                    traceback.print_exc()
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
        
class GameUserInterface(UI, ABC):
    def __init__(self, game: Game):
        super().__init__(game)

    @discord.ui.button(label="READY", style=discord.ButtonStyle.green, row=2)
    async def handle_ready(self, interaction: discord.Interaction, button: discord.ui.Button):
        assert(isinstance(self.game, Game)) # Needed for highlighting
        if not self.game.check_valid_player(interaction.user):
            await interaction.response.send_message(f"{interaction.user.mention} You need to join the game first to place bets!", ephemeral=True, delete_after=10)
            return
        await CommandHandler.cmd_ready(self.game, interaction, ["ready"])
       
    @discord.ui.button(label="NOT READY", style=discord.ButtonStyle.red, row=2)
    async def handle_unready(self, interaction: discord.Interaction, button: discord.ui.Button):
        assert(isinstance(self.game, Game)) # Needed for highlighting
        if not self.game.check_valid_player(interaction.user):
            await interaction.response.send_message(f"{interaction.user.mention} You need to join the game first to place bets!", ephemeral=True, delete_after=10)
            return
        await CommandHandler.cmd_unready(self.game, interaction, ["ready"])


    @discord.ui.button(label="STATUS", style=discord.ButtonStyle.gray, row=3)
    async def handle_betlist(self, interaction: discord.Interaction, button: discord.ui.Button):
        assert(isinstance(self.game, Game)) # Needed for highlighting
        if not self.game.check_valid_player(interaction.user):
            await interaction.response.send_message(f"{interaction.user.mention} You need to join the game first to place bets!", ephemeral=True, delete_after=10)
            return
        match self.game.type:
            case GameType.COINFLIP:
                await CoinflipCmdHandler.command_status(self.game, interaction, ["status"])
            case GameType.ROLLTHEDICE:
                await RollTheDiceCmdHandler.command_status(self.game, interaction, ["status"])
            case GameType.BLACKJACK:
                await BlackJackCmdHandler.cmd_status(self.game, interaction, ["status"])
            case GameType.BACCARAT:
                await BaccaratCmdHandler.cmd_status(self.game, interaction, ["status"])
            case GameType.GUESSNUMBER:
                await GuessNumberCmdHandler.command_status(self.game, interaction, ["status"])
            case GameType.POKER:
                await PokerCmdHandler.cmd_status(self.game, interaction, ["status"])
            case _:
                await interaction.response.send_message("Not implemented yet", ephemeral=True)

    @discord.ui.button(label="BET LIST", style=discord.ButtonStyle.gray, row=3)
    async def handle_bestlist(self, interaction: discord.Interaction, button: discord.ui.Button):
        assert(isinstance(self.game, Game)) # Needed for highlighting
        if not self.game.check_valid_player(interaction.user):
            await interaction.response.send_message(f"{interaction.user.mention} You need to join the game first to place bets!", ephemeral=True, delete_after=10)
            return
        match self.game.type:
            case GameType.COINFLIP:
                await CoinflipCmdHandler.command_betlist(self.game, interaction, ["betlist"])
            case GameType.ROLLTHEDICE:
                await RollTheDiceCmdHandler.command_betlist(self.game, interaction, ["betlist"])
            case GameType.BACCARAT:
                await BaccaratCmdHandler.cmd_betlist(self.game, interaction, ["betlist"])
            case GameType.BLACKJACK:
                await BlackJackCmdHandler.cmd_betlist(self.game, interaction, ["betlist"])
            case GameType.GUESSNUMBER:
                await GuessNumberCmdHandler.command_betlist(self.game, interaction, ["betlist"])
            case GameType.POKER:
                await PokerCmdHandler.cmd_bank(self.game, interaction, ["banklist"])
            case _:
                await interaction.response.send_message("Not implemented yet", ephemeral=True)

class BetUI(GameUserInterface):
    def __init__(self, game: Game):
        super().__init__(game)

    @discord.ui.button(label="SET BET AMOUNT", style=discord.ButtonStyle.blurple, row=1)
    async def handle_bet_amount(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BetModal(self.game))
    

class BetModal(discord.ui.Modal, title="Place Your Bet"):

    def __init__(self, game: Game):
        super().__init__(title="Place your bet")
        self.game = game

        self.bet_amount: discord.ui.TextInput = discord.ui.TextInput(
            label=f"Enter your bet amount",
            placeholder="e.g. 100",
            required=True
        )
        self.add_item(self.bet_amount)

    async def on_submit(self, interaction: discord.Interaction):
        await CommandHandler.cmd_bet(self.game, interaction, ["join", self.bet_amount.value])