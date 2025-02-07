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