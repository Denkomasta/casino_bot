from enum import IntEnum

class E(IntEnum):
    SUCCESS = 0
    INV_STATE = -1

class GameType(IntEnum):
    BLACKJACK = 0
    COINFLIP = 1
    POKER = 2
    ROULETTE = 3
    SLOTS = 4

class GameState(IntEnum):
    WAITING_FOR_PLAYER = 0
    RUNNING = 1
    ENDED = 2
