from abc import ABC, abstractmethod
from enums import GameType, PlayerState, GameState, PlayerResult, E, CardSuits
from database import Database
import discord
from ascii_obj import Ascii

class Card:
    value: int
    suit: CardSuits
    showable: bool

    def __init__(self, suit: CardSuits, value: int, show: bool= True):
        self.suit = suit
        self.value = value
        self.showable = show
    
    def show_card(self) ->str:
        ascii_card = Ascii.get_card(self.suit, self.value, self.showable)
        show: str = ""
        for line in ascii_card:
            show += "`"
            show += "".join(line)
            show += "`"
            show += "\n"
        return show

class Bet:
    value: int
    result: int
    winning: int

    def __init__(self, value: int):
        self.value = value
        self.result = PlayerResult.UNDEFINED
        self.winning = 0

class Player(ABC):
    bet: Bet
    state: PlayerState
    player_info: discord.User | discord.Member

    def __init__(self, player_info: discord.User | discord.Member, bet: int):
        self.bet = Bet(bet)
        self.state = PlayerState.NOT_READY
        self.player_info = player_info

class CardPlayer(Player):
    cards: list[Card]

    def __init__(self, player_info: discord.User | discord.Member, bet: int):
        super().__init__(player_info, bet)
        self.cards = []

    def show_cards(self) -> str:
        show = ""
        for index in range(5):
            #show += "`"
            for card in self.cards:
                show += "".join(Ascii.get_card(card.suit, card.value, card.showable)[index])
            #show += "`"
            show += "\n"
        return show

class Game(ABC):
    type: GameType
    players: dict[int, Player]
    state: GameState
    data: Database

    def __init__(self, data: Database, type: GameType):
        self.players = {}
        self.state = GameState.WAITING_FOR_PLAYERS
        self.type = type
        self.data = data

    def add_player(self,  player_info: discord.User | discord.Member, bet: int=0) -> E:
        if (self.players.get(player_info.id) is not None):
            return E.INV_STATE
    
        match self.type:
            case GameType.BLACKJACK:
                from black_jack import BlackJackPlayer
                self.players[player_info.id] = BlackJackPlayer(player_info, bet)
        return E.SUCCESS
    
    def remove_player(self, player_info: discord.User | discord.Member) -> E:
        if (self.players.get(player_info.id) is None):
            return E.INV_STATE
        
        self.players.pop(player_info.id)
        return E.SUCCESS
    
    def are_players_ready(self):
        for player in self.players.values():
            if (player.state != PlayerState.READY):
                return False
        return True

    def change_bet(self, player_info: discord.User | discord.Member, bet: int) -> None:
        self.players[player_info.id].bet.value = bet

    def collect_bets(self) -> None:
        for player in self.players.values():
            if (player.bet.value > 0):
                self.data.change_player_balance(player.player_info.id, -player.bet.value)
    
    def give_winnings(self) -> None:
        for player in self.players.values():
            if (player.bet.winning > 0):
                self.data.change_player_balance(player.player_info.id, player.bet.winning)

class CardGame(Game):
    deck: list[Card]

    def __init__(self, data: Database, type: GameType):
        super().__init__(data, type)
        self.deck = self.get_new_deck()

    def get_new_deck(self) -> list[Card]:
        return [Card(suit, value, True) for suit in CardSuits if suit != CardSuits.UNSHOWABLE for value in range(1, 14)]

