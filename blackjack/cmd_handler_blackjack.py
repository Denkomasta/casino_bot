from enums import GameType, GameState, E, PlayerState, BaccaratBetType, CoinflipSides
from typing import Callable, Awaitable
from discord.ext import commands
from base_classes import Game
from blackjack.black_jack import BlackJack
from cmd_handler import CommandHandler
import discord



class BlackJackCmdHandler(CommandHandler):

    @staticmethod
    async def cmd_run(game: BlackJack, source: commands.Context | discord.Interaction, args: list[str]) -> None:
        if (len(args) == 0):
            await CommandHandler.send("There is no argument, use \"!blackjack help\" to see the options", source)
        if (args[0] not in BlackJackCmdHandler.command_dict.keys()):
            await CommandHandler.send("Invalid argument, use \"!blackjack help\" to see the options", source)
        await BlackJackCmdHandler.command_dict[args[0]](game, source, args)

    @staticmethod
    async def cmd_restart(game: BlackJack, source: commands.Context | discord.Interaction, args: list[str]):
        """Handles the 'restart' command."""
        if (len(args) != 1):
            await CommandHandler.send(f"Invalid number of arguments: is {len(args)} should be 1", source)
            return
        if (game.state == GameState.RUNNING):
            await CommandHandler.send(f"Game is running right now, wait until it ends", source, ephemeral=True)
            return
        game.game_restart()
        await CommandHandler.send("Game was succesfully reseted, use \'join [bet]\' to enter the game", source)


    @staticmethod
    async def cmd_start(game: BlackJack, source: commands.Context | discord.Interaction, args: list[str]):
        if (len(args) != 1):
            await CommandHandler.send(f"Invalid number of arguments: is {len(args)} should be 1", source)
            return
        if (not game.are_players_ready()):
            await CommandHandler.send(f"Waiting for players:\n{game.show_players_by_state(PlayerState.NOT_READY)}", source)
            return
        game.game_start()
        await game.channel.send(f"```\n{game.show_game()}\n```")
        game.check_blackjack()
        if (game.is_everyone_finished()):
            await BlackJackCmdHandler.blackjack_finish(game, source)
            return
        else:
            from blackjack.ui_blackjack import BlackJackHitStandUI
            await game.channel.send(view=BlackJackHitStandUI(game))

    @staticmethod
    async def cmd_ready(game: BlackJack, source: commands.Context | discord.Interaction, args: list[str]):
        """Handles the 'ready' command."""    
        if (len(args) != 1):
            await CommandHandler.send(f"Invalid number of arguments: is {len(args)} should be 1", source)
            return
        if (game.state == GameState.RUNNING):
            await CommandHandler.send(f"Game is already running", source, ephemeral=True)
            return
        game.players[CommandHandler.get_id(source)].state = PlayerState.READY
        await CommandHandler.send(f"{CommandHandler.get_name(source)} is READY", source, ephemeral=True)
        if (game.are_players_ready()):
            from ui import StartUI
            await game.channel.send(view=StartUI(game))
    
    @staticmethod
    async def cmd_unready(game: BlackJack, source: commands.Context | discord.Interaction, args: list[str]):
        """Handles the 'ready' command."""    
        if (len(args) != 1):
            await CommandHandler.send(f"Invalid number of arguments: is {len(args)} should be 1", source)
            return
        if (game.state == GameState.RUNNING):
            await CommandHandler.send(f"Game is already running", source, ephemeral=True)
            return
        game.players[CommandHandler.get_id(source)].state = PlayerState.NOT_READY
        await CommandHandler.send(f"{CommandHandler.get_name(source)} is UNREADY", source, ephemeral=True)

    @staticmethod
    async def cmd_hit(game: BlackJack, source: commands.Context | discord.Interaction, args: list[str]):
        """Handles the 'hit' command."""
        if (len(args) != 1):
            await CommandHandler.send(f"Invalid number of arguments: is {len(args)} should be 1", source)
            return
        can_play: E = game.player_hit(CommandHandler.get_info(source))
        await game.channel.send(f"```{game.players[CommandHandler.get_id(source)].show_player()}```")
        if (game.is_everyone_finished()):
            await BlackJackCmdHandler.blackjack_finish(game, CommandHandler.get_info(source))
            return
        if (can_play == E.INV_STATE):
            await CommandHandler.send(f"{CommandHandler.get_name(source)} cannot hit anymore", source, ephemeral=True)
        
    @staticmethod
    async def cmd_stand(game: BlackJack, source: commands.Context | discord.Interaction, args: list[str]):
        """Handles the 'stand' command."""
        if (len(args) != 1):
            await CommandHandler.send(f"Invalid number of arguments: is {len(args)} should be 1", source)
            return
        if (game.player_stand(CommandHandler.get_info(source)) == E.INV_STATE):
            await CommandHandler.send(f"{CommandHandler.get_name(source)} already stands", source, ephemeral=True)
            return
        if (game.is_everyone_finished()):
            await BlackJackCmdHandler.blackjack_finish(game, CommandHandler.get_info(source))
            return
        await game.channel.send(f"{CommandHandler.get_name(source)} now stands")
        
    

    @staticmethod
    async def cmd_status(game: BlackJack, source: commands.Context | discord.Interaction, args: list[str]):
        """Handles the 'status' command."""
        if (len(args) != 1):
            await CommandHandler.send(f"Invalid number of arguments: is {len(args)} should be 1", source)
            return
        match (game.state):
            case GameState.WAITING_FOR_PLAYERS:
                await game.channel.send(f"```GAME IS WAITING TO START:\n\nPlayer that are not ready:\n{game.show_players_by_state(PlayerState.NOT_READY)}```")
                return
            case GameState.RUNNING:
                await game.channel.send(f"```GAME IS RUNNING:\n\nTable:\n{game.show_game()}\n\nStill active players:\n{game.show_players_by_state(PlayerState.PLAYING)}```")
                return
            case GameState.ENDED:
                await game.channel.send(f"```GAME ENDED:\n\nResults:\n{game.show_results()}```")
                return
        await CommandHandler.send("Command 'status' invoked.")

    @staticmethod
    async def cmd_help(game: BlackJack, source: commands.Context | discord.Interaction, args: list[str]):
        """Handles the 'help' command."""
        help: list[str] = [
            "create - creates a new game",
            "exit - destroys current game",
            "join [number] - adds you to current game, with instead of number use size of your bet",
            "ready - sets you READY",
            "unready - sets you UNREADY",
            #"start - starts the game if all players are READY",
            "hit - get a card",
            "stand - end your turn",
            "bet [number] - changes your bet",
            "restart - restarts the game, but players and bets will stay",
        ]
        await game.channel.send("```\n".join(help) + "```")

    @staticmethod
    async def blackjack_finish(game: BlackJack, source: commands.Context | discord.Interaction):
        game.game_finish()
        await game.channel.send(f"```\n{game.show_game()}\n{game.show_results()}\n```")
        game.round_restart()
        from ui import ReadyUI, BetUI, JoinLeaveUI
        await game.channel.send("Are you new here? Do you want to join? Or you are bored already?", view=JoinLeaveUI(game, GameType.BLACKJACK))
        await game.channel.send("Do you want to change your bet??", view=BetUI(game, False))
        await game.channel.send("Are you ready for the next game?", view=ReadyUI(game))
    

    command_dict: dict[str, Callable[[BlackJack, commands.Context | discord.Interaction, list[str]], Awaitable[None]]] = {
        "restart": cmd_restart,
        "join": CommandHandler.cmd_join,
        "leave": CommandHandler.cmd_leave,
        "start": cmd_start,
        "ready": cmd_ready,
        "unready": cmd_unready,
        "hit": cmd_hit,
        "stand": cmd_stand,
        "bet": CommandHandler.cmd_bet,
        "status": cmd_status,
        "help": cmd_help
    }
