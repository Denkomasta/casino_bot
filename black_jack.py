from random import randrange
from typing import Callable, Awaitable
import discord
from discord.ext import commands
from enums import E, GameState, PlayerState, GameType, PlayerResult
from database import Database
from base_classes import CardGame, CardPlayer, Card, Player

class BlackJackPlayer(CardPlayer):

    def __init__(self, player_info: discord.User | discord.Member, bet: int=0):
        super().__init__(player_info, bet)
    
    def count_cards(self) -> int:
        count_a1: int = 0
        count_a11: int = 0
        for card in self.cards:
            if (card.showable):
                count_a1 += card.value if card.value <= 10 else 10
                count_a11 += 10 if card.value > 10 else 11 if card.value == 1 else card.value
        if (count_a11 > 21):
            return count_a1
        return count_a11
    
    def show_player_header(self):
        return f"{self.player_info.name} |{self.count_cards()}|"
    
    def show_player(self):
        return f"{self.show_player_header()}\n{self.show_cards()}"

class BlackJackDealer(BlackJackPlayer):
    cards: list[Card]
    name: str

    def __init__(self):
        self.cards = []
        self.name = "Dealer"

    def show_player_header(self):
        return f"{self.name} |{self.count_cards()}|"


class BlackJack(CardGame):
    dealer: BlackJackDealer

    def __init__(self, data: Database):
        super().__init__(data, GameType.BLACKJACK)
        self.dealer = BlackJackDealer()
        self.players = {}
        self.state = GameState.WAITING_FOR_PLAYERS
        
    def show_game(self)-> str:
        show: str = ""
        show += f"{self.dealer.show_player_header()}\n{self.dealer.show_cards()}\n"
        for player in self.players.values():
            show += f"{player.show_player_header()}\n{player.show_cards()}\n"
        return show

    def deal_cards(self) -> None:
        hidden_card: Card = self.deck.pop(randrange(len(self.deck)))
        hidden_card.showable = False
        self.dealer.cards.append(hidden_card)
        for _ in range(2):
            for player in self.players.values():
                player.cards.append(self.draw_card())
        self.dealer.cards.append(self.deck.pop(randrange(len(self.deck))))


    def player_hit(self, player_info: discord.User | discord.Member) -> E:
        player: BlackJackPlayer = self.players[player_info.id]
        if (player.state != PlayerState.PLAYING):
            return E.INV_STATE
        card: Card = self.draw_card()
        player.cards.append(card)
        if (player.count_cards() == 21):
            player.state = PlayerState.FINISHED
        if (player.count_cards() > 21):
            player.state = PlayerState.FINISHED
        return E.SUCCESS
    
    def is_everyone_finished(self) -> bool:
        result: bool = True
        for player in self.players.values():
            result = result and player.state == PlayerState.FINISHED
        return result
    
    def player_stand(self, player_info: discord.User | discord.Member) -> E:
        player: BlackJackPlayer = self.players[player_info.id]
        if (player.state != PlayerState.PLAYING):
            return E.INV_STATE
        player.state = PlayerState.FINISHED
        return E.SUCCESS
    
    def dealers_turn(self):
        for card in self.dealer.cards:
            card.showable = True
        while (self.dealer.count_cards() < 17):
            self.dealer.cards.append(self.draw_card())

    def evaluate(self) -> None:
        dealers_count: int = self.dealer.count_cards()
        for player in self.players.values():
            player_count: int = player.count_cards()
            if (player_count > 21):
                player.bet.result = PlayerResult.DEFEAT
                player.bet.winning = 0
                continue
            if (player_count == 21):
                player.bet.result = PlayerResult.VICTORY
                player.bet.winning = player.bet.value * 2
                continue
            if (dealers_count > 21 or player_count > dealers_count):
                player.bet.result = PlayerResult.VICTORY
                player.bet.winning = player.bet.value * 2
                continue
            if (dealers_count > player_count):
                player.bet.result = PlayerResult.DEFEAT
                player.bet.winning = 0
                continue
            player.bet.result = PlayerResult.DRAW
            player.bet.winning = player.bet.value
    
    def show_results(self) -> str:
        show: str = ""
        for player in self.players.values():
            result = player.bet.result
            income = player.bet.winning
            match result:
                case PlayerResult.VICTORY:
                    show += f"{player.player_info.name}: You won! Your bet was {player.bet.value}, you won {income}.\n"
                case PlayerResult.DEFEAT:
                    show += f"{player.player_info.name}: You lost. Your lost your bet of {player.bet.value}.\n"
                case PlayerResult.DRAW:
                    show += f"{player.player_info.name}: Draw. Your bet of {player.bet.value} has been returned.\n"
        return show
    
    def round_restart(self):
        self.deck = self.get_new_deck()
        self.dealer.cards = []
        self.state = GameState.WAITING_FOR_PLAYERS
        for player in self.players.values():
            player.state = PlayerState.NOT_READY
            player.bet.result = PlayerResult.UNDEFINED
            player.bet.winning = 0
            player.cards = []

    def show_players_by_state(self, state: PlayerState) -> str:
        show: str = ""
        for player in self.players.values():
            if (player.state == state):
                show += f"{player.player_info.name}\n"
        return show

    def game_start(self):
        self.collect_bets()
        self.deal_cards()
        self.state = GameState.RUNNING
        for player in self.players.values():
            player.state = PlayerState.PLAYING
    
    def game_finish(self):
        self.dealers_turn()
        self.evaluate()
        self.give_winnings()
        self.state = GameState.ENDED

    def game_restart(self):
        self.deck = self.get_new_deck()
        self.dealer.cards = []
        self.players = {}
        self.state = GameState.WAITING_FOR_PLAYERS

    def check_blackjack(self) -> None:
        for player in self.players.values():
            if (player.count_cards() == 21):
                player.state = PlayerState.FINISHED



    