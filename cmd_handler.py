from enums import GameType, GameState, E, PlayerState, BaccaratBetType, CoinflipSides
from typing import Callable, Awaitable
from discord.ext import commands
from base_classes import Game
from blackjack.black_jack import BlackJack
from baccarat.baccarat import Baccarat
from rng_games.rng_games import RNGGame, Bet, Coinflip, RollTheDice, GuessTheNumber
from abc import ABC, abstractmethod
from database import Database

import discord

class CommandHandler:
    @staticmethod
    async def cmd(game: Game, source: commands.Context | discord.Interaction, args: list[str]) -> None:
        #jenom aby mě nebuzeroval
        pass
    
    @staticmethod
    async def send(message: str, source: commands.Context | discord.Interaction, ephemeral=False):
        if (isinstance(source, discord.Interaction)):
            await source.response.send_message(message, ephemeral=ephemeral)
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
    async def play(source: commands.Context | discord.Interaction, games: dict[tuple[int, int], Game], data: Database):
        options = [discord.SelectOption(label=GameType(type).name, value=f"{type}") for id, type in games.keys() if id == source.channel.id]
        if len(options) == 0:
            from ui import CreateUI
            await source.channel.send("There is no existing game in the channel currently", view=CreateUI(games, data, channel_id=CommandHandler.get_id(source)))
            return
        from ui import PlayUI
        await source.channel.send(view=PlayUI(games, options=options))

    @staticmethod
    async def create(source: commands.Context | discord.Interaction, games: dict[tuple[int, int], Game], data: Database):
        options = [discord.SelectOption(label=GameType(type).name, value=f"{type}") for type in GameType if (source.channel.id, type) not in games.keys()]
        if len(options) == 0:
            from ui import PlayUI
            await source.channel.send("All types of games already exists in this channel", view=PlayUI(games, channel_id=CommandHandler.get_id(source)))
            return
        from ui import CreateUI
        await source.channel.send(view=CreateUI(games, data, options=options))

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
            case _:
                await CommandHandler.send("Not implemented yet", source)
                return
        games[(source.channel.id, type)] = game
        await CommandHandler.send(f'Game was created, join the game using \'join -bet- -type-\' and start the game using \'start\'', source)
        from ui import JoinUI
        await source.channel.send(view=JoinUI(games[(source.channel.id, type)], type))


    @staticmethod
    async def cmd_join(game: Game, source: commands.Context | discord.Interaction, args: list[str]):
        """Handles the 'join' command."""
        if (len(args) > 2):
            await CommandHandler.send(f"Invalid number of arguments: is {len(args)} should be < 2", source)
            return
        if (game.state == GameState.RUNNING):
            await CommandHandler.send(f"Game is running, wait for the end", source)
            return
        bet = 0
        if (len(args) == 2):
            try:
                bet = int(args[1])
            except Exception as _:
                await CommandHandler.send(f"Argument [bet] has to be number, try again", source, ephemeral=True)
                return
        if (game.add_player(CommandHandler.get_info(source), bet) == E.INV_STATE):
             await CommandHandler.send(f"Player {CommandHandler.get_name(source)} is already in the game!", source, ephemeral=True)
             return
        await game.channel.send(f"Player {CommandHandler.get_name(source)} joined the game! {('Your bet is set to 0, use !bj bet [number] to change it.' if bet == 0 else f' Bet set to {bet}.')}")

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
