from enums import GameType, GameState, E, PlayerState, BaccaratBetType
from typing import Callable, Awaitable
from discord.ext import commands
from base_classes import Game
from black_jack import BlackJack
from baccarat import Baccarat
from rng_games import RNGGame, Bet
from abc import ABC


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


class BaccaratCmdHandler(CommandHandler):

    @staticmethod
    async def cmd_run(game: Baccarat, ctx: commands.Context, args: list[str]) -> None:
        if (len(args) == 0):
            await ctx.send("There is no argument, use \"!baccarat help\" to see the options")
        if (args[0] not in BaccaratCmdHandler.command_dict.keys()):
            await ctx.send("Invalid argument, use \"!blackjack help\" to see the options")
        await BaccaratCmdHandler.command_dict[args[0]](game, ctx, args)

    @staticmethod
    async def cmd_ready(game: Baccarat, ctx: commands.Context, args: list[str]):
        if (len(args) != 1):
            await ctx.send(f"Invalid number of arguments: is {len(args)} should be 1")
            return
        if (game.state == GameState.RUNNING):
            await ctx.send(f"Game is already running")
            return
        game.players[ctx.author.id].state = PlayerState.READY
        await ctx.send(f"{ctx.author.name} is READY")
        if (game.are_players_ready()):
            game.collect_bets()
            game.game_start()
            game.evaluate_bets()
            game.give_winnings()
            await ctx.send(f"```\n{game.show_game()}\n{game.show_results()}```")
            game.round_restart()

    @staticmethod
    async def cmd_unready(game: Baccarat, ctx: commands.Context, args: list[str]):
        if (len(args) != 1):
            await ctx.send(f"Invalid number of arguments: is {len(args)} should be 1")
            return
        if (game.state == GameState.RUNNING):
            await ctx.send(f"Game is already running")
            return
        game.players[ctx.author.id].state = PlayerState.NOT_READY
        await ctx.send(f"{ctx.author.name} is UNREADY")

    @staticmethod
    async def cmd_bet(game: Baccarat, ctx: commands.Context, args: list[str]):
        if (len(args) != 3):
            await ctx.send(f"Invalid number of arguments: is {len(args)} should be 2")
            return
        try:
            bet = int(args[1])
        except Exception as _:
            await ctx.send(f"Argument [bet] has to be number, try again")
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
                await ctx.send(f"Argument [type] has to be banker/player/tie, try again")
                return
            
        game.change_bet(ctx.author, bet, type)
        await ctx.send(f"{ctx.author.name}'s bet changed to {bet}")


    @staticmethod
    async def cmd_join(game: Baccarat, ctx: commands.Context, args: list[str]):
        """Handles the 'join' command."""
        if (len(args) != 3 and len(args) != 1):
            await ctx.send(f"Invalid number of arguments: is {len(args)} should be < 3")
            return
        bet = 0
        type = 0
        if (len(args) == 3):
            try:
                bet = int(args[1])
            except Exception as _:
                await ctx.send(f"Argument [bet] has to be number, try again")
                return
            
            match args[2]:
                case "banker":
                    type = BaccaratBetType.BANKER
                case "player":
                    type = BaccaratBetType.PLAYER
                case "tie":
                    type = BaccaratBetType.TIE
                case _:
                    await ctx.send(f"Argument [type] has to be banker/player/tie, try again")
                    return
        if (game.add_player(ctx.author, bet) == E.INV_STATE):
             await ctx.send(f"Player {ctx.author.name} is already in the game!")
             return
        game.change_bet(ctx.author, bet, type)
        await ctx.send(f"Player {ctx.author.name} joined the game! {('Your bet is set to 0, use !bj bet [number] to change it.' if bet == 0 else f' Bet set to {bet}.')}")

    @staticmethod
    async def cmd_leave(game: Baccarat, ctx: commands.Context, args: list[str]):
        """Handles the 'leave' command."""
        if (len(args) != 1):
            await ctx.send(f"Invalid number of arguments: is {len(args)} should be 1")
            return
        if (game.remove_player(ctx.author) == E.INV_STATE):
             await ctx.send(f"Player {ctx.author.name} is not in the game!")
             return
        await ctx.send(f"Player {ctx.author.name} was removed from the game!")

    @staticmethod
    async def cmd_help(game: Baccarat, ctx: commands.Context, args: list[str]):
        """Handles the 'help' command."""
        help: list[str] = [
            "create - creates a new game",
            "exit - destroys current game",
            "join [number] [type] - adds you to current game, with instead of number use size of your bet and instead of type use banker/player/tie",
            "ready - sets you READY",
            "unready - sets you UNREADY",
            "bet [number][type]- changes your bet",
        ]
        await ctx.send("\n".join(help))


    command_dict: dict[str, Callable[[Baccarat, commands.Context, list[str]], Awaitable[None]]] = {
        "join": cmd_join,
        "leave": cmd_leave,
        "ready": cmd_ready,
        "unready": cmd_unready,
        "bet": cmd_bet,
        "help": cmd_help
    }

class RNGCmdHandler(ABC, CommandHandler):
    
    @staticmethod
    async def command_run(game: RNGGame, ctx: commands.Context, argv: list[str]):
        command = argv[0]
        if RNGCmdHandler.commands_dict.get(command, None) is None:
            await ctx.send(f"Unknown command, run !{game.name} help for available commands")
            return
        await RNGCmdHandler.commands_dict[command](game, ctx, argv)

    @staticmethod
    async def inv_args_message(game: RNGGame, ctx: commands.Context):
        await ctx.send(f"Invalid number of arguments, run !{game.name} help for available commands")

    @staticmethod
    async def command_join(game: RNGGame, ctx: commands.Context, argv: list[str]):
        if len(argv) > 2:
            await RNGCmdHandler.inv_args_message(game, ctx)
            return
        try:
            bet: int = int(argv[1])
        except ValueError:
            await ctx.send(f"Invalid format of bet, insert whole number")
            return
        cmd_status: E = game.add_player(ctx.author.id, ctx.author.display_name, bet)
        if cmd_status == E.INV_PLAYER:
            await ctx.send(f"Player {ctx.message.author.mention} is already in-game")
            return
        if cmd_status == E.INSUFFICIENT_FUNDS:
            await ctx.send(f"{ctx.message.author.mention} You don't have enough money in your server balance!")
            return
        await ctx.send(f"Player {ctx.author.display_name} has successfully joined the game with balance {game.players[ctx.author.id].balance}\n{ctx.message.author.mention} The in-game balance was deducted from your global balance and will be returned when you leave using !{game.name} leave")

    @staticmethod
    async def command_leave(game: RNGGame, ctx: commands.Context, argv: list[str]):
        cmd_status: E = game.remove_player(ctx.author.id)
        if cmd_status == E.INV_PLAYER:
            await ctx.send(f"{ctx.message.author.mention} You are not in the game!")
        await ctx.send(f"Player {ctx.author.display_name} has successfully left the game. \n{ctx.message.author.mention} Your server balance was updated!")

    @staticmethod
    async def command_bet(game: RNGGame, ctx: commands.Context, argv: list[str]):
        if len(argv) != 3:
            await RNGCmdHandler.inv_args_message(game, ctx)
            return
        try:
            number = int(argv[1])
            bet = int(argv[2])
        except ValueError:
            await ctx.send(f"Invalid format of the command, both number and the value of the bet must be whole numbers.")
            return
        cmd_status: E = game.place_bet(ctx.author.id, bet, number, (game.highest - game.lowest + 1))
        if cmd_status == E.INV_PLAYER:
            ctx.send(f"{ctx.message.author.mention} You are not in the game! You must use !{game.name} join [balance] to participate")
        if cmd_status == E.OUT_OF_RANGE:
            await ctx.send(f"{ctx.message.author.mention} The number you want to bet on is out of the valid range. Bet on a number between {game.lowest} and {game.highest}")
            return
        if cmd_status == E.INSUFFICIENT_FUNDS:
            await ctx.send(f"{ctx.message.author.mention} You don't have enough money in your in-game balance. Try again with less or re-join the game with higher balance!")
            return
        await ctx.send(f"Player {ctx.author.display_name} has successfully bet {bet} on number {number}")

    @staticmethod
    async def command_ready(game: RNGGame, ctx: commands.Context, argv: list[str]):
        cmd_status: E = game.ready_up(ctx.author.id)
        if cmd_status == E.INV_PLAYER:
            ctx.send(f"{ctx.message.author.mention} You are not in the game! You must use !{game.name} join [balance] to participate")
            return
        if cmd_status == E.INV_STATE:
            ctx.send(f"{ctx.message.author.mention} You are already ready for the roll!")
            return
        await ctx.send(f"Player {ctx.author.display_name} is ready for the roll!")
        if game.check_ready():
            await ctx.send("All players are ready! Rolling!")
            await RNGCmdHandler.command_roll(game, ctx, argv)


    @staticmethod
    async def command_unready(game: RNGGame, ctx: commands.Context, argv: list[str]):
        cmd_status: E = game.unready(ctx.author.id)
        if cmd_status == E.INV_PLAYER:
            ctx.send(f"{ctx.message.author.mention} You are not in the game! You must use !{game.name} join [balance] to participate")
            return
        await ctx.send(f"Player {ctx.author.display_name} needs more time to think and is now not ready")

    @staticmethod
    async def command_roll(game: RNGGame, ctx: commands.Context, argv: list[str]):
        winning_bets: list[Bet] = game.roll()
        await ctx.send(f"The winning number is: {game.last_roll}!")
        await ctx.send(game.build_winners_message(winning_bets))
        if game.give_winnings(winning_bets) == E.INV_PLAYER:
            await ctx.send(f"One or more players could not collect their winning because they left the game :(")
        game.restart_game()
        await ctx.send(f"The game has been restarted, bet and try your luck again!")

    commands_dict = {
            "join": command_join,
            "bet": command_bet,
            "leave": command_leave,
            "ready": command_ready,
            "unready": command_unready,
            "roll": command_roll
        }
    
class CoinflipCmdHandler(RNGCmdHandler):
    pass

class RollTheDiceCmdHandler(RNGCmdHandler):
    pass