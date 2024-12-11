from abc import ABC, abstractmethod # Importing abstract classes functionality
from random import randrange
import discord
from discord.ext import commands

SUCCESS = 0
EINVALID_PLAYER = -1
ENUMBER_OUT_OF_RANGE = -2
EINSUFFICIENT_FUNDS = -3
EREADY = -4


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
    players_not_ready: int
    last_roll: int | None
    def __init__(self, lowest: int, highest: int):
        self.lowest = lowest
        self.highest = highest
        self.bets = dict()
        self.players = dict()
        self.last_roll = None

    def add_player(self, name: str, balance: int=0) -> int:
        if self.players.get(name, None) is None:
            return EINVALID_PLAYER

        self.players[name] = RNGPlayer(name, balance)
        self.players_not_ready += 1
        return SUCCESS

    def remove_player(self, name: str) -> int:
        if self.players.get(name, None) is None:
            return EINVALID_PLAYER
        
        self.players.pop(name)
        return SUCCESS
    
    def place_bet(self, name: str, bet: int, number: int, odd: int) -> int:
        if number < self.lowest or number > self.highest:
            return ENUMBER_OUT_OF_RANGE
        if bet > self.players[name].balance:
            return EINSUFFICIENT_FUNDS
        
        new_bet = Bet(self.players[name], bet, odd)
        self.bets[number].append(new_bet)
        return SUCCESS
    
    def ready_up(self, name: str) -> int:
        if self.players.get(name, None) is None:
            return EINVALID_PLAYER
        if self.players[name].ready:
            return EREADY

        self.players[name].ready = True
        self.players_not_ready -= 1
        return SUCCESS
    
    def roll(self) -> int:
        if self.players_not_ready > 0:
            return EREADY
        result: int = randrange(self.lowest, self.highest)
        if (result in self.bets.keys()):
            for bet in self.bets[result]:
                bet.player.balance += bet.bet * bet.odd
        for player in self.players.values():
            player.ready = False
            self.players_not_ready += 1
        self.bets = dict()
        self.last_roll = result
        return SUCCESS
        

        
        


    

