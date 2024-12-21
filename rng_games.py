from abc import ABC, abstractmethod # Importing abstract classes functionality
from random import randrange
import discord
from discord.ext import commands
from enums import E
from typing import Callable, Awaitable
from database import Database


class RNGPlayer:
    player_id: int
    name: str
    balance: int
    ready: bool
    def __init__(self, player_id: int, name: str, balance: int):
        self.player_id = player_id
        self.name = name
        self.balance = balance
        self.ready = False

class Bet:
    player: RNGPlayer
    bet: int
    odd: int
    possible_winning: int
    def __init__(self, player: RNGPlayer, bet: int, odd: int):
        self.player = player
        self.bet = bet
        self.odd = odd
        self.possible_winning = self.bet * self.odd

class RNGGame(ABC):
    name: str
    lowest: int
    highest: int
    bets: dict[int, list[Bet]]
    players: dict[int, RNGPlayer]
    last_roll: int | None
    database: Database
    commands_dict: dict[str, Callable[[commands.Context, list[str]], Awaitable[None]]]
    def __init__(self, database: Database, name: str, lowest: int, highest: int):
        self.database = database
        self.name = name
        self.lowest = lowest
        self.highest = highest
        self.bets = {number: [] for number in range(self.lowest, self.highest + 1)}
        self.players = dict()
        self.last_roll = None
        self.commands_dict = {
            "join": self.command_join,
            "bet": self.command_bet,
            "leave": self.command_leave,
            "ready": self.command_ready,
            "unready": self.command_unready
        }
        
    async def command_run(self, ctx: commands.Context, argv: list[str]):
        if len(argv) == 0:
            await ctx.send(f"No argument, run !{self.name} help for available commands")
            return
        command = argv[0]
        if self.commands_dict.get(command, None) is None:
            await ctx.send(f"Unknown command, run !{self.name} help for available commands")
            return
        await self.commands_dict[command](ctx, argv)

    async def inv_args_message(self, ctx: commands.Context):
        await ctx.send(f"Invalid number of arguments, run !{self.name} help for available commands")

    async def command_join(self, ctx: commands.Context, argv: list[str]):
        if len(argv) > 2:
            await self.inv_args_message(ctx)
            return
        try:
            bet: int = int(argv[1])
        except ValueError:
            await ctx.send(f"Invalid format of bet, insert whole number")
            return
        cmd_status: E = self.add_player(ctx.author.id, ctx.author.display_name, bet)
        if cmd_status == E.INV_PLAYER:
            await ctx.send(f"Player {ctx.message.author.mention} is already in-game")
            return
        if cmd_status == E.INSUFFICIENT_FUNDS:
            await ctx.send(f"{ctx.message.author.mention} You don't have enough money in your server balance!")
            return
        await ctx.send(f"Player {ctx.author.display_name} has successfully joined the game with balance {self.players[ctx.author.id].balance}\n\
                        {ctx.message.author.mention} The in-game balance was deducted from your global balance and will be returned when you leave using !{self.name} leave")

    async def command_leave(self, ctx: commands.Context, argv: list[str]):
        cmd_status: E = self.remove_player(ctx.author.id)
        if cmd_status == E.INV_PLAYER:
            await ctx.send(f"{ctx.message.author.mention} You are not in the game!")
        await ctx.send(f"Player {ctx.author.display_name} has successfully left the game. \n{ctx.message.author.mention} Your server balance was updated!")

    async def command_bet(self, ctx: commands.Context, argv: list[str]):
        if len(argv) != 3:
            await self.inv_args_message(ctx)
            return
        try:
            number = int(argv[1])
            bet = int(argv[2])
        except ValueError:
            await ctx.send(f"Invalid format of the command, both number and the value of the bet must be whole numbers.")
            return
        cmd_status: E = self.place_bet(ctx.author.id, bet, number, (self.highest - self.lowest + 1))
        if cmd_status == E.INV_PLAYER:
            ctx.send(f"{ctx.message.author.mention} You are not in the game! You must use !{self.name} join [balance] to participate")
        if cmd_status == E.OUT_OF_RANGE:
            await ctx.send(f"{ctx.message.author.mention} The number you want to bet on is out of the valid range. Bet on a number between {self.lowest} and {self.lowest}")
            return
        if cmd_status == E.INSUFFICIENT_FUNDS:
            await ctx.send(f"{ctx.message.author.mention} You don't have enough money in your in-game balance. Try again with less or re-join the game with higher balance!")
            return
        await ctx.send(f"Player {ctx.author.display_name} has successfully bet {bet} on number {number}")

    async def command_ready(self, ctx: commands.Context, argv: list[str]):
        cmd_status: E = self.ready_up(ctx.author.id)
        if cmd_status == E.INV_PLAYER:
            ctx.send(f"{ctx.message.author.mention} You are not in the game! You must use !{self.name} join [balance] to participate")
            return
        if cmd_status == E.INV_STATE:
            ctx.send(f"{ctx.message.author.mention} You are already ready for the roll!")
            return
        await ctx.send(f"Player {ctx.author.display_name} is ready for the roll!")

    async def command_unready(self, ctx: commands.Context, argv: list[str]):
        cmd_status: E = self.unready(ctx.author.id)
        if cmd_status == E.INV_PLAYER:
            ctx.send(f"{ctx.message.author.mention} You are not in the game! You must use !{self.name} join [balance] to participate")
            return
        await ctx.send(f"Player {ctx.author.display_name} needs more time to think and is now not ready")

    async def command_roll(self, ctx: commands.Context, argv: list[str]):
        if not self.check_ready():
            await ctx.send(f"All players must be ready in order to roll!")
            return
        winning_bets: list[Bet] = self.roll()
        await ctx.send(f"The winning number is: {self.last_roll}! �")
        await ctx.send(self.build_winners_message(winning_bets))
        if self.give_winnings(winning_bets) == E.INV_PLAYER:
            await ctx.send(f"One or more players could not collect their winning because they left the game :(")
        self.restart_game()
        await ctx.send(f"The game has been restarted, bet and try your luck again!")

    def add_player(self, player_id: int, name: str, balance: int = 1) -> E:
        if self.players.get(name, None) is not None:
            return E.INV_PLAYER
        if balance > self.database.get_player_balance(player_id):
            return E.INSUFFICIENT_FUNDS
        
        self.database.change_player_balance(player_id, -balance)
        self.players[player_id] = RNGPlayer(player_id, name, balance)
        return E.SUCCESS

    def remove_player(self, player_id: int) -> E:
        if self.players.get(player_id, None) is None:
            return E.INV_PLAYER
        
        self.database.change_player_balance(player_id, self.players[player_id].balance)
        self.players.pop(player_id)
        return E.SUCCESS
    
    def place_bet(self, player_id: int, bet: int, number: int, odd: int) -> E:
        if self.players.get(player_id, None) is None:
            return E.INV_PLAYER
        if number < self.lowest or number > self.highest:
            return E.OUT_OF_RANGE
        if bet > self.players[player_id].balance:
            return E.INSUFFICIENT_FUNDS
        
        new_bet = Bet(self.players[player_id], bet, odd)
        self.bets[number].append(new_bet)
        new_bet.player.balance -= bet
        return E.SUCCESS
    
    def ready_up(self, player_id: int) -> E:
        if self.players.get(player_id, None) is None:
            return E.INV_PLAYER
        if self.players[player_id].ready:
            return E.INV_STATE

        self.players[player_id].ready = True
        return E.SUCCESS

    def unready(self, player_id: int) -> E:
        if self.players.get(player_id, None) is None:
            return E.INV_PLAYER
        if not self.players[player_id].ready:
            return E.INV_STATE

        self.players[player_id].ready = False
        return E.SUCCESS

    def check_ready(self) -> bool:
        for player in self.players.values():
            if not player.ready:
                return False
        return True
    
    def roll(self) -> tuple[int, list[Bet]]:
        winning_number: int = randrange(self.lowest, self.highest + 1)
        self.last_roll = winning_number
        return self.bets[winning_number]

    def give_winnings(self, winning_bets: list[Bet]) -> E:
        retval: E = E.SUCCESS
        for bet in winning_bets:
            if self.players.get(bet.player.player_id, None) is None:
                retval = E.INV_PLAYER
                continue
            bet.player.balance += bet.possible_winning
        return retval
    
    def build_winners_message(self, winning_bets: list[Bet]) -> str:
        if len(winning_bets) == 0:
            return "No winners this round!"
        message = f"The winners are:\n{winning_bets[0].player.name} with a win of {winning_bets[0].possible_winning}"
        for i in range(1, len(winning_bets)):
            message += f"\n{winning_bets[i].player.name} with a win of {winning_bets[i].possible_winning}"
        message += "\nCongratulations!"
        return message

    def restart_game(self):
        self.bets = {number: [] for number in range(self.lowest, self.highest + 1)}
        for player in self.players.values():
            player.ready = False

class Coinflip(RNGGame):
    def __init__(self):
        super().__init__("coinflip", 1, 2)

class RollTheDice(RNGGame):
    def __init__(self):
        super().__init__("dice", 1, 6)