from abc import ABC, abstractmethod # Importing abstract classes functionality
from random import randrange
import discord
from discord.ext import commands
from enums import E
from typing import Callable, Awaitable
from casino_bot import player_stats, add_player_balance, get_player_balance


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
    def __init__(self, player: RNGPlayer, bet: int, odd: int):
        self.player = player
        self.bet = bet
        self.odd = odd

class RNGGame(ABC):
    name: str
    lowest: int
    highest: int
    bets: dict[int, list[Bet]]
    players: dict[str, RNGPlayer]
    last_roll: int | None
    commands_dict: dict[str, Callable[[commands.Context, list[str]], Awaitable[None]]]
    def __init__(self, name: str, lowest: int, highest: int):
        self.name = name
        self.lowest = lowest
        self.highest = highest
        self.bets = {number: [] for number in range(self.lowest, self.highest + 1)}
        self.players = dict()
        self.last_roll = None
        
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
        cmd_status: E = self.add_player(ctx.author.id, ctx.author.display_name, argv[1])
        if cmd_status == E.INV_PLAYER:
            await ctx.send(f"Player {ctx.author.display_name} is already in-game")
            return
        if cmd_status == E.INSUFFICIENT_FUNDS:
            await ctx.send(f"Player {ctx.author.display_name} wants to bet more than they have in their account")
            return
        await ctx.send(f"Player {ctx.author.display_name} has successfully joined the game with balance {self.players[ctx.author.display_name].balance}")

    def add_player(self, player_id: int, name: str, balance: int=0) -> E:
        if self.players.get(name, None) is not None:
            return E.INV_PLAYER
        if balance > get_player_balance(player_id):
            return E.INSUFFICIENT_FUNDS

        self.players[name] = RNGPlayer(player_id, name, balance)
        return E.SUCCESS

    def remove_player(self, name: str) -> E:
        if self.players.get(name, None) is None:
            return E.INV_PLAYER
        
        self.players.pop(name)
        return E.SUCCESS
    
    def place_bet(self, name: str, bet: int, number: int, odd: int) -> E:
        if number < self.lowest or number > self.highest:
            return E.OUT_OF_RANGE
        if bet > self.players[name].balance:
            return E.INSUFFICIENT_FUNDS
        
        new_bet = Bet(self.players[name], bet, odd)
        self.bets[number].append(new_bet)
        new_bet.player.balance -= bet
        return E.SUCCESS
    
    def ready_up(self, name: str) -> E:
        if self.players.get(name, None) is None:
            return E.INV_PLAYER
        if self.players[name].ready:
            return E.INV_STATE

        self.players[name].ready = True
        return E.SUCCESS

    def check_ready(self) -> bool:
        for player in self.players.values():
            if not player.ready:
                return False
        return True
    
    def roll(self) -> E:
        if not self.check_ready():
            return E.INV_STATE
        result: int = randrange(self.lowest, self.highest + 1)
        if (result in self.bets.keys()):
            for bet in self.bets[result]:
                bet.player.balance += bet.bet * bet.odd
        for player in self.players.values():
            player.ready = False
        self.bets = {number: [] for number in range(self.lowest, self.highest + 1)}
        self.last_roll = result
        return E.SUCCESS

class Coinflip(RNGGame):
    def __init__(self):
        super().__init__("coinflip", 1, 2)

class RollTheDice(RNGGame):
    def __init__(self):
        super().__init__("dice", 1, 6)

    

