from enums import GameType, GameState, E, PlayerState, BaccaratBetType, CoinflipSides
from typing import Callable, Awaitable
from discord.ext import commands
from base_classes import Game
from blackjack.black_jack import BlackJack
from baccarat.baccarat import Baccarat
from rng_games.rng_games import RNGGame, RNGBet, Coinflip, RollTheDice, GuessTheNumber
from poker.poker import Poker
from abc import ABC, abstractmethod
import traceback
from database import Database

import discord

class CommandHandler:
    @staticmethod
    async def cmd(game: Game, source: commands.Context | discord.Interaction, args: list[str]) -> None:
        #jenom aby mě nebuzeroval
        pass
    
    @staticmethod
    async def send(message: str, source: commands.Context | discord.Interaction, ephemeral=False, delete_after=None):
        if (isinstance(source, discord.Interaction)):
            await source.response.send_message(message, ephemeral=ephemeral, delete_after=delete_after)
        else:
            await source.send(message)

    @staticmethod
    def get_id(source: commands.Context | discord.Interaction):
        if (isinstance(source, discord.Interaction)):
            return source.user.id
        else:
            return source.author.id
        
    @staticmethod
    def get_name(source: commands.Context | discord.Interaction):
        if (isinstance(source, discord.Interaction)):
            return source.user.name
        else:
            return source.author.name

    @staticmethod
    def get_info(source: commands.Context | discord.Interaction):
        if (isinstance(source, discord.Interaction)):
            return source.user
        else:
            return source.author
    
    @staticmethod
    async def join(source: commands.Context | discord.Interaction, games: dict[tuple[int, int], Game], data: Database):
        try:
            options = [discord.SelectOption(label=GameType(type).name, value=f"{type}") for id, type in games.keys() if id == source.channel.id]
            if len(options) == 0:
                from ui import GeneralCreateUI
                options = [discord.SelectOption(label=GameType(type).name, value=f"{type}") for type in GameType if (source.channel.id, type) not in games.keys()]
                await source.channel.send("There is no existing game in the channel currently", view=GeneralCreateUI(games, data, options))
                return
            from ui import GeneralJoinUI
            await source.channel.send(view=GeneralJoinUI(games, options))
        except:
            traceback.print_exc()

    @staticmethod
    async def play(source: commands.Context | discord.Interaction, games: dict[tuple[int, int], Game], data: Database):
        try:
            from ui import GeneralPlayUI
            await source.channel.send(view=GeneralPlayUI(games, data))
        except:
            traceback.print_exc()

    @staticmethod
    async def create(source: commands.Context | discord.Interaction, games: dict[tuple[int, int], Game], data: Database):
        try:
            options = [discord.SelectOption(label=GameType(type).name, value=f"{type}") for type in GameType if (source.channel.id, type) not in games.keys()]
            if len(options) == 0:
                from ui import GeneralJoinUI
                options = [discord.SelectOption(label=GameType(type).name, value=f"{type}") for id, type in games.keys() if id == source.channel.id]
                await source.channel.send("All types of games already exists in this channel", view=GeneralJoinUI(games, options))
                return
            from ui import GeneralCreateUI
            await source.channel.send(view=GeneralCreateUI(games, data, options=options))
        except:
            traceback.print_exc()

    @staticmethod
    async def cmd_create(source: commands.Context | discord.Interaction, games: dict[(int, int), Game], data: Database, type: GameType):
        if ((CommandHandler.get_id(source), type) in games.keys()):
            await CommandHandler.send(f'Game already exists in your channel, use \'exit\' first', source)
            return
        game: Game
        match type:
            case GameType.BACCARAT:
                game = Baccarat(data, source.channel)
            case GameType.BLACKJACK:
                game = BlackJack(data, source.channel)
            case GameType.COINFLIP:
                game = Coinflip(data, source.channel)
            case GameType.ROLLTHEDICE:
                game = RollTheDice(data, source.channel)
            case GameType.GUESSNUMBER:
                game = GuessTheNumber(data, source.channel)
            case GameType.POKER:
                game = Poker(data, source.channel)
            case _:
                await CommandHandler.send("Not implemented yet", source)
                return
        games[(source.channel.id, type)] = game
        await CommandHandler.send(f'Game of {GameType(type).name} was created', source)
        from ui import JoinUI
        await source.channel.send(view=JoinUI(games[(source.channel.id, type)], type))

    @staticmethod
    async def cmd_exit(source: commands.Context | discord.Interaction, games: dict[tuple[int, int], Game], data: Database, type: GameType):
        if ((source.channel.id, type) not in games.keys()):
            await CommandHandler.send(f'Game of {GameType(type).name} does not exist', source, ephemeral=True)
            return
        games.pop((source.channel.id, GameType.BLACKJACK))
        await source.channel.send(f'Game of {GameType(type).name} was exited')
        return


    @staticmethod
    async def cmd_join(game: Game, source: commands.Context | discord.Interaction, args: list[str]):
        """Handles the 'join' command."""
        if (game.state == GameState.RUNNING):
            await CommandHandler.send(f"Game is running, wait for the end", source)
            return
        if (game.add_player(CommandHandler.get_info(source)) == E.INV_STATE):
             await CommandHandler.send(f"Player {CommandHandler.get_name(source)} is already in the game!", source, ephemeral=True)
             return
        await game.channel.send(f"Player {CommandHandler.get_name(source)} joined the game of {GameType(game.type).name}!")
        if len(args) > 1:
            match game.type:
                case GameType.BACCARAT:
                    from baccarat.cmd_handler_baccarat import BaccaratCmdHandler
                    await BaccaratCmdHandler.cmd_bet(game, source, args)
                case GameType.BLACKJACK:
                    await CommandHandler.cmd_bet(game, source, args)

    @staticmethod
    async def cmd_bet(game: Game, source: commands.Context | discord.Interaction, args: list[str]):
        """Handles the 'bet' command."""
        if (len(args) != 2):
            await CommandHandler.send(f"Invalid number of arguments: is {len(args)} should be 2", source)
            return
        try:
            bet = int(args[1])
        except Exception as _:
            await CommandHandler.send(f"Argument [bet] has to be number, try again", source, ephemeral=True)
            return
        game.change_bet(CommandHandler.get_info(source), bet)
        await CommandHandler.send(f"{CommandHandler.get_name(source)}'s bet changed to {bet}", source, ephemeral=True)

    @staticmethod
    async def cmd_leave(game: Game, source: commands.Context | discord.Interaction, args: list[str]):
        """Handles the 'leave' command."""
        if (len(args) != 1):
            await CommandHandler.send(f"Invalid number of arguments: is {len(args)} should be 1", source)
            return
        if (game.remove_player(CommandHandler.get_info(source)) == E.INV_STATE):
             await CommandHandler.send(f"Player {CommandHandler.get_name(source)} is not in the game!", source, ephemeral=True)
             return
        await CommandHandler.send(f"Player {CommandHandler.get_name(source)} left the game!", source, ephemeral=True)
        if (len(game.players) == 0):
            #TODO exit game
            pass


    @staticmethod
    async def cmd_ready(game: Game, source: commands.Context | discord.Interaction, args: list[str]):
        if (len(args) != 1):
            await CommandHandler.send(f"Invalid number of arguments: is {len(args)} should be 1", source)
            return
        if (game.state == GameState.RUNNING):
            await CommandHandler.send(f"Game is already running", source, ephemeral=True)
            return
        cmd_status: E = game.ready_up(CommandHandler.get_info(source))
        if cmd_status == E.INV_PLAYER:
            await CommandHandler.send(f"{CommandHandler.get_info(source).mention} You are not in the game! You must use !{GameType(game.type).name.lower()} join to participate", source, ephemeral=True)
            return
        if cmd_status == E.INV_STATE:
            await CommandHandler.send(f"{CommandHandler.get_info(source).mention} You are already ready for the roll!", source, ephemeral=True)
            return
        await CommandHandler.send(f"Player {CommandHandler.get_info(source).display_name} is ready for the roll!", source, ephemeral=True)
        if (game.are_players_ready()):
            from ui import StartUI
            await game.channel.send(view=StartUI(game))
        

    @staticmethod
    async def cmd_unready(game: Game, source: commands.Context | discord.Interaction, args: list[str]):
        if (len(args) != 1):
            await CommandHandler.send(f"Invalid number of arguments: is {len(args)} should be 1", source)
            return
        if (game.state == GameState.RUNNING):
            await CommandHandler.send(f"Game is already running", source, ephemeral=True)
            return
        cmd_status: E = game.unready(CommandHandler.get_info(source))
        if cmd_status == E.INV_PLAYER:
            await CommandHandler.send(f"{CommandHandler.get_info(source).mention} You are not in the game! You must use !{GameType(game.type).name.lower()} join to participate", source, ephemeral=True)
            return
        await CommandHandler.send(f"Player {CommandHandler.get_info(source).display_name} needs more time to think and is now not ready", source)
