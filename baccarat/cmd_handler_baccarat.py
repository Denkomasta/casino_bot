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
        await game.channel.send("Are you ready for the next game?", view=ReadyUI(game))


    @staticmethod
    async def cmd_join(game: Baccarat, source: commands.Context | discord.Interaction, args: list[str]):
        """Handles the 'join' command."""
        if (len(args) != 3 and len(args) != 1):
            await CommandHandler.send(f"Invalid number of arguments: is {len(args)} should be < 3", source)
            return
        bet = 0
        type = 0
        if (len(args) == 3):
            try:
                bet = int(args[1])
            except Exception as _:
                await CommandHandler.send(f"Argument [bet] has to be number, try again", source, ephemeral=True)
                return
            
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
        if (game.add_player(CommandHandler.get_info(source), bet, type) == E.INV_STATE):
             await CommandHandler.send(f"Player {CommandHandler.get_name(source)} is already in the game!", source, ephemeral=True)
             return
        await game.channel.send(f"Player {CommandHandler.get_name(source)} joined the game! {('Your bet is set to 0, use !bj bet [number] to change it.' if bet == 0 else f' Bet set to {bet}.')}")

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
        "join": cmd_join,
        "leave": CommandHandler.cmd_leave,
        "ready": cmd_ready,
        "unready": cmd_unready,
        "bet": cmd_bet,
        "help": cmd_help
    }