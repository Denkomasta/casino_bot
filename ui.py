import discord
import traceback
from discord.ext import commands
from base_classes import Game, Player, Bet
from enums import BaccaratBetType, GameType, E, GameState, PlayerState
from baccarat import BaccaratPlayer, BaccaratBet
from cmd_handler import BaccaratCmdHandler, CommandHandler, BlackJackCmdHandler

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
        bet_ui: BetUI
        match self.type:
            case GameType.BACCARAT:
                bet_ui = BaccaratBetUI(self.game)
            case _:
                bet_ui = BetUI(self.game)
        await interaction.response.send_message(view=bet_ui, ephemeral=True)

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
        await interaction.response.send_message("Game started succesfully", delete_after=1)

class BetUI(UI):

    def __init__(self, game: Game):
        super().__init__(game)

    @discord.ui.button(label="SET BET AMOUNT", style=discord.ButtonStyle.blurple)
    async def handle_bet_amount(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BetModal(self.game))
        

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
        if interaction.user.id not in self.game.players.keys():
            await CommandHandler.cmd_join(self.game, interaction, ["join", self.bet_amount.value])
            await interaction.response.send_message(view=ReadyUI(self.game), ephemeral=True)
        else:
            await CommandHandler.cmd_bet(self.game, interaction, ["join", self.bet_amount.value])



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
