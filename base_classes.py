from abc import ABC, abstractmethod
from enums import GameType, PlayerState, GameState, PlayerResult, E
from database import Database
import discord

class Card:
    value: int
    suit: int
    showable: bool
    ascii: list[list[str]]

    def __init__(self, suit: int, value: int, show: bool= True):
        self.suit = suit
        self.value = value
        self.showable = show
        self.ascii = [
            ["┌","─","─","─","─","─","┐"],
            ["│","V"," "," "," "," ","│"],
            ["│"," "," ","S"," "," ","│"],
            ["│"," "," "," "," ","V","│"],
            ["└","─","─","─","─","─","┘"]
        ]
    
    def fill_ascii(self) -> None:
        suit = self.suit
        value = self.value

        if (not self.showable):
            suit = -1
            value = -1

        suits = {0: "♥", 1: "♦", 2: "♣", 3: "♠", -1: "?"}
        values = {1: "A", 10: "1", 11: "J", 12: "Q", 13: "K", -1: "?"}

        if (value == 10):
            self.ascii[1][1] = "1"
            self.ascii[1][2] = "0"
            self.ascii[3][4] = "1"
            self.ascii[3][5] = "0"
            self.ascii[2][3] = suits.get(suit, "?")
            return

        self.ascii[1][1] = values.get(value, str(value))
        self.ascii[2][3] = suits.get(suit, "?")
        self.ascii[3][5] = values.get(value, str(value))
        

    def show_card(self) ->str:
        self.fill_ascii()
        show: str = ""
        for lst in self.ascii:
            show += "`"
            show += "".join(lst)
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
        for card in self.cards:
            card.fill_ascii()
        for index in range(5):
            show += "`"
            for card in self.cards:
                show += "".join(card.ascii[index])
            show += "`"
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
        return [Card(suit, value, True) for suit in range(4) for value in range(1, 14)]

