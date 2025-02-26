from random import randrange
from typing import Callable, Awaitable
import discord
from discord.ext import commands
from enums import E, GameState, PlayerState, GameType, PlayerResult, CardSuits, PokerRoundStatus, PokerPlayerState
from database import Database
from base_classes import CardGame, CardPlayer, Card, Player
from itertools import combinations
from collections import Counter
from ascii_obj import Ascii
import traceback

class PokerPlayer(CardPlayer):
    def __init__(self, player_info):
        super().__init__(player_info)
        self.round_bet = 0
        self.game_bet = 0
        self.eval_cards: list[Card] = []

class PokerPot:
    def __init__(self):
        self.bank = 0
        self.players: list[Player] = []
        self.winners: list[Player] = []

class PokerTable(CardPlayer):

    def __init__(self):
        self.cards = []

    def draw_card(self, game: CardGame):
        self.cards.append(game.draw_card())


class Poker(CardGame):
    
    def __init__(self,channel: discord.TextChannel):
        super().__init__(channel, GameType.POKER)
        self.table: PokerTable = PokerTable()
        self.blind = 20
        self.blind_index = 0
        self.blind_increase = 10
        self.round_bet = 0
        self.pots: dict[int, PokerPot] = {}
        self.joinable = True
        self.banks_changeable = True
        self.preset_bank: int | None = None
        self.first_round = True
        self.winner_rank = -1
        self.winner_cards = []
    
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

    def divide_pots(self):
        sorted_by_round_bets = sorted(self.players.values(), key=lambda player: player.game_bet)
        for player in sorted_by_round_bets:
            if player.game_bet not in self.pots.keys() and player.state != PokerPlayerState.FOLDED:
                self.pots[player.game_bet] = PokerPot()
        
        for player in sorted_by_round_bets:
            for contribution, pot in self.pots.items():
                if player.game_bet >= contribution and player.state != PokerPlayerState.FOLDED:
                    pot.players.append(player)
        
        prev_contributions = 0
        for contribution, pot in self.pots.items():
            for player in sorted_by_round_bets:
                bet_to_add = min(contribution - prev_contributions, player.game_bet)
                pot.bank += bet_to_add
                player.game_bet -= bet_to_add
            prev_contributions = contribution


    def get_bank_size(self):
        bank = 0
        for player in self.players.values():
            bank += player.game_bet
        return bank

    def round_restart(self):
        self.round_bet = 0
        for player in self.players.values():
            player.round_bet = 0
            if player.state < PokerPlayerState.FOLDED: #state stays if FOLDER, ALL_IN_CALLED, ALL_IN_RAISED
                player.state = PokerPlayerState.WAITING

    def raise_bet(self, new_bet: int, player: discord.User | discord.Member):
        self.players[player.id].game_bet += new_bet - self.players[player.id].round_bet
        self.players[player.id].bet.value -= new_bet - self.players[player.id].round_bet
        self.players[player.id].round_bet = new_bet
        self.round_bet = new_bet


    def game_restart(self):
        self.blind_index = (self.blind_index + 1) % len(self.players)
        if self.blind_index == 0:
            self.blind += self.blind_increase
        self.deck = self.get_new_deck()
        self.table.cards = []
        self.pots = {}
        self.first_round = False
        for player in self.players.values():
            player.state = PlayerState.NOT_READY
            player.round_bet = 0
            player.cards = []
            player.eval_cards = []
            player.game_bet = 0

    def show_game(self):
        show = f"Bank: |{self.get_bank_size()}|\n\n"
        show += "Table: "
        for card in self.table.cards:
            show += Ascii.get_value_symbol(card.value) + Ascii.get_symbol(card.suit) + " "
        show += "\n"
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
    
    def is_instand_win(self):
        finished = 0
        for player in self.players.values():
            if player.state == PokerPlayerState.FOLDED:
                finished += 1
        return finished == len(self.players) - 1
    
    def insta_win(self):
        for player in self.players.values():
            if player.state != PokerPlayerState.FOLDED:
                player.bet.value += self.get_bank_size()
                pot = PokerPot()
                pot.winners.append(player)
                pot.bank = self.get_bank_size()
                pot.players.append(player)
                self.pots[self.get_bank_size()] = pot
                player.state = PokerPlayerState.FOLDED
                return
    
    def is_ready_to_get_all_cards(self):
        finished = 0
        for player in self.players.values():
            if player.state >= PokerPlayerState.FOLDED: #FOLDED/ALL_IN
                finished += 1
        return finished == len(self.players) - 1

    def draw_cards(self, number: int):
        self.draw_card()
        for i in range(number):
            self.table.draw_card(self)

    def get_blinds(self):
        self.round_bet = self.blind
        self.raise_bet(self.blind // 2, self.get_player_by_index(self.blind_index).player_info)
        self.raise_bet(self.blind, self.get_player_by_index(self.blind_index + 1).player_info)
    
    def get_status_msg(self):
        message = f"There are now {len(self.players.values())} players in this game, listing:\n" + 25 * '-' + '\n'
        for player in self.players.values():
            message += (player.player_info.display_name + " - " + PokerPlayerState(player.state).name + "\n")
        return message + "The game will start rolling automatically after everyone is ready!"
    
    def get_banklist_msg(self):
        message = f"There is now {self.get_bank_size()} in the BANK on the table!\n"
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
    
    def evaluate_winners(self):
        for pot in self.pots.values():
            best_rank, temp = self.determine_winner(pot.players)
            self.winner_rank = best_rank
            self.winner_cards = temp[0][1]
            pot.winners = [record[0] for record in temp]

            for winner in pot.winners:
                winner.bet.value += pot.bank // len(pot.winners)
    
    def show_winners(self):
        show = ""
        if len(self.pots) == 1:
            for pot in self.pots.values():
                if len(pot.winners) == 1:
                    show += f"WINNER is {pot.winners[0].player_info.name} winning bank of {pot.bank}\n"
                else:
                    show += "WINNERS are "
                    for index, player in enumerate(pot.winners):
                        if index != 0:
                            show += ", "
                        show += f"{player.player_info.name}"
                    show += f" each winning bank of {pot.bank // len(pot.winners)}\n"
            return show

        for index, pot in enumerate(self.pots.values()):
            show += f"Pot {index + 1}:\n"
            show += f"   Bank |{pot.bank}|\n"
            show += "Players: "
            for index, player in enumerate(pot.players):
                if index != 0:
                    show += ", "
                show += f"{player.player_info.name}"
            show +="\n\n"
            if len(pot.winners) == 1:
                show += f"WINNER is {pot.winners[0].player_info.name} winning bank of {pot.bank}\n\n"
            else:
                show += "WINNERS are "
                for index, player in enumerate(pot.winners):
                    if index != 0:
                        show += ", "
                    show += f"{player.player_info.name}"
                show += f" each winning bank of {pot.bank // len(pot.winners)}\n\n"
        return show

    def show_winning_combination(self) -> str:
        ranks = {
            9: "Royal Flush",
            8: "Straight Flush",
            7: "Four of a Kind",
            6: "Full House",
            5: "Flush",
            4: "Straight",
            3: "Three of a Kind",
            2: "Two Pair",
            1: "One Pair",
            0: "High Card"
        }
        res = ""
        res += f"Winning combination is **{ranks[self.winner_rank]}**:\nWith cards: "
        for card in self.winner_cards:
            res += Ascii.get_value_symbol(card.value) + Ascii.get_symbol(card.suit) + " "
        
        res += "\n"

        self.sort_poker_combination()
        for index in range(5):
            for card in self.winner_cards:
                res += "".join(Ascii.get_card(card.suit, card.value, card.showable)[index])
            res += "\n"

        self.winner_rank = -1
        self.winner_cards = []
        return res

    def sort_poker_cards(self, cards: list[Card]) -> list[Card]:
        return sorted(cards, key=lambda card: card.value, reverse=True)

    def determine_winner(self, players: list[PokerPlayer]) -> tuple[int, list[tuple[PokerPlayer, list[Card]]]]:     # use ranks and values to determine winner
        for player in players:
            if len(player.eval_cards) == 0:
                player.eval_cards = player.cards + self.table.cards
            player.eval_cards = self.change_aces_value(player.eval_cards)

        best_hands = {player: self.best_hand(player) for player in players}
        best_rank = best_hands[players[0]][0][0]
        best_players = []

        for player in players:
            for curr, vals, hand in best_hands[player]:
                if curr > best_rank:
                    best_players = [(player, vals, hand)]
                    best_rank = curr
                elif curr == best_rank:
                    best_players.append((player, vals, hand))

        for player in players:
            player.eval_cards = self.revert_aces_value(player.eval_cards)

        if len(best_players) == 1:
            return (best_rank, [(best_players[0][0], best_players[0][2])])
        return (best_rank, self.resolve_even_rank(best_players, best_rank))

    def best_hand(self, player: PokerPlayer) -> list[tuple[int, list[int], list[Card]]]:
        all_five_card_hands = combinations(player.eval_cards, 5)
        best_rank = 0
        res = []
        for h in all_five_card_hands:
            hand = list(h)
            rank, values = self.get_hand_rank(hand)
            if rank > best_rank:
                best_rank = rank
                res = [(rank, values, hand)]
            elif rank == best_rank:
                res.append((rank, values, hand))
        return res

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
    
    def resolve_even_rank(self, players: list[tuple[PokerPlayer, list[int], list[Card]]], rank: int) -> list[tuple[CardPlayer, list[Card]]]:
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
        temp = card_combinations[rank](players)
        seen = set()
        res = []
        for player, hand in temp:
            if player.player_info.id not in seen:
                res.append((player, hand))
                seen.add(player.player_info.id)
        return res

    # !!! player.cards needs to be sorted and change ace value from 1 to 14 !!!
    def royal_flush(self, players: list[tuple[PokerPlayer, list[int], list[Card]]]) -> list[tuple[CardPlayer, list[Card]]]:
        res = []

        for player in players:
            res.append(player[0], player[2])

        return res

    def straight_flush(self, players: list[tuple[PokerPlayer, list[int], list[Card]]]) -> list[tuple[CardPlayer, list[Card]]]:
        res = []
        max_val = 2
        for player, curr_values, hand in players:
            curr_max = curr_values[0]
            if curr_max > max_val:
                res = [(player, hand)]
                max_val = curr_max
            elif curr_max == max_val:
                res.append((player, hand))
        return res

    def four_of_a_kind(self, players: list[tuple[PokerPlayer, list[int], list[Card]]]) -> list[tuple[CardPlayer, list[Card]]]:
        res = []
        max_val = 2
        max_div = 2
        for player, curr_values, hand in players:
            curr_div = curr_values[0]
            if curr_div == curr_values[1]:
                curr_div = curr_values[4]

            poker = curr_values[2]
            if poker > max_val:
                res = [(player, hand)]
                max_val = poker
                max_div = curr_div
            elif poker == max_val:
                if curr_div > max_div:
                    res = [(player, hand)]
                    max_div = curr_div
                elif curr_div == max_div:
                    res.append((player, hand))
        return res

    def full_house(self, players: list[tuple[PokerPlayer, list[int], list[Card]]]) -> list[tuple[CardPlayer, list[Card]]]:
        res = []
        max_trips = 2
        max_pair = 2
        for player, curr_value, hand in players:
            trips = curr_value[2]
            pair = curr_value[0]
            if trips != curr_value[4]:
                pair = curr_value[4]

            if trips > max_trips:
                res = [(player, hand)]
                max_trips = trips
                max_pair = pair
            elif trips == max_trips:
                if pair > max_pair:
                    res = [(player, hand)]
                    max_pair = pair
                elif pair == max_pair:
                    res.append((player, hand))
        return res

    def flush(self, players: list[tuple[PokerPlayer, list[int], list[Card]]]) -> list[tuple[CardPlayer, list[Card]]]:
        res = []
        max_flush = [2, 2, 2, 2, 2]
        for player, curr_value, hand in players:
            if curr_value > max_flush:
                res = [(player, hand)]
                max_flush = curr_value
            elif curr_value == max_flush:
                    res.append((player, hand))
        return res

    def straight(self, players: list[tuple[PokerPlayer, list[int], list[Card]]]) -> list[tuple[CardPlayer, list[Card]]]:
        res = []
        max_val = 2
        for player, curr_value, hand in players:
            curr_max = curr_value[0]
            if curr_value[1] == 5:  # if 14, 5, 4, 3, 2
                curr_max = 5

            if curr_max > max_val:
                res = [(player, hand)]
                max_val = curr_max
            elif curr_max == max_val:
                res.append((player, hand))
        return res

    def three_of_a_kind(self, players: list[tuple[PokerPlayer, list[int], list[Card]]]) -> list[tuple[CardPlayer, list[Card]]]:
        res = []
        max_val = 2
        max_div = [2, 2]
        for player, curr_value, hand in players:
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
                res = [(player, hand)]
                max_val = trips
                max_div = div
            elif trips == max_val:
                if div > max_div:
                    res = [(player, hand)]
                    max_div = div
                elif div == max_div:
                    res.append((player, hand))
        return res

    def two_pair(self, players: list[tuple[PokerPlayer, list[int], list[Card]]]) -> list[tuple[CardPlayer, list[Card]]]:
        res = []
        max_val = [2, 2, 2]   # bigger pair, smaller pair, div
        
        for player, curr_value, hand in players:
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
                res = [(player, hand)]
                max_val = val
            elif val == max_val:
                res.append((player, hand))
        return res

    def one_pair(self, players: list[tuple[PokerPlayer, list[int], list[Card]]]) -> list[tuple[CardPlayer, list[Card]]]:
        res = []
        max_val = [2, 2, 2, 2]  # pair, div1, div2, div3
        for player, curr_value, hand in players:
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
                res = [(player, hand)]
                max_val = val
            elif val == max_val:
                res.append((player, hand))
        return res

    def high_card(self, players: list[tuple[PokerPlayer, list[int], list[Card]]]) -> list[tuple[CardPlayer, list[Card]]]:
        res = []
        max_val = [2, 2, 2, 2, 2]
        for player, curr_value, hand in players:
            if curr_value > max_val:
                res = [(player, hand)]
                max_val = curr_value
            elif curr_value == max_val:
                res.append((player, hand))
        return res

    def sort_poker_combination(self) -> None:
        hand = self.winner_cards
        values = {}
        for card in hand:
            values[card.value] = values.get(card.value, 0) + 1
        rank = self.winner_rank
        sorted_hand = []

        if rank == 9:  # Royal Flush
            sorted_hand = sorted(hand, key=lambda card: card.value, reverse=True)
        elif rank == 8:  # Straight Flush
            sorted_hand = sorted(hand, key=lambda card: card.value, reverse=True)
        elif rank == 7:  # Four of a Kind
            four_of_a_kind = [card for card in hand if values[card.value] == 4]
            kicker = [card for card in hand if values[card.value] != 4]
            sorted_hand = four_of_a_kind + kicker
        elif rank == 6:  # Full House
            three_of_a_kind = [card for card in hand if values[card.value] == 3]
            pair = [card for card in hand if values[card.value] == 2]
            sorted_hand = three_of_a_kind + pair
        elif rank == 5:  # Flush
            sorted_hand = sorted(hand, key=lambda card: card.value, reverse=True)
        elif rank == 4:  # Straight
            sorted_hand = sorted(hand, key=lambda card: card.value, reverse=True)
        elif rank == 3:  # Three of a Kind
            three_of_a_kind = [card for card in hand if values[card.value] == 3]
            kickers = [card for card in hand if values[card.value] != 3]
            sorted_hand = three_of_a_kind + sorted(kickers, key=lambda card: card.value, reverse=True)
        elif rank == 2:  # Two Pair
            pairs = [card for card in hand if values[card.value] == 2]
            kicker = [card for card in hand if values[card.value] != 2]
            sorted_hand = sorted(pairs, key=lambda card: card.value, reverse=True) + kicker
        elif rank == 1:  # One Pair
            pair = [card for card in hand if values[card.value] == 2]
            kickers = [card for card in hand if values[card.value] != 2]
            sorted_hand = pair + sorted(kickers, key=lambda card: card.value, reverse=True)
        else:  # High Card
            sorted_hand = sorted(hand, key=lambda card: card.value, reverse=True)

        self.winner_cards = sorted_hand
        