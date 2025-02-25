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
import global_vars

import discord

class CommandHandler:
    @staticmethod
    async def cmd(game: Game, source: commands.Context | discord.Interaction, args: list[str]) -> None:
        #jenom aby mě nebuzeroval
        pass
    
    @staticmethod
    async def send(message: str, source: commands.Context | discord.Interaction, ephemeral=False, delete_after=None, view=None):
        if view is None:
            view=discord.ui.View()
        if (isinstance(source, discord.Interaction)):
            await source.response.send_message(message, ephemeral=ephemeral, delete_after=delete_after, view=view)
        else:
            await source.send(message, view=view)

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
    async def join(source: commands.Context | discord.Interaction):
        try:
            options = [discord.SelectOption(label=GameType(type).name, value=f"{type}") for id, type in casino_bot.Games.keys() if id == source.channel.id]
            if len(options) == 0:
                from ui import GeneralCreateUI
                options = [discord.SelectOption(label=GameType(type).name, value=f"{type}") for type in GameType if (source.channel.id, type) not in casino_bot.Games.keys()]
                await CommandHandler.send("There is no existing game in the channel currently", source, view=GeneralCreateUI(options), ephemeral=True)
                return
            from ui import GeneralJoinUI
            await CommandHandler.send("", source, view=GeneralJoinUI(options), ephemeral=True)
        except:
            traceback.print_exc()

    @staticmethod
    async def play(source: commands.Context | discord.Interaction):
        try:
            from ui import GeneralPlayUI
            await CommandHandler.send("", source, ephemeral=True, view=GeneralPlayUI())
        except:
            traceback.print_exc()

    @staticmethod
    async def create(source: commands.Context | discord.Interaction):
        try:
            options = [discord.SelectOption(label=GameType(type).name, value=f"{type}") for type in GameType if (source.channel.id, type) not in global_vars.Games.keys()]
            if len(options) == 0:
                from ui import GeneralJoinUI
                options = [discord.SelectOption(label=GameType(type).name, value=f"{type}") for id, type in global_vars.Games.keys() if id == source.channel.id]
                await CommandHandler.send("All types of games already exists in this channel", source, ephemeral=True, view=GeneralJoinUI(options))
                return
            from ui import GeneralCreateUI
            await CommandHandler.send("", source, ephemeral=True, view=GeneralCreateUI(options=options))
        except:
            traceback.print_exc()

    @staticmethod
    async def balance(source: commands.Context | discord.Interaction):
        await CommandHandler.send(f'{global_vars.Data.get_player_name(CommandHandler.get_id(source))} has casino balance: {global_vars.Data.get_player_balance(CommandHandler.get_id(source))}', source, ephemeral=True, delete_after=5)


    @staticmethod
    async def drop(source: commands.Context | discord.Interaction):
        import time
        if global_vars.Data.data.get(str(CommandHandler.get_id(source))) is None:
            await CommandHandler.send(f"{CommandHandler.get_info(source).mention} You must be a member of {casino_bot.BOTNAME} to participate!", source, ephemeral=True, delete_after=5)
            return
        time_since_last = time.time() - global_vars.Data.get_last_drop(CommandHandler.get_id(source))
        if time_since_last < 86400:
            time_to_next = 86400 - time_since_last
            await CommandHandler.send(f"You'll be able to get your next drop in {int(time_to_next // 3600)} hours and {int((time_to_next // 60) % 60)} minutes", source, ephemeral=True, delete_after=5)
            return
        global_vars.Data.change_player_balance(CommandHandler.get_id(source), 2000)
        global_vars.Data.update_last_drop(CommandHandler.get_id(source))
        await CommandHandler.send(f"{CommandHandler.get_info(source).mention} You got your daily drop of 2000 coins!", source, ephemeral=True, delete_after=5)

    @staticmethod
    async def leaderboard(source: commands.Context | discord.Interaction):
        header = f"{'Rank':<5} {'Name':<25} {'Balance':<10}\n"
        header += "-" * 40 + "\n"
        
        rows = ""
        for i, (name, balance) in enumerate(global_vars.Data.get_leaderboard()):
            rank = i + 1
            name = name[:25]
            rows += f"{rank:<5} {name:<25} {balance:<10}\n"

        table = header + rows 
        await CommandHandler.send(f"```\n{table}\n```", source)    # Code formatting

    @staticmethod
    async def cmd_create(source: commands.Context | discord.Interaction, type: GameType):
        try:
            if ((source.channel.id, type) in global_vars.Games.keys()):
                await CommandHandler.send(f'Game of {GameType(type).name} already exists in your channel', source)
                return
            
            if type not in CommandHandler.create_dict.keys():
                await CommandHandler.send(f"Game of {GameType(type).name} not implemented yet", source, ephemeral=True)
                return
            game: Game = CommandHandler.create_dict[type](source.channel)
           
            global_vars.Games[(source.channel.id, type)] = game
            if game.type == GameType.POKER:
                from poker.ui_poker import PokerSettingsUI
                view = PokerSettingsUI(game)
                await CommandHandler.send("You can now change your game's settings and click on \"ALL SET\"", source, view=view, ephemeral=True)
                await view.wait()
            await game.channel.send(f'Game of {GameType(type).name} was created')
            from ui import JoinUI
            await game.channel.send(view=JoinUI(global_vars.Games[(source.channel.id, type)], type))
        except:
            traceback.print_exc()

    @staticmethod
    async def cmd_exit(source: commands.Context | discord.Interaction, game: Game):
        if ((game.channel.id, game.type) not in global_vars.Games.keys()):
            await CommandHandler.send(f'Game of {GameType(game.type).name} does not exist', source, ephemeral=True)
            return
        global_vars.Games.pop((game.channel.id, game.type))
        await game.channel.send(f'Game of {GameType(game.type).name} was exited')
        return

    @staticmethod
    async def cmd_join(game: Game, source: commands.Context | discord.Interaction, args: list[str]):
        """Handles the 'join' command."""
        try:
            if (game.state == GameState.RUNNING):
                await CommandHandler.send(f"Game is running, wait for the end", source)
                return
            
            status = game.add_player(CommandHandler.get_info(source))
            from ui import GameUserInterface
            bet_ui: GameUserInterface = CommandHandler.get_game_ui(game)
            if (status == E.INV_STATE):
                await CommandHandler.send(f"Player {CommandHandler.get_name(source)} is already in the game!", source, ephemeral=True, view=bet_ui)
                return
            if status == E.BLOCKED:
                await CommandHandler.send(f"{CommandHandler.get_info(source).mention} The game has now joining disabled!", source, ephemeral=True)
                return
            await game.channel.send(f"Player {CommandHandler.get_name(source)} joined the game of {GameType(game.type).name}!")
            await CommandHandler.send("", source, ephemeral=True, view=bet_ui)
            
            if len(args) > 1:
                match game.type:
                    case GameType.BACCARAT:
                        from baccarat.cmd_handler_baccarat import BaccaratCmdHandler
                        await BaccaratCmdHandler.cmd_bet(game, source, args)
                    case GameType.BLACKJACK:
                        await CommandHandler.cmd_bet(game, source, args)
        except:
            traceback.print_exc()

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
        if game.type == GameType.POKER and (not game.banks_changeable and not game.first_round):
            await CommandHandler.send(f"{CommandHandler.get_info(source).mention} The game has now betting disabled!")
            return
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
            await CommandHandler.cmd_exit(source, game)
            return
        if (game.are_players_ready()):
            from ui import StartUI
            await game.channel.send(view=StartUI(game))

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


    @staticmethod
    def get_game_ui(game: Game):
        bet_ui = None
        match game.type:
                case GameType.BACCARAT:
                    from baccarat.ui_baccarat import BaccaratBetUI
                    bet_ui = BaccaratBetUI(game)
                case GameType.COINFLIP:
                    from rng_games.ui_rng import CoinflipUserInterface
                    bet_ui = CoinflipUserInterface(game)
                case GameType.ROLLTHEDICE:
                    from rng_games.ui_rng import RollTheDiceUserInterface
                    bet_ui = RollTheDiceUserInterface(game)
                case GameType.GUESSNUMBER:
                    from rng_games.ui_rng import GuessNumberUserInterface
                    bet_ui = GuessNumberUserInterface(game)
                case GameType.POKER:
                    from poker.ui_poker import PokerBetUI
                    bet_ui = PokerBetUI(game)
                case _:
                    from ui import BetUI
                    bet_ui = BetUI(game)
        return bet_ui


    create_dict = {
        GameType.BACCARAT: Baccarat,
        GameType.BLACKJACK: BlackJack,
        GameType.COINFLIP: Coinflip,
        GameType.GUESSNUMBER: GuessTheNumber,
        GameType.POKER: Poker,
        GameType.ROLLTHEDICE: RollTheDice,
    }

    """
    from baccarat.ui_baccarat import BaccaratBetUI
    from rng_games.ui_rng import CoinflipUserInterface, RollTheDiceUserInterface, GuessNumberUserInterface
    from poker.ui_poker import PokerBetUI
    betui_dict = {
        GameType.BACCARAT: BaccaratBetUI,
        GameType.COINFLIP: CoinflipUserInterface,
        GameType.GUESSNUMBER: GuessNumberUserInterface,
        GameType.POKER: PokerBetUI,
        GameType.ROLLTHEDICE: RollTheDiceUserInterface,
    }
    """