from random import randrange
from typing import Callable, Awaitable
import discord
from discord.ext import commands
from enums import E, GameState, PlayerState, GameType, PlayerResult, CardSuits
from database import Database
from base_classes import CardGame, CardPlayer, Card, Player



class Poker(CardGame):
    
    def __init__(self, data: Database, channel: discord.TextChannel):
        super().__init__(data, channel, GameType.POKER)
        self.players = {}
        self.state = GameState.WAITING_FOR_PLAYERS
    
    def game_start(self):
        pass

    def game_finish(self):
        pass

    def play_round(self):
        pass

    # !!! player.cards needs to be sorted and change ace value from 1 to 14 !!!
    def royal_flush(self, players: list[CardPlayer]) -> list[CardPlayer]:
        res = []
        vals = [10, 11, 12, 13, 14]
        for player in players:
            suit: CardSuits = player.cards[0].suit
            has = True
            for i in range(len(player.cards)):
                card = player.cards[i]
                if card.suit != suit:
                    has = False
                    break
                if card.value != vals[i]:
                    has = False
                    break
            if has:
                res.append(player)
        return res

    def straight_flush(self, players: list[CardPlayer]) -> list[CardPlayer]:
        res = []
        max_val = 2
        for player in players:
            suit: CardSuits = player.cards[0].suit
            curr_max = player.cards[-1].value
            has = True
            for i in range(1, len(player.cards)):
                card = player.cards[i]
                if card.suit != suit:
                    has = False
                    break
                if card.value != player.cards[i - 1].value - 1:
                    has = False
                    break
            if has:
                if curr_max > max_val:
                    res = [player]
                    max_val = curr_max
                elif curr_max == max_val:
                    res.append(player)
        return res

    def four_of_a_kind(self, players: list[CardPlayer]) -> list[CardPlayer]:
        res = []
        max_val = 2
        max_div = 2
        for player in players:
            has = True
            curr_div = player.cards[0].value
            if curr_div == player.cards[3].value:
                curr_div = player.cards[4].value
            elif player.cards[1].value == player.cards[4].value:
                pass
            else:
                has = False

            poker = player.cards[2].value

            if has:
                if poker > max_val:
                    res = [player]
                    max_val = poker
                    max_div = curr_div
                elif poker == max_val:
                    if curr_div > max_div:
                        res = [player]
                        max_div = curr_div
                    elif curr_div == max_div:
                        res.append(player)
        return res

    def full_house(self, players: list[CardPlayer]) -> list[CardPlayer]:
        res = []
        max_trips = 2
        max_pair = 2
        for player in players:
            has = True
            trips = player.cards[2].value
            pair = player.cards[0].value

            if trips != player.cards[4].value:
                pair = player.cards[4].value
                if trips != player.cards[0].value or pair != player.cards[3].value:
                    has = False
                    continue

            if has:
                if trips > max_trips:
                    res = [player]
                    max_trips = trips
                    max_pair = pair
                elif trips == max_trips:
                    if pair > max_pair:
                        res = [player]
                        max_pair = pair
                    elif pair == max_pair:
                        res.append(player)
        return res

    def flush(self, players: list[CardPlayer]) -> list[CardPlayer]:
        res = []
        max_flush = [2, 2, 2, 2, 2]
        for player in players:
            suit: CardSuits = player.cards[0].suit
            has = True
            temp = []
            for i in range(len(player.cards) - 1, -1, -1):
                card = player.cards[i]
                if card.suit != suit:
                    has = False
                    break
                temp.append(card.value)

            if has:
                if temp > max_flush:    # TODO optimize
                    res = [player]
                    max_flush = temp
                elif temp == max_flush:
                    res.append(player)
        return res

    def straight(self, players: list[CardPlayer]) -> list[CardPlayer]:
        res = []
        max_val = 2
        for player in players:
            curr_max = player.cards[-1].value
            has = True
            for i in range(len(player.cards)):
                card = player.cards[i]
                if card.value != player.cards[i - 1].value - 1:
                    if i == 4 and card.value == 14 and player.cards[3].value == 5:
                        curr_max = 5
                        continue
                    has = False
                    break
            if has:
                if curr_max > max_val:
                    res = [player]
                    max_val = curr_max
                elif curr_max == max_val:
                    res.append(player)
        return res

    def three_of_a_kind(self, players: list[CardPlayer]) -> list[CardPlayer]:
        res = []
        max_val = 2
        max_div = [2, 2]
        for player in players:
            curr = {}
            for card in player.cards:
                curr[card.value] = curr.get(card.value, 0) + 1
            has = False
            div = []

            for key, value in curr.items():
                if value == 3:
                    has = True
                else:
                    div.append(key)

            if has:
                div.sort(reverse=True)
                if player.cards[2].value > max_val:
                    res = [player]
                    max_val = player.cards[2].value
                    max_div = div
                elif player.cards[2].value == max_val:
                    if div > max_div:
                        res = [player]
                        max_div = div
                    elif div == max_div:
                        res.append(player)
        return res

    def two_pair(self, players: list[CardPlayer]) -> list[CardPlayer]:
        res = []
        max_val = [2, 2, 2]   # bigger pair, smaller pair, div
        
        for player in players:
            curr = {}
            val = []
            for card in player.cards:
                curr[card.value] = curr.get(card.value, 0) + 1
            
            one = 0
            pair_c = 0
            for key, value in curr.items():
                if value == 2:
                    pair_c += 1
                    val.append(key)
                else:
                    one = key
            
            if pair_c == 2:
                val.sort(reverse=True)
                val.append(one)
                if val > max_val:
                    res = [player]
                    max_val = val
                elif val == max_val:
                    res.append(player)
        return res

    def one_pair(self, players: list[CardPlayer]) -> list[CardPlayer]:
        res = []

        max_val = [2, 2, 2, 2]
        for player in players:
            curr = {}
            val = []
            for card in player.cards:
                curr[card.value] = curr.get(card.value, 0) + 1
            
            has = False
            pair = []
            for key, value in curr.items():
                if value == 2:
                    has = True
                    pair.append(key)
                else:
                    val.append(key)
            
            if has:
                val.sort(reverse=True)
                val = pair + val
                if val > max_val:
                    res = [player]
                    max_val = val
                elif val == max_val:
                    res.append(player)
        return res

    def high_card(self, players: list[CardPlayer]) -> list[CardPlayer]:
        res = []
        max_val = [2, 2, 2, 2, 2]
        for player in players:
            val = []

            for card in player.cards:
                val.append(card.value)

            val.sort(reverse=True)
            if val > max_val:
                res = [player]
                max_val = val
            elif val == max_val:
                res.append(player)
        return res
