from random import randrange
from typing import Callable, Awaitable
import discord
from discord.ext import commands
from enums import E, GameState, PlayerState, GameType, PlayerResult, CardSuits
from database import Database
from base_classes import CardGame, CardPlayer, Card, Player
from itertools import combinations
from collections import Counter



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

    def determine_winner(self):     # use ranks and values to determine winner
        pass

    def best_hand(self, player: CardPlayer):
        all_five_card_hands = combinations(player.cards, 5)
        return max(all_five_card_hands, key=self.get_hand_rank)

    def get_hand_rank(self, hand: list[Card]):
        values = sorted([card.value for card in hand], reverse=True)
        suits = [card.suit for card in hand]

        value_counts = Counter(values)
        sorted_counts = sorted(value_counts.values(), reverse=True)

        is_flush = len(set(suits)) == 1
        is_straight = values == list(range(values[0], values[0] - 5, -1)) or values == [14, 5, 4, 3, 2]

        if is_straight and is_flush:
            return (9, values) if values[0] == 14 else (8, values)  # Royal Flush / Straight Flush
        if 4 in sorted_counts:
            return (7, values)  # Four of a Kind
        if sorted_counts == [3, 2]:
            return (6, values)  # Full House
        if is_flush:
            return (5, values)  # Flush
        if is_straight:
            return (4, values)  # Straight
        if 3 in sorted_counts:
            return (3, values)  # Three of a Kind
        if sorted_counts == [2, 2, 1]:
            return (2, values)  # Two Pair
        if 2 in sorted_counts:
            return (1, values)  # One Pair
        return (0, values)  # High Card
