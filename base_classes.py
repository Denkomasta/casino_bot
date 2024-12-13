from abc import ABC, abstractmethod
from enums import GameType, PlayerState, GameState
from database import Database

class Card:
    value: int
    suit: int
    ascii: list[list[str]]

class Dealer:
    cards: list[Card] #TBD

class Bet(ABC):
    value: int

class Player(ABC):
    bet: Bet
    state: PlayerState

class Game(ABC):
    type: GameType
    players: dict[str, Player]
    state: GameState
    data: Database

    def __init__(self, data: Database, type: GameType):
        self.players = {}
        self.state = GameState.WAITING_FOR_PLAYERS
        self.type = type
        self.data = data

class CardGame(Game):
    deck: list[Card]
    dealer: Dealer

