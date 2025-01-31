from abc import ABC, abstractmethod # Importing abstract classes functionality
from random import randrange
import discord
from discord.ext import commands
from enums import E, GameType
from typing import Callable, Awaitable
from database import Database
from base_classes import Game

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

class RNGGame(Game):
    name: str
    lowest: int
    highest: int
    bets: dict[int, list[Bet]]
    players: dict[int, RNGPlayer]
    last_roll: int | None
    database: Database
    commands_dict: dict[str, Callable[[commands.Context, list[str]], Awaitable[None]]]
    def __init__(self, database: Database, name: str, lowest: int, highest: int, gametype: GameType):
        super().__init__(database, gametype)
        self.database = database
        self.name = name
        self.lowest = lowest
        self.highest = highest
        self.bets = {number: [] for number in range(self.lowest, self.highest + 1)}
        self.players = dict()
        self.last_roll = None

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
    def __init__(self, data: Database):
        super().__init__(data, "coinflip", 1, 2, GameType.COINFLIP)

class RollTheDice(RNGGame):
    def __init__(self, data: Database):
        super().__init__(data, "dice", 1, 6, GameType.ROLLTHEDICE)