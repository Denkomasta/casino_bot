from abc import ABC, abstractmethod
from enums import GameType, PlayerState, GameState

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

    def __init__(self, type: GameType):
        self.players = {}
        self.state = GameState.WAITING_FOR_PLAYERS
        self.type = type

class CardGame(Game):
    deck: list[Card]
    dealer: Dealer

