from enum import IntEnum

class E(IntEnum):
    SUCCESS = 0
    INV_STATE = -1
    INSUFFICIENT_FUNDS = -2
    OUT_OF_RANGE = -3
    INV_PLAYER = -4
    INV_BET = -5

class GameType(IntEnum):
    BLACKJACK = 0
    COINFLIP = 1
    POKER = 2
    ROULETTE = 3
    SLOTS = 4

class GameState(IntEnum):
    WAITING_FOR_PLAYERS = 0
    RUNNING = 1
    ENDED = 2

class PlayerState(IntEnum):
    PLAYING = 0
    READY = 1
    NOT_READY = 2
    FINISHED = 3