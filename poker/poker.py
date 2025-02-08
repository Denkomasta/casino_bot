from random import randrange
from typing import Callable, Awaitable
import discord
from discord.ext import commands
from enums import E, GameState, PlayerState, GameType, PlayerResult
from database import Database
from base_classes import CardGame, CardPlayer, Card, Player



class Poker(CardGame):
    
    def __init__(self, data: Database, channel: discord.TextChannel):
        super().__init__(data, channel, GameType.POKER)
        self.players = {}
        self.state = GameState.WAITING_FOR_PLAYERS
    
    def game_start(self):
        pass

    def game_finish(self):
        pass

    def play_round(self):
        pass

    def full_house(self, player: list[CardPlayer]) -> list[CardPlayer]:
        pass