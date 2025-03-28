from enum import IntEnum

class E(IntEnum):
    SUCCESS = 0
    INV_STATE = -1
    INSUFFICIENT_FUNDS = -2
    OUT_OF_RANGE = -3
    INV_PLAYER = -4
    INV_BET = -5
    DUPLICITE_BET = -6
    BLOCKED = -7

class GameType(IntEnum):
    BLACKJACK = 0
    COINFLIP = 1
    POKER = 2
    ROULETTE = 3
    SLOTS = 4
    BACCARAT = 5
    ROLLTHEDICE = 6
    GUESSNUMBER = 7

class GameState(IntEnum):
    WAITING_FOR_PLAYERS = 0
    RUNNING = 1
    ENDED = 2

class PlayerState(IntEnum):
    PLAYING = 0
    READY = 1
    NOT_READY = 2
    FINISHED = 3

class PokerPlayerState(IntEnum):
    PLAYING = 0
    READY = 1
    NOT_READY = 2
    FINISHED = 3
    WAITING = 4
    CHECKED = 5
    RAISED = 6
    CALLED = 7
    FOLDED = 8
    ALL_IN_CALLED = 9
    ALL_IN_RAISED = 10

class CardSuits(IntEnum):
    UNSHOWABLE = -1
    HEARTS = 0
    DIAMONDS = 1
    CLUBS = 2
    SPADES = 3

class PlayerResult(IntEnum):
    DEFEAT = 0
    VICTORY = 1
    DRAW = 2
    UNDEFINED = 3

class BaccaratBetType(IntEnum):
    PLAYER = 0
    BANKER = 1
    TIE = 2
    UNDEFINED = 3

class CoinflipSides(IntEnum):
    HEADS = 1
    TAILS = 2

class RTDDoubles(IntEnum):
    ONES = -1
    TWOS = -2
    THREES = -3
    FOURS = -4
    FIVES = -5
    SIXES = -6

class PokerRoundStatus(IntEnum):
    CHECKED = 0
    RAISED = 1