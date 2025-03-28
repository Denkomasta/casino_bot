from enums import GameType, GameState, E, PlayerState, BaccaratBetType, CoinflipSides
from typing import Callable, Awaitable
from discord.ext import commands
from base_classes import Game
from baccarat.baccarat import Baccarat
from cmd_handler import CommandHandler
import discord

class BaccaratCmdHandler(CommandHandler):

    @staticmethod
    async def cmd_run(game: Baccarat, source: commands.Context | discord.Interaction, args: list[str]) -> None:
        if (len(args) == 0):
            await CommandHandler.send("There is no argument, use \"!baccarat help\" to see the options", source)
        if (args[0] not in BaccaratCmdHandler.command_dict.keys()):
            await CommandHandler.send("Invalid argument, use \"!blackjack help\" to see the options", source)
        await BaccaratCmdHandler.command_dict[args[0]](game, source, args)

    @staticmethod
    async def cmd_ready(game: Baccarat, source: commands.Context | discord.Interaction, args: list[str]):
        if (len(args) != 1):
            await CommandHandler.send(f"Invalid number of arguments: is {len(args)} should be 1", source)
            return
        if (game.state == GameState.RUNNING):
            await CommandHandler.send(f"Game is already running", source)
            return
        game.players[CommandHandler.get_id(source)].state = PlayerState.READY
        await CommandHandler.send(f"{CommandHandler.get_name(source)} is READY", source, ephemeral=True)
        if (game.are_players_ready()):
            from ui import StartUI
            await game.channel.send(view=StartUI(game))

    @staticmethod
    async def cmd_unready(game: Baccarat, source: commands.Context | discord.Interaction, args: list[str]):
        if (len(args) != 1):
            await CommandHandler.send(f"Invalid number of arguments: is {len(args)} should be 1", source)
            return
        if (game.state == GameState.RUNNING):
            await CommandHandler.send(f"Game is already running", source, ephemeral=True)
            return
        game.players[CommandHandler.get_id(source)].state = PlayerState.NOT_READY
        await CommandHandler.send(f"{CommandHandler.get_name(source)} is UNREADY", source, ephemeral=True)

    @staticmethod
    async def cmd_bet(game: Baccarat, source: commands.Context | discord.Interaction, args: list[str]):
        if (len(args) != 3):
            await CommandHandler.send(f"Invalid number of arguments: is {len(args)} should be 2", source)
            return
        try:
            bet = int(args[1])
        except Exception as _:
            await CommandHandler.send(f"Argument [bet] has to be number, try again", source, ephemeral=True)
            return
        
        type: int

        match args[2]:
            case "banker":
                type = BaccaratBetType.BANKER
            case "player":
                type = BaccaratBetType.PLAYER
            case "tie":
                type = BaccaratBetType.TIE
            case _:
                await CommandHandler.send(f"Argument [type] has to be banker/player/tie, try again", source, ephemeral=True)
                return
            
        game.change_bet(CommandHandler.get_info(source), bet, type)
        await CommandHandler.send(f"{CommandHandler.get_name(source)}'s bet changed to {bet} on {args[2]}", source, ephemeral=True)

    @staticmethod
    async def cmd_start(game: Baccarat, source: commands.Context | discord.Interaction, args: list[str]):
        if (len(args) != 1):
            await CommandHandler.send(f"Invalid number of arguments: is {len(args)} should be 1", source)
            return
        if (not game.are_players_ready()):
            await game.channel.send(f"Waiting for players:\n{game.show_players_by_state(PlayerState.NOT_READY)}")
            return
        game.game_start()
        game.evaluate_bets()
        game.give_winnings()
        await game.channel.send(f"```\n{game.show_game()}\n{game.show_results()}```")
        game.round_restart()
        from ui import ReadyUI, JoinLeaveUI
        from baccarat.ui_baccarat import BaccaratBetUI
        await game.channel.send("Are you new here? Do you want to join? Or you are bored already?", view=JoinLeaveUI(game, GameType.BACCARAT))
        await game.channel.send("Do you want to change your bet??", view=BaccaratBetUI(game))

    @staticmethod
    async def cmd_betlist(game: Baccarat, source: commands.Context | discord.Interaction, args: list[str]):
        if (len(args) != 1):
            await CommandHandler.send(f"Invalid number of arguments: is {len(args)} should be 1", source)
            return
        await CommandHandler.send(f"```\n{game.show_betlist()}\n```", source, ephemeral=True)


    @staticmethod
    async def cmd_status(game: Baccarat, source: commands.Context | discord.Interaction, args: list[str]):
        if (len(args) != 1):
            await CommandHandler.send(f"Invalid number of arguments: is {len(args)} should be 1", source, ephemeral=True)
            return
        match (game.state):
            case GameState.WAITING_FOR_PLAYERS:
                await CommandHandler.send(f"```GAME IS WAITING TO START:\n\nPlayer that are not ready:\n{game.show_players_by_state(PlayerState.NOT_READY)}```", source, ephemeral=True)
                return
            case GameState.RUNNING:
                await CommandHandler.send(f"```GAME IS RUNNING:\n\nTable:\n{game.show_game()}\n\nStill active players:\n{game.show_players_by_state(PlayerState.PLAYING)}```", source, ephemeral=True)
                return
            case GameState.ENDED:
                await CommandHandler.send(f"```GAME ENDED:\n\nResults:\n{game.show_results()}```", source, ephemeral=True)
                return

    @staticmethod
    async def cmd_help(game: Baccarat, source: commands.Context | discord.Interaction, args: list[str]):
        """Handles the 'help' command."""
        help: list[str] = [
            "create - creates a new game",
            "exit - destroys current game",
            "join [number] [type] - adds you to current game, with instead of number use size of your bet and instead of type use banker/player/tie",
            "ready - sets you READY",
            "unready - sets you UNREADY",
            "bet [number][type]- changes your bet",
        ]
        await game.channel.send("```\n".join(help) + "\n```")


    command_dict: dict[str, Callable[[Baccarat, commands.Context | discord.Interaction, list[str]], Awaitable[None]]] = {
        "join": CommandHandler.cmd_join,
        "leave": CommandHandler.cmd_leave,
        "ready": cmd_ready,
        "unready": cmd_unready,
        "bet": cmd_bet,
        "betlist": cmd_betlist,
        "help": cmd_help
    }