import discord
import traceback
from discord.ext import commands
from base_classes import Game, Player, Bet
from enums import BaccaratBetType, GameType, E, GameState, PlayerState
from ui import UI, GameUserInterface
from poker.cmd_handler_poker import PokerCmdHandler

class PokerUI(GameUserInterface):
    def __init__(self, game: Game):
        super().__init__(game)

class Poker_ingame(UI):
    def __init__(self, game: Game, id: int):
        super().__init__(game)
        self.author_id = id