from enums import GameType, GameState, E, PlayerState
from typing import Callable, Awaitable
from discord.ext import commands
from base_classes import Game
from black_jack import BlackJack


class CommandHandler:
    @staticmethod
    async def cmd(game: Game, ctx: commands.Context, args: list[str]) -> None:
        #jenom aby mě nebuzeroval
        pass

class BlackJackCmdHandler(CommandHandler):

    @staticmethod
    async def cmd_run(game: BlackJack, ctx: commands.Context, args: list[str]) -> None:
        if (len(args) == 0):
            await ctx.send("There is no argument, use \"!blackjack help\" to see the options")
        if (args[0] not in BlackJackCmdHandler.command_dict.keys()):
            await ctx.send("Invalid argument, use \"!blackjack help\" to see the options")
        await BlackJackCmdHandler.command_dict[args[0]](game, ctx, args)

    @staticmethod
    async def cmd_restart(game: BlackJack, ctx: commands.Context, args: list[str]):
        """Handles the 'restart' command."""
        if (len(args) != 1):
            await ctx.send(f"Invalid number of arguments: is {len(args)} should be 1")
            return
        if (game.state == GameState.RUNNING):
            await ctx.send(f"Game is running right now, wait until is ends or use 'exit'")
            return
        game.game_restart()
        await ctx.send("Game was succesfully reseted, use \'join [bet]\' to enter the game")

    @staticmethod
    async def cmd_join(game: BlackJack, ctx: commands.Context, args: list[str]):
        """Handles the 'join' command."""
        if (len(args) > 2):
            await ctx.send(f"Invalid number of arguments: is {len(args)} should be < 2")
            return
        if (game.state == GameState.RUNNING):
            await ctx.send(f"Game is running, wait for till the end")
            return
        bet = 0
        if (len(args) == 2):
            try:
                bet = int(args[1])
            except Exception as _:
                await ctx.send(f"Argument [bet] has to be number, try again")
                return
        if (game.add_player(ctx.author, bet) == E.INV_STATE):
             await ctx.send(f"Player {ctx.author.name} is already in the game!")
             return
        await ctx.send(f"Player {ctx.author.name} joined the game! {('Your bet is set to 0, use !bj bet [number] to change it.' if bet == 0 else f' Bet set to {bet}.')}")

    @staticmethod
    async def cmd_leave(game: BlackJack, ctx: commands.Context, args: list[str]):
        """Handles the 'leave' command."""
        if (len(args) != 1):
            await ctx.send(f"Invalid number of arguments: is {len(args)} should be 1")
            return
        if (game.remove_player(ctx.author) == E.INV_STATE):
             await ctx.send(f"Player {ctx.author.name} is not in the game!")
             return
        await ctx.send(f"Player {ctx.author.name} was removed from the game!")

    """ @staticmethod
    async def cmd_start(game: BlackJack, ctx: commands.Context, args: list[str]):
        if (len(args) != 1):
            await ctx.send(f"Invalid number of arguments: is {len(args)} should be 1")
            return
        if (not game.are_players_ready()):
            await ctx.send(f"Waiting for players:\n{game.show_players_by_state(PlayerState.NOT_READY)}")
            return
        game.game_start()
        await ctx.send(f"```\n{game.show_game()}\n```")
        game.check_blackjack()
        if (game.is_everyone_finished()):
            await BlackJackCmdHandler.blackjack_finish(game, ctx)
            return """

    @staticmethod
    async def cmd_ready(game: BlackJack, ctx: commands.Context, args: list[str]):
        """Handles the 'ready' command."""    
        if (len(args) != 1):
            await ctx.send(f"Invalid number of arguments: is {len(args)} should be 1")
            return
        if (game.state == GameState.RUNNING):
            await ctx.send(f"Game is already running")
            return
        game.players[ctx.author.id].state = PlayerState.READY
        await ctx.send(f"{ctx.author.name} is READY")
        if (game.are_players_ready()):
            game.game_start()
            await ctx.send(f"```\n{game.show_game()}\n```")
            game.check_blackjack()
            if (game.is_everyone_finished()):
                await BlackJackCmdHandler.blackjack_finish(game, ctx)
                return
    
    @staticmethod
    async def cmd_unready(game: BlackJack, ctx: commands.Context, args: list[str]):
        """Handles the 'ready' command."""    
        if (len(args) != 1):
            await ctx.send(f"Invalid number of arguments: is {len(args)} should be 1")
            return
        if (game.state == GameState.RUNNING):
            await ctx.send(f"Game is already running")
            return
        game.players[ctx.author.id].state = PlayerState.NOT_READY
        await ctx.send(f"{ctx.author.name} is UNREADY")

    @staticmethod
    async def cmd_hit(game: BlackJack, ctx: commands.Context, args: list[str]):
        """Handles the 'hit' command."""
        if (len(args) != 1):
            await ctx.send(f"Invalid number of arguments: is {len(args)} should be 1")
            return
        can_play: E = game.player_hit(ctx.author)
        await ctx.send(f"```{game.players[ctx.author.id].show_player()}```")
        if (game.is_everyone_finished()):
            await BlackJackCmdHandler.blackjack_finish(game, ctx)
            return
        if (can_play == E.INV_STATE):
            await ctx.send(f"{ctx.author.name} cannot hit anymore")
        
    @staticmethod
    async def cmd_stand(game: BlackJack, ctx: commands.Context, args: list[str]):
        """Handles the 'stand' command."""
        if (len(args) != 1):
            await ctx.send(f"Invalid number of arguments: is {len(args)} should be 1")
            return
        if (game.player_stand(ctx.author) == E.INV_STATE):
            await ctx.send(f"{ctx.author.name} already stands")
            return
        if (game.is_everyone_finished()):
            await BlackJackCmdHandler.blackjack_finish(game, ctx)
            return
        await ctx.send(f"{ctx.author.name} now stands")
        
    @staticmethod
    async def cmd_bet(game: BlackJack, ctx: commands.Context, args: list[str]):
        """Handles the 'bet' command."""
        if (len(args) != 2):
            await ctx.send(f"Invalid number of arguments: is {len(args)} should be 2")
            return
        try:
            bet = int(args[1])
        except Exception as _:
            await ctx.send(f"Argument [bet] has to be number, try again")
            return
        game.change_bet(ctx.author, bet)
        await ctx.send(f"{ctx.author.name}'s bet changed to {bet}")

    @staticmethod
    async def cmd_status(game: BlackJack, ctx: commands.Context, args: list[str]):
        """Handles the 'status' command."""
        if (len(args) != 1):
            await ctx.send(f"Invalid number of arguments: is {len(args)} should be 1")
            return
        match (game.state):
            case GameState.WAITING_FOR_PLAYERS:
                await ctx.send(f"```GAME IS WAITING TO START:\n\nPlayer that are not ready:\n{game.show_players_by_state(PlayerState.NOT_READY)}```")
                return
            case GameState.RUNNING:
                await ctx.send(f"```GAME IS RUNNING:\n\nTable:\n{game.show_game()}\n\nStill active players:\n{game.show_players_by_state(PlayerState.PLAYING)}```")
                return
            case GameState.ENDED:
                await ctx.send(f"```GAME ENDED:\n\nResults:\n{game.show_results()}```")
                return
        await ctx.send("Command 'status' invoked.")

    @staticmethod
    async def cmd_help(game: BlackJack, ctx: commands.Context, args: list[str]):
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
        await ctx.send("\n".join(help))

    @staticmethod
    async def blackjack_finish(game: BlackJack, ctx: commands.Context):
        game.game_finish()
        await ctx.send(f"```\n{game.show_game()}\n{game.show_results()}\n```")
        game.round_restart()
    

    command_dict: dict[str, Callable[[BlackJack, commands.Context, list[str]], Awaitable[None]]] = {
        "restart": cmd_restart,
        "join": cmd_join,
        "leave": cmd_leave,
        #"start": cmd_start,
        "ready": cmd_ready,
        "unready": cmd_unready,
        "hit": cmd_hit,
        "stand": cmd_stand,
        "bet": cmd_bet,
        "status": cmd_status,
        "help": cmd_help
    }
