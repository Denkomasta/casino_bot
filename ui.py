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
import global_vars

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
                    if game.type == GameType.POKER:
                        from poker.poker import Poker
                        assert(isinstance(game, Poker))
                        item.label = f"JOIN A GAME OF {GameType(type).name}" + ("" if game.preset_bank is None else f" (BANK {game.preset_bank})")
                        if not game.joinable and not game.first_round:
                            item.disabled = True
                    else:
                        item.label = f"JOIN A GAME OF {GameType(type).name}"

    @discord.ui.button(label="JOIN", style=discord.ButtonStyle.blurple)
    async def handle_join(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await CommandHandler.cmd_join(self.game, interaction, ["join"])
            #await interaction.response.send_message(view=bet_ui, ephemeral=True)
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
        self.is_clicked = False
        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.label == "START":
                item.label = f"START THE GAME OF {GameType(game.type).name}"

    @discord.ui.button(label="START", style=discord.ButtonStyle.blurple)
    async def handle_ready(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.is_clicked:
            await interaction.response.send_message("Button was already clicked", ephemeral=True, delete_after=2)
        self.is_clicked = True
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
                    if not await PokerCmdHandler.check_blinds(self.game):
                        await interaction.response.send_message("These don't have enough for blinds", delete_after=1)
                    await interaction.response.send_message("Game started succesfully", delete_after=0)
                    await PokerCmdHandler.cmd_start(self.game, interaction, ["start"])
                except:
                    traceback.print_exc()
        await interaction.response.send_message("Game started succesfully", delete_after=0)

class GeneralCommandsUI(discord.ui.View):
    def __init__(self):
        super().__init__()

class GeneralCreateUI(GeneralCommandsUI):
    def __init__(self, options):
        super().__init__()
            
        select = discord.ui.Select(
                options=options,
                placeholder="Choose game to create"
            )
        
        async def select_callback( interaction: discord.Interaction):
            type = int(select.values[0])  # Get the selected value
            await CommandHandler.cmd_create(interaction, GameType(type))
            await interaction.response.send_message(f"You created a game of {GameType(type).name}", delete_after=1)

        select.callback = select_callback
        self.add_item(select)


class GeneralJoinUI(GeneralCommandsUI):
    def __init__(self, options):
        super().__init__()

        select = discord.ui.Select(
                options=options,
                placeholder="Choose game you want to join"
            )

        async def select_callback(interaction: discord.Interaction):
            type = int(select.values[0])  # Get the selected value
            await CommandHandler.cmd_join(global_vars.Games[(interaction.channel.id, type)], interaction, ["join"])
            #await interaction.response.send_message(view=JoinUI(games[(interaction.channel.id, GameType(type))], GameType(type)))
        
        select.callback = select_callback
        self.add_item(select)


class GeneralLeaveUI(GeneralCommandsUI):
    def __init__(self, options):
        super().__init__()

        select = discord.ui.Select(
                options=options,
                placeholder="Choose game you want to leave"
            )

        async def select_callback(interaction: discord.Interaction):
            type = int(select.values[0])  # Get the selected value
            await CommandHandler.cmd_leave(global_vars.Games[(interaction.channel.id, type)], interaction, ["join"])
            #await interaction.response.send_message(view=JoinUI(games[(interaction.channel.id, GameType(type))], GameType(type)))
        
        select.callback = select_callback
        self.add_item(select)


class GeneralPlayUI(GeneralCommandsUI):
    def __init__(self):
        super().__init__()

        select = discord.ui.Select(
                options=[discord.SelectOption(label=GameType(type).name, value=f"{type}") for type in GameType],
                placeholder="Choose game you want to play"
            )
        
        async def select_callback(interaction: discord.Interaction):
            type = int(select.values[0])  # Get the selected value
            if ((interaction.channel.id, type) not in global_vars.Games.keys()):
                await CommandHandler.cmd_create(interaction, GameType(type))
            await CommandHandler.cmd_join(global_vars.Games[(interaction.channel.id, type)], interaction, ["join"])

        
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


class ControlsUI(discord.ui.View):

    def __init__(self, source):
        super().__init__()

        for channel_id, type in global_vars.Games.keys():
            if channel_id == source.channel.id:
                button = discord.ui.Button(
                    label=f"{GameType(type).name}",
                    style=discord.ButtonStyle.blurple,
                    row=3,
                    custom_id=f"{GameType(type)}"
                )
                button.callback = lambda i, b=button: self.game_controls(i, b)
                self.add_item(button)

    async def game_controls(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_message(view=GameControlsUI(GameType(int(button.custom_id))))

        

    @discord.ui.button(label="PLAY", style=discord.ButtonStyle.blurple, row=1)
    async def handle_play(self, interaction: discord.Interaction, button: discord.ui.Button):
        await CommandHandler.play(interaction)

    @discord.ui.button(label="CREATE", style=discord.ButtonStyle.blurple, row=1)
    async def handle_create(self, interaction: discord.Interaction, button: discord.ui.Button):
        await CommandHandler.create(interaction)

    @discord.ui.button(label="JOIN", style=discord.ButtonStyle.blurple, row=1)
    async def handle_join(self, interaction: discord.Interaction, button: discord.ui.Button):
        await CommandHandler.join(interaction)

    @discord.ui.button(label="LEAVE", style=discord.ButtonStyle.red, row=1)
    async def handle_leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        await CommandHandler.leave(interaction)

    @discord.ui.button(label="BALANCE", style=discord.ButtonStyle.grey, row=2)
    async def handle_balance(self, interaction: discord.Interaction, button: discord.ui.Button):
        await CommandHandler.balance(interaction)

    @discord.ui.button(label="DROP", style=discord.ButtonStyle.green, row=2)
    async def handle_drop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await CommandHandler.drop(interaction)
    
    @discord.ui.button(label="LEADERBOARD", style=discord.ButtonStyle.grey, row=2)
    async def handle_leaderboard(self, interaction: discord.Interaction, button: discord.ui.Button):
        await CommandHandler.leaderboard(interaction)
    

class GameControlsUI(discord.ui.View):

    def __init__(self, type):
        super().__init__()
        self.type = type

        options = []
        options.append(discord.SelectOption(label="JOIN/LEAVE", value="JOIN/LEAVE"))
        options.append(discord.SelectOption(label="GENERAL CONTROLS", value="GENERAL"))
        match type:
            case GameType.BLACKJACK:
                options.append(discord.SelectOption(label="HIT/STAND", value="HIT/STAND"))
        select = discord.ui.Select(
                options=options,
                placeholder="Choose controls you need"
            )
        
        async def select_callback(interaction: discord.Interaction):
            view = None
            match select.values[0]:
                case "JOIN/LEAVE":
                    view = JoinLeaveUI(global_vars.Games[(interaction.channel.id, self.type)], self.type)
                case "GENERAL":
                    view = CommandHandler.get_game_ui(global_vars.Games[(interaction.channel.id, self.type)])
                case "HIT/STAND":
                    from blackjack.ui_blackjack import BlackJackHitStandUI
                    view = BlackJackHitStandUI(global_vars.Games[(interaction.channel.id, self.type)])
            await interaction.response.send_message(view=view, ephemeral=True)                    
                
        select.callback = select_callback
        self.add_item(select)
        
    
