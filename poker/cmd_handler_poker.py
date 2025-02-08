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

    @staticmethod
    async def cmd_start(game: Poker, source: commands.Context | discord.Interaction, args: list[str]) -> None:
        pass

    @staticmethod
    async def cmd_check(game: Poker, source: commands.Context | discord.Interaction, args: list[str]) -> None:
        pass

    @staticmethod
    async def cmd_raise(game: Poker, source: commands.Context | discord.Interaction, args: list[str]) -> None:
        pass

    @staticmethod
    async def cmd_fold(game: Poker, source: commands.Context | discord.Interaction, args: list[str]) -> None:
        pass

    @staticmethod
    async def cmd_status(game: Poker, source: commands.Context | discord.Interaction, args: list[str]) -> None:
        pass

    # Only interaction
    @staticmethod
    async def cmd_show_cards(game: Poker, source: commands.Context | discord.Interaction, args: list[str]) -> None:
        pass
    
    command_dict: dict[str, Callable[[Poker, commands.Context | discord.Interaction, list[str]], Awaitable[None]]] = {
        "join": CommandHandler.cmd_join,
        "leave": CommandHandler.cmd_leave,
        "start": cmd_start,
        "ready": CommandHandler.cmd_ready,
        "unready": CommandHandler.cmd_unready,
        "check": cmd_check,
        "raise": cmd_raise,
        "fold": cmd_fold,
        "bet": CommandHandler.cmd_bet,
        "status": cmd_status,
    }