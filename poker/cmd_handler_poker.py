from enums import GameType, GameState, E, PlayerState, BaccaratBetType, CoinflipSides
from typing import Callable, Awaitable
from discord.ext import commands
from base_classes import Game
from poker.poker import Poker
from cmd_handler import CommandHandler
import discord

class PokerCmdHandler(CommandHandler):

    @staticmethod
    async def cmd_run(game: Poker, source: commands.Context | discord.Interaction, args: list[str]) -> None:
        if (len(args) == 0):
            await CommandHandler.send("There is no argument, use \"!help poker\" to see the options", source)
        if (args[0] not in PokerCmdHandler.command_dict.keys()):
            await CommandHandler.send("Invalid argument, use \"!help poker\" to see the options", source)
        await PokerCmdHandler.command_dict[args[0]](game, source, args)
    
    command_dict: dict[str, Callable[[Poker, commands.Context | discord.Interaction, list[str]], Awaitable[None]]] = {
        #"restart": cmd_restart,
        "join": CommandHandler.cmd_join,
        "leave": CommandHandler.cmd_leave,
        #"start": cmd_start,
        "ready": CommandHandler.cmd_ready,
        "unready": CommandHandler.cmd_unready,
        #"hit": cmd_hit,
        #"stand": cmd_stand,
        "bet": CommandHandler.cmd_bet,
        #"status": cmd_status,
        #"betlist": cmd_betlist,
        #"help": cmd_help
    }