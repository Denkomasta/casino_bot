from abc import ABC, abstractmethod # Importing abstract classes functionality
from random import randrange
import discord
from discord.ext import commands
from enums import E, GameType, CoinflipSides, RTDDoubles, PlayerState
from typing import Callable, Awaitable, Type
from database import Database
from base_classes import Game, Player
from ascii_obj import Ascii

class RNGPlayer(Player):
    def __init__(self, player_info):
        super().__init__(player_info)

class RNGBet:
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
    bets: dict[int, list[RNGBet]]
    players: dict[int, RNGPlayer]
    last_roll: int | None
    database: Database
    def __init__(self, database: Database, name: str, lowest: int, highest: int, gametype: GameType, channel: discord.TextChannel):
        super().__init__(database, channel, gametype)
        self.database = database
        self.name = name
        self.lowest = lowest
        self.highest = highest
        self.bets = {number: [] for number in range(self.lowest, self.highest + 1)}
        self.players = dict()
        self.last_roll = None

    def add_player(self, player_info: discord.User | discord.Member) -> E:
        if self.players.get(player_info.id, None) is not None:
            return E.INV_STATE
        self.players[player_info.id] = RNGPlayer(player_info)
        return E.SUCCESS

    def remove_player(self, player_info: discord.User | discord.Member) -> E:
        if self.players.get(player_info.id, None) is None:
            return E.INV_STATE
        self.players.pop(player_info.id)
        return E.SUCCESS
    
    def place_bet(self, player_info: discord.User | discord.Member, bet_amount: int, number: int, odd: int) -> E:
        if self.players.get(player_info.id, None) is None:
            return E.INV_PLAYER
        if number < self.lowest or number > self.highest:
            return E.OUT_OF_RANGE
        if bet_amount > self.database.get_player_balance(player_info.id):
            return E.INSUFFICIENT_FUNDS

        existing_bet = self.find_duplicite_bet(player_info, number)
        if existing_bet is not None:
            existing_bet.bet += bet_amount
            existing_bet.possible_winning = bet_amount * odd
            self.database.change_player_balance(player_info.id, -bet_amount)
            return E.DUPLICITE_BET

        new_bet = RNGBet(self.players[player_info.id], bet_amount, odd)
        self.bets[number].append(new_bet)
        self.database.change_player_balance(player_info.id, -bet_amount)
        return E.SUCCESS
    
    def find_duplicite_bet(self, player_info: discord.User | discord.Member, number: int) -> RNGBet | None:
        for bet in self.bets[number]:
            if bet.player.player_info.id == player_info.id:
                return bet
        return None

    def change_bet(self, player_info: discord.User | discord.Member, new_bet_amount: int, new_number: int, new_odd: int) -> E:
        if self.players.get(player_info.id, None) is None:
            return E.INV_PLAYER
        if new_number < self.lowest or new_number > self.highest:
            return E.OUT_OF_RANGE
        temp = self.find_bet_by_player(player_info.id)
        if temp is None:
            return self.place_bet(player_info, new_bet_amount, new_number, new_odd)

        existing_bet = self.bets[temp[0]][temp[1]]
        number, index = temp
        if new_bet_amount > self.database.get_player_balance(player_info.id):
            return E.INSUFFICIENT_FUNDS

        if new_bet_amount != existing_bet.bet:
            self.database.change_player_balance(player_info.id, existing_bet.bet)
            existing_bet.bet = new_bet_amount
            existing_bet.possible_winning = new_bet_amount * new_odd
            self.database.change_player_balance(player_info.id, -new_bet_amount)
        
        if new_number != number:
            self.bets[number].pop(index)
            self.bets[new_number].append(existing_bet)

        return E.SUCCESS
    
    def find_bet_by_player(self, player_info: discord.User | discord.Member) -> tuple[int, int] | None:
        for number, bets in self.bets.items():
            for i in range(len(bets)):
                if bets[i].player.player_info.id == player_info.id:
                    return number, i
        return None
    

    def check_ready(self) -> bool:
        for player in self.players.values():
            if player.state == PlayerState.NOT_READY:
                return False
        return True
    
    def roll(self) -> list[RNGBet]:
        winning_number: int = randrange(self.lowest, self.highest + 1)
        self.last_roll = winning_number
        return self.bets[winning_number]

    def give_winnings(self, winning_bets: list[RNGBet]) -> E:
        retval: E = E.SUCCESS
        for bet in winning_bets:
            if self.players.get(bet.player.player_info.id, None) is None:
                retval = E.INV_PLAYER
                continue
            self.database.change_player_balance(bet.player.player_info.id, bet.possible_winning)
        return retval
    
    def build_winners_message(self, winning_bets: list[RNGBet]) -> str:
        if len(winning_bets) == 0:
            return "No winners this round!"
        message = f"The winners are:\n{winning_bets[0].player.player_info.display_name} with a win of {winning_bets[0].possible_winning}"
        for i in range(1, len(winning_bets)):
            message += f"\n{winning_bets[i].player.player_info.display_name} with a win of {winning_bets[i].possible_winning}"
        message += "\nCongratulations!"
        return message

    def restart_game(self):
        self.bets = {number: [] for number in range(self.lowest, self.highest + 1)}
        for player in self.players.values():
            player.state = PlayerState.NOT_READY


    def get_status_msg(self):
        message = f"There are now {len(self.players.values())} players in this game, listing:\n" + 25 * '-' + '\n'
        for player in self.players.values():
            message += (player.player_info.display_name + " - " + ("Ready" if player.state == PlayerState.READY else "Not ready") + "\n")
        return message + "The game will start rolling automatically after everyone is ready!"

    @abstractmethod
    def get_bets_msg(self):
        pass

    def list_bets(self, number):
        bet_list = self.bets.get(int(number))
        message = ""
        if bet_list is None:
            raise ValueError
        for i, bet in enumerate(bet_list):
            if i > 0:
                message += ", "
            message += f"({bet.player.player_info.display_name}, {bet.bet})"
        return message

class Coinflip(RNGGame):
    def __init__(self, data: Database, channel: discord.TextChannel):
        super().__init__(data, "coinflip", 1, 2, GameType.COINFLIP, channel)
    
    # Override
    def get_bets_msg(self):
        message = f"Current bets are as follows:\n" + 25 * '-' + '\n'
        try:
            message += "HEADS: " + self.list_bets(CoinflipSides.HEADS) + "\n"
            message += "TAILS: " + self.list_bets(CoinflipSides.TAILS) + "\n"
        except ValueError:
            return None
        return message

class GuessTheNumber(RNGGame):
    rounds: int
    remaining_rounds: int
    def __init__(self, data: Database, channel: discord.TextChannel):
        self.rounds = 4
        self.remaining_rounds = self.rounds
        super().__init__(data, "gtn", 1, 100, GameType.GUESSNUMBER, channel)
    
    def get_bets_msg(self):
        pass

class RollTheDice(RNGGame):
    def __init__(self, data: Database, channel: discord.TextChannel):
        self.rates : dict[int, float]
        self.last_dice1: int
        self.last_dice2: int
        super().__init__(data, "rtd", 2, 12, GameType.ROLLTHEDICE, channel)
        for number in range(-1, -7, -1):
            self.bets[number] = []
        self.rates = {
            2 : 36,
            3 : 18,
            4 : 12,
            5 : 9,
            6 : 7.2,
            7 : 6,
            8 : 7.2,
            9 : 9,
            10 : 12,
            11 : 18,
            12 : 36,
            int(RTDDoubles.ONES) : 36,
            int(RTDDoubles.TWOS) : 36,
            int(RTDDoubles.THREES) : 36,
            int(RTDDoubles.FOURS) : 36,
            int(RTDDoubles.FIVES) : 36,
            int(RTDDoubles.SIXES) : 36
        }
    
    def get_rate(self, number):
        return self.rates.get(number)
    
    # Override
    def place_bet(self, player_info: discord.User | discord.Member, bet_amount: int, number: int, odd: float) -> E:
        if self.players.get(player_info.id, None) is None:
            return E.INV_PLAYER
        if number < -6 or number in [0, 1] or number > 12:
            return E.OUT_OF_RANGE
        if bet_amount > self.database.get_player_balance(player_info.id):
            return E.INSUFFICIENT_FUNDS

        existing_bet = self.find_duplicite_bet(player_info.id, number)
        if existing_bet is not None:
            existing_bet.bet += bet_amount
            existing_bet.possible_winning = bet_amount * odd
            self.database.change_player_balance(player_info.id, -bet_amount)
            return E.DUPLICITE_BET

        new_bet = RNGBet(self.players[player_info.id], bet_amount, odd)
        self.bets[number].append(new_bet)
        self.database.change_player_balance(player_info.id, -bet_amount)
        return E.SUCCESS
    
    # Override
    def roll(self) -> list[RNGBet]:
        self.last_dice1: int = randrange(1, 7)
        self.last_dice2: int = randrange(1, 7)
        self.last_roll = self.last_dice1 + self.last_dice2
        winning_bets = self.bets[self.last_roll]
        if self.last_dice1 == self.last_dice2:
            winning_bets.extend(self.bets[-self.last_dice1])
        return winning_bets
    
    def build_conclusion_message(self, winning_bets: list[RNGBet]):
        message = "Dice are on the table and the result is:\n"
        message += Ascii.draw_dice([self.last_dice1, self.last_dice2])
        message += f"We got a sum of {self.last_roll}!"
        if self.last_dice1 == self.last_dice2:
            message += f" On top of that, we got DOUBLE {self.last_dice1}"
        message += '\n' + self.build_winners_message(winning_bets) + '\n'
        return message
    
    def get_bets_msg(self):
        message = f"Current bets are as follows:\n" + 25 * '-' + '\n'
        for sum in range(2, 13):
            if len(self.bets[sum]) == 0:
                continue
            message += f"Sum of {sum}: " + self.list_bets(sum) + "\n"
        for doubles in range(1, 7):
            if len(self.bets[-doubles]) == 0:
                continue
            message += f"Double {doubles}s: " + self.list_bets(-doubles) + "\n"
        return message
    
    def restart_game(self):
        self.bets = {number: [] for number in range(self.lowest, self.highest + 1)}
        for number in range(-1, -7, -1):
            self.bets[number] = []
        for player in self.players.values():
            player.state = PlayerState.NOT_READY

class Roulette(RNGGame):

    def __init__(self, data: Database, channel: discord.TextChannel):
        super().__init__(data, "roulette", 0, 36, GameType.ROULETTE, channel)

#              ││
#              \/
#            │ 47 │
#       │ 56 │BLCK│
#  │ 24 │RED-│    │
#  │BLCK│
# 
# 
# 
# 
