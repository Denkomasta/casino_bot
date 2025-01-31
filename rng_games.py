from abc import ABC, abstractmethod # Importing abstract classes functionality
from random import randrange
import discord
from discord.ext import commands
from enums import E, GameType, CoinflipSides
from typing import Callable, Awaitable, Type
from database import Database
from base_classes import Game

class RNGPlayer:
    player_id: int
    name: str
    ready: bool
    def __init__(self, player_id: int, name: str):
        self.player_id = player_id
        self.name = name
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

class RNGGame(Game, ABC):
    name: str
    lowest: int
    highest: int
    bets: dict[int, list[Bet]]
    players: dict[int, RNGPlayer]
    last_roll: int | None
    database: Database
    def __init__(self, database: Database, name: str, lowest: int, highest: int, gametype: GameType):
        super().__init__(database, gametype)
        self.database = database
        self.name = name
        self.lowest = lowest
        self.highest = highest
        self.bets = {number: [] for number in range(self.lowest, self.highest + 1)}
        self.players = dict()
        self.last_roll = None

    def add_player(self, player_id: int, name: str) -> E:
        if self.players.get(name, None) is not None:
            return E.INV_PLAYER
        self.players[player_id] = RNGPlayer(player_id, name)
        return E.SUCCESS

    def remove_player(self, player_id: int) -> E:
        if self.players.get(player_id, None) is None:
            return E.INV_PLAYER
        self.players.pop(player_id)
        return E.SUCCESS
    
    def place_bet(self, player_id: int, bet_amount: int, number: int, odd: int) -> E:
        if self.players.get(player_id, None) is None:
            return E.INV_PLAYER
        if number < self.lowest or number > self.highest:
            return E.OUT_OF_RANGE
        if bet_amount > self.database.get_player_balance(player_id):
            return E.INSUFFICIENT_FUNDS
        existing_bet = self.find_duplicite_bet(player_id, number)
        if existing_bet is not None:
            existing_bet.bet += bet_amount
            existing_bet.possible_winning = bet_amount * odd
            self.database.change_player_balance(player_id, -bet_amount)
            return E.DUPLICITE_BET
        new_bet = Bet(self.players[player_id], bet_amount, odd)
        self.bets[number].append(new_bet)
        self.database.change_player_balance(player_id, -bet_amount)
        return E.SUCCESS
    
    def find_duplicite_bet(self, player_id: int, number: int) -> Bet | None:
        for bet in self.bets[number]:
            if bet.player.player_id == player_id:
                return bet
        return None

    def change_bet(self, player_id: int, new_bet_amount: int, new_number: int, new_odd: int) -> E:
        if self.players.get(player_id, None) is None:
            return E.INV_PLAYER
        if new_number < self.lowest or new_number > self.highest:
            return E.OUT_OF_RANGE
        temp = self.find_bet_by_player(player_id)
        if temp is None:
            return self.place_bet(player_id, new_bet_amount, new_number, new_odd)

        existing_bet = self.bets[temp[0]][temp[1]]
        number, index = temp
        if new_bet_amount > self.database.get_player_balance(player_id):
            return E.INSUFFICIENT_FUNDS

        if new_bet_amount != existing_bet.bet:
            self.database.change_player_balance(player_id, existing_bet.bet)
            existing_bet.bet = new_bet_amount
            existing_bet.possible_winning = new_bet_amount * new_odd
            self.database.change_player_balance(player_id, -new_bet_amount)
        
        if new_number != number:
            self.bets[number].pop(index)
            self.bets[new_number].append(existing_bet)

        return E.SUCCESS
    
    def find_bet_by_player(self, player_id: int) -> tuple[int, int] | None:
        for number, bets in self.bets.items():
            for i in range(len(bets)):
                if bets[i].player.player_id == player_id:
                    return number, i
        return None
    
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
    
    def roll(self) -> list[Bet]:
        winning_number: int = randrange(self.lowest, self.highest + 1)
        self.last_roll = winning_number
        return self.bets[winning_number]

    def give_winnings(self, winning_bets: list[Bet]) -> E:
        retval: E = E.SUCCESS
        for bet in winning_bets:
            if self.players.get(bet.player.player_id, None) is None:
                retval = E.INV_PLAYER
                continue
            self.database.change_player_balance(bet.player.player_id, bet.possible_winning)
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

    def check_valid_player(self, player_id: int):
        return (self.players.get(player_id, None) is not None)

    def get_status_msg(self):
        message = f"There are now {len(self.players.values())} players in this game, listing:\n" + 25 * '-' + '\n'
        for player in self.players.values():
            message += (player.name + " - " + ("Ready" if player.ready else "Not ready") + "\n")
        return message + "The game will start rolling automatically after everyone is ready!"

    @abstractmethod
    def get_bets_msg(self):
        pass

class Coinflip(RNGGame):
    def __init__(self, data: Database):
        super().__init__(data, "coinflip", 1, 2, GameType.COINFLIP)
    
    # Override
    def get_bets_msg(self):
        message = f"Current bets are as follows:\n" + 25 * '-' + '\n'
        try:
            message += "HEADS: " + self.list_bets(CoinflipSides.HEADS) + "\n"
            message += "TAILS: " + self.list_bets(CoinflipSides.TAILS) + "\n"
        except ValueError:
            return None
        return message
    
    def list_bets(self, number):
        bet_list = self.bets.get(int(number))
        message = ""
        if bet_list is None:
            raise ValueError
        for i, bet in enumerate(bet_list):
            if i > 0:
                message += ", "
            message += f"({bet.player.name}, {bet.bet})"
        return message

class GuessTheNumber(RNGGame):
    rounds: int
    remaining_rounds: int
    def __init__(self, data: Database):
        super().__init__(data, "GuessTheNumber", 1, 100, GameType.GUESSNUMBER)
        self.rounds = 3
        self.remaining_rounds = self.rounds

class RollTheDice(RNGGame):
    def __init__(self, data: Database):
        super().__init__(data, "dice", 1, 6, GameType.ROLLTHEDICE)