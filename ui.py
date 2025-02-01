import discord
import traceback
from discord.ext import commands
from base_classes import Game, Player, Bet
from enums import BaccaratBetType, GameType, E, GameState, PlayerState
from baccarat import BaccaratPlayer, BaccaratBet

class UI(discord.ui.View):
    game: Game

    def __init__(self, game: Game):
        super().__init__()
        self.game = game

class JoinUI(UI):

    def __init__(self, game: Game, type: GameType):
            super().__init__(game)
            self.type = type


    @discord.ui.button(label="Join!", style=discord.ButtonStyle.green)
    async def handle_bet(self, interaction: discord.Interaction, button: discord.ui.Button):
        bet_ui: BetUI
        match self.type:
            case GameType.BACCARAT:
                bet_ui = BaccaratBetUI(self.game)
        try:
            await interaction.response.send_message(view=bet_ui, ephemeral=True)
        except Exception as e:
            print(e)


class ReadyUI(UI):
    def __init__(self, game: Game):
        super().__init__(game)


    @discord.ui.button(label="READY", style=discord.ButtonStyle.green)
    async def handle_ready(self, interaction: discord.Interaction, button: discord.ui.Button):
        if (self.game.state == GameState.RUNNING):
            await interaction.response.send_message(f"Game is already running", ephemeral=True)
            return
        self.game.players[interaction.user.id].state = PlayerState.READY
        await interaction.response.send_message(f"You are READY", ephemeral=True)
        if (self.game.are_players_ready()):
            print("col start")
            self.game.collect_bets()
            print("game start")
            self.game.game_start()
            print("eval start")
            self.game.evaluate_bets()
            print("give start")
            self.game.give_winnings()
            print("write start")
            try:
                await interaction.response.send_message(f"```\n{self.game.show_game()}\n{self.game.show_results()}```", ephemeral=True)
            except Exception as e:
                print("Exception:", e)
                traceback.print_exc()
            print("re start")
            self.game.round_restart()

    @discord.ui.button(label="UNREADY", style=discord.ButtonStyle.red)
    async def handle_unready(self, interaction: discord.Interaction, button: discord.ui.Button):
        if (self.game.state == GameState.RUNNING):
            await interaction.response.send_message(f"Game is already running", ephemeral=True)
            return
        self.game.players[interaction.user.id].state = PlayerState.NOT_READY
        await interaction.response.send_message(f"You are UNREADY", ephemeral=True)

        
class BetUI(UI):

    def __init__(self, game: Game):
        super().__init__(game)
        

class BaccaratBetUI(BetUI):

    def __init__(self, game: Game):
        super().__init__(game)
        self.bet_type: int | None = None
        
    @discord.ui.select(
        placeholder="Choose your bet type...",
        options=[
            discord.SelectOption(label="Player", value=f"{BaccaratBetType.PLAYER}"),
            discord.SelectOption(label="Banker", value=f"{BaccaratBetType.BANKER}"),
            discord.SelectOption(label="Tie", value=f"{BaccaratBetType.TIE}"),
        ],
    )
    async def handle_bet_type(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.bet_type = int(select.values[0])
        await interaction.response.send_message("Selected succesfully", ephemeral=True)

    
    @discord.ui.button(label="Set bet!", style=discord.ButtonStyle.blurple)
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
        player_balance = self.game.data.get_player_balance(interaction.user.id)
        try:
            int_bet_amount = int(self.bet_amount.value)
        except ValueError:
            await interaction.response.send_message(f"Enter a number to the amount", ephemeral=True)
        if int_bet_amount > player_balance:
            await interaction.response.send_message(f"You don't have enough balance to place that bet. Your balance is {player_balance}", ephemeral=True)
            return
        if self.game.add_player(interaction.user, int_bet_amount) != E.SUCCESS:
            await interaction.response.send_message(f"{interaction.user.name} add failed!")
            return
        await interaction.response.send_message(view=ReadyUI(self.game), ephemeral=True)
        await interaction.response.send_message(f"{interaction.user.name} joined the game!")


class BaccaratBetModal(BetModal):

    def __init__(self, game: Game, type: BaccaratBetType):
        super().__init__(game)
        self.bet_type = type
    
    async def on_submit(self, interaction: discord.Interaction):
        await super().on_submit(interaction)
        self.game.players[interaction.user.id].bet.type = self.bet_type