from abc import ABC, abstractmethod # Importing abstract classes functionality
from random import randrange
import discord
from discord.ext import commands
from enums import E


class RNGPlayer:
    name: str
    balance: int
    ready: bool
    def __init__(self, name: str, balance: int):
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
    lowest: int
    highest: int
    bets: dict[int, list[Bet]]
    players: dict[str, RNGPlayer]
    last_roll: int | None
    def __init__(self, lowest: int, highest: int):
        self.lowest = lowest
        self.highest = highest
        self.bets = {number: [] for number in range(self.lowest, self.highest + 1)}
        self.players = dict()
        self.last_roll = None

    def add_player(self, name: str, balance: int=0) -> int:
        if self.players.get(name, None) is not None:
            return E.INV_PLAYER

        self.players[name] = RNGPlayer(name, balance)
        return E.SUCCESS

    def remove_player(self, name: str) -> int:
        if self.players.get(name, None) is None:
            return E.INV_PLAYER
        
        self.players.pop(name)
        return E.SUCCESS
    
    def place_bet(self, name: str, bet: int, number: int, odd: int) -> int:
        if number < self.lowest or number > self.highest:
            return E.OUT_OF_RANGE
        if bet > self.players[name].balance:
            return E.INSUFFICIENT_FUNDS
        
        new_bet = Bet(self.players[name], bet, odd)
        self.bets[number].append(new_bet)
        new_bet.player.balance -= bet
        return E.SUCCESS
    
    def ready_up(self, name: str) -> int:
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
    
    def roll(self) -> int:
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
        super().__init__(1, 2)

class RollTheDice(RNGGame):
    def __init__(self):
        super().__init__(1, 6)

        
        


    

