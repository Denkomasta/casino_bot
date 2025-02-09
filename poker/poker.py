from random import randrange
from typing import Callable, Awaitable
import discord
from discord.ext import commands
from enums import E, GameState, PlayerState, GameType, PlayerResult, CardSuits, PokerRoundStatus, PokerPlayerState
from database import Database
from base_classes import CardGame, CardPlayer, Card, Player
from itertools import combinations
from collections import Counter
import traceback

class PokerPlayer(CardPlayer):
    def __init__(self, player_info):
        super().__init__(player_info)
        self.round_bet = 0

class PokerTable(CardPlayer):

    def __init__(self):
        self.cards = []

    def draw_card(self, game: CardGame):
        self.cards.append(game.draw_card())


class Poker(CardGame):
    
    def __init__(self, data: Database, channel: discord.TextChannel):
        super().__init__(data, channel, GameType.POKER)
        self.table: PokerTable = PokerTable()
        self.blind = 20
        self.blind_index = 0
        self.round_bet = 0
        self.bank = 0
    
    def game_start(self):
        self.get_blinds()

        for _ in range(2):
            for player in self.players.values():
                player.cards.append(self.draw_card())
                player.state = PokerPlayerState.WAITING

    def game_finish(self):
        pass

    def play_round(self):
        pass

    def round_restart(self):
        self.round_bet = 0
        for player in self.players.values():
            player.round_bet = 0
            if player.state != PokerPlayerState.FOLDED:
                player.state = PokerPlayerState.WAITING

    def raise_bet(self, new_bet: int, player: discord.User | discord.Member):
        self.bank += new_bet - self.players[player.id].round_bet
        self.players[player.id].bet.value -= new_bet - self.players[player.id].round_bet
        self.players[player.id].round_bet = new_bet
        self.round_bet = new_bet


    def game_restart(self):
        self.bank = 0
        self.blind += 10
        self.blind_index = (self.blind_index + 1) % len(self.players)
        self.deck = self.get_new_deck()
        self.table.cards = []
        for player in self.players.values():
            player.state = PlayerState.NOT_READY
            player.round_bet = 0
            player.cards = []

    def show_game(self):
        show = f"Bank: |{self.bank}|\n\n"
        show += "Table:\n"
        show += self.table.show_cards()
        show += "\n"
        
        return show

    def show_players_after_game(self):
        show = ""
        for player in self.players.values():
            if player.state == PokerPlayerState.FOLDED:
                continue
            show += f"{player.player_info.name}\n"
            show += player.show_cards()
            show += "\n"
        return show

    def get_player_by_index(self, index):
        return list(self.players.values())[(index) % len(self.players)]

    def draw_cards(self, number: int):
        self.draw_card()
        for i in range(number):
            self.table.draw_card(self)

    def get_blinds(self):
        self.round_bet = self.blind
        self.raise_bet(self.blind, self.get_player_by_index(self.blind_index).player_info)
        self.raise_bet(self.blind // 2, self.get_player_by_index(self.blind_index + 1).player_info)
    
    def get_status_msg(self):
        message = f"There are now {len(self.players.values())} players in this game, listing:\n" + 25 * '-' + '\n'
        for player in self.players.values():
            message += (player.player_info.display_name + " - " + PokerPlayerState(player.state).name + "\n")
        return message + "The game will start rolling automatically after everyone is ready!"
    
    def get_banklist_msg(self):
        message = f"There is now {self.bank} in the BANK on the table!\n"
        message += f"There are now {len(self.players.values())} players in this game, showing their banks:\n" + 25 * '-' + '\n'
        for player in self.players.values():
            message += f"{player.player_info.display_name} ({PokerPlayerState(player.state).name}) - BANK: {player.bet.value}, ON THE TABLE: {player.round_bet}\n"
        return message

    def change_aces_value(self, cards: list[Card]) -> list[Card]:
        for card in cards:
            if card.value == 1:
                card.value = 14
        return cards

    def revert_aces_value(self, cards: list[Card]) -> list[Card]:
        for card in cards:
            if card.value == 14:
                card.value = 1
        return cards

    def sort_poker_cards(self, cards: list[Card]) -> list[Card]:
        return sorted(cards, key=lambda card: card.value, reverse=True)

    def determine_winner(self, players: list[CardPlayer]) -> list[CardPlayer]:     # use ranks and values to determine winner
        for player in players:
            player.cards = self.change_aces_value(player.cards)

        best_hands = {player: self.best_hand(player) for player in players}
        best_rank = best_hands[players[0]][0]
        best_players = [players[0]]

        for player in players:
            curr = best_hands[player][0]
            if curr > best_rank:
                best_players = [player]
                best_rank = curr
            elif curr == best_rank:
                best_players.append(player)

        if len(best_players) == 1:
            for player in players:
                player.cards = self.revert_aces_value(player.cards)
            return best_players
        
        res = self.resolve_even_rank(best_players, best_rank)
        for player in players:
            player.cards = self.revert_aces_value(player.cards)
        return res

    def best_hand(self, player: CardPlayer) -> tuple[int, list[int]]:   # TODO get best hand of player, not vals
        all_five_card_hands = combinations(player.cards, 5)
        return max(all_five_card_hands, key=self.get_hand_rank)

    def get_hand_rank(self, hand: list[Card]) -> tuple[int, list[int]]:
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
    
    def resolve_even_rank(self, players: list[tuple[CardPlayer, list[int]]], rank: int) -> list[CardPlayer]:
        card_combinations = {
            9: self.royal_flush,
            8: self.straight_flush,
            7: self.four_of_a_kind,
            6: self.full_house,
            5: self.flush,
            4: self.straight,
            3: self.three_of_a_kind,
            2: self.two_pair,
            1: self.one_pair,
            0: self.high_card
        }
        return card_combinations[rank](players)
    
    # !!! player.cards needs to be sorted and change ace value from 1 to 14 !!!
    def royal_flush(self, players: list[tuple[CardPlayer, list[int]]]) -> list[CardPlayer]:
        res = []

        for player in players:
            res.append(player[0])

        return res

    def straight_flush(self, players: list[tuple[CardPlayer, list[int]]]) -> list[CardPlayer]:
        res = []
        max_val = 2
        for player, curr_values in players:
            curr_max = curr_values[0]
            if curr_max > max_val:
                res = [player]
                max_val = curr_max
            elif curr_max == max_val:
                res.append(player)
        return res

    def four_of_a_kind(self, players: list[tuple[CardPlayer, list[int]]]) -> list[CardPlayer]:
        res = []
        max_val = 2
        max_div = 2
        for player, curr_values in players:
            curr_div = curr_values[0]
            if curr_div == curr_values[1]:
                curr_div = curr_values[4]

            poker = curr_values[2]
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

    def full_house(self, players: list[tuple[CardPlayer, list[int]]]) -> list[CardPlayer]:
        res = []
        max_trips = 2
        max_pair = 2
        for player, curr_value in players:
            trips = curr_value[2]
            pair = curr_value[0]
            if trips != curr_value[4]:
                pair = curr_value[4]

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

    def flush(self, players: list[tuple[CardPlayer, list[int]]]) -> list[CardPlayer]:
        res = []
        max_flush = [2, 2, 2, 2, 2]
        for player, curr_value in players:
            if curr_value > max_flush:
                res = [player]
                max_flush = curr_value
            elif curr_value == max_flush:
                    res.append(player)
        return res

    def straight(self, players: list[tuple[CardPlayer, list[int]]]) -> list[CardPlayer]:
        res = []
        max_val = 2
        for player, curr_value in players:
            curr_max = curr_value[0]
            if curr_value[1] == 5:  # if 14, 5, 4, 3, 2
                curr_max = 5

            if curr_max > max_val:
                res = [player]
                max_val = curr_max
            elif curr_max == max_val:
                res.append(player)
        return res

    def three_of_a_kind(self, players: list[tuple[CardPlayer, list[int]]]) -> list[CardPlayer]:
        res = []
        max_val = 2
        max_div = [2, 2]
        for player, curr_value in players:
            curr = {}
            for v in curr_value:
                curr[v] = curr.get(v, 0) + 1

            div = []
            for key, value in curr.items():
                if value != 3:
                    div.append(key)
            div.sort(reverse=True)
            trips = curr_value[2]

            if trips > max_val:
                res = [player]
                max_val = trips
                max_div = div
            elif trips == max_val:
                if div > max_div:
                    res = [player]
                    max_div = div
                elif div == max_div:
                    res.append(player)
        return res

    def two_pair(self, players: list[tuple[CardPlayer, list[int]]]) -> list[CardPlayer]:
        res = []
        max_val = [2, 2, 2]   # bigger pair, smaller pair, div
        
        for player, curr_value in players:
            curr = {}
            val = []
            for v in curr_value:
                curr[v] = curr.get(v, 0) + 1
            
            one = 0
            for key, value in curr.items():
                if value == 2:
                    val.append(key)
                else:
                    one = key

            val.sort(reverse=True)
            val.append(one)
            if val > max_val:
                res = [player]
                max_val = val
            elif val == max_val:
                res.append(player)
        return res

    def one_pair(self, players: list[tuple[CardPlayer, list[int]]]) -> list[CardPlayer]:
        res = []
        max_val = [2, 2, 2, 2]  # pair, div1, div2, div3
        for player, curr_value in players:
            curr = {}
            val = []
            for v in curr_value:
                curr[v] = curr.get(v, 0) + 1

            pair = []
            for key, value in curr.items():
                if value == 2:
                    pair.append(key)
                else:
                    val.append(key)
            
            val.sort(reverse=True)
            val = pair + val
            if val > max_val:
                res = [player]
                max_val = val
            elif val == max_val:
                res.append(player)
        return res

    def high_card(self, players: list[tuple[CardPlayer, list[int]]]) -> list[CardPlayer]:
        res = []
        max_val = [2, 2, 2, 2, 2]
        for player, curr_value in players:
            if curr_value > max_val:
                res = [player]
                max_val = curr_value
            elif curr_value == max_val:
                res.append(player)
        return res