from enums import GameType, GameState, E, PlayerState, BaccaratBetType, CoinflipSides
from typing import Callable, Awaitable
from discord.ext import commands
from base_classes import Game
from black_jack import BlackJack
from baccarat import Baccarat
from rng_games import RNGGame, Bet, Coinflip, RollTheDice, GuessTheNumber
from abc import ABC, abstractmethod


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

class RNGCmdHandler(CommandHandler):
    
    @staticmethod
    async def command_run(game: RNGGame, ctx: commands.Context, argv: list[str]):
        pass

    @staticmethod
    async def inv_args_message(game: RNGGame, ctx: commands.Context):
        await ctx.send(f"Invalid arguments, run !{game.name} help for available commands")

    @staticmethod
    async def command_join(game: RNGGame, ctx: commands.Context, argv: list[str]):
        if len(argv) > 2:
            await RNGCmdHandler.inv_args_message(game, ctx)
            return
        cmd_status: E = game.add_player(ctx.author.id, ctx.author.display_name)
        if cmd_status == E.INV_PLAYER:
            await ctx.send(f"Player {ctx.message.author.mention} is already in-game")
            return
        if cmd_status == E.INSUFFICIENT_FUNDS:
            await ctx.send(f"{ctx.message.author.mention} You don't have enough money in your server balance!")
            return
        await ctx.send(f"Player {ctx.author.display_name} has successfully joined the game! You can now place bets with !{game.name} bet!")

    @staticmethod
    async def command_leave(game: RNGGame, ctx: commands.Context, argv: list[str]):
        cmd_status: E = game.remove_player(ctx.author.id)
        if cmd_status == E.INV_PLAYER:
            await ctx.send(f"{ctx.message.author.mention} You are not in the game!")
        await ctx.send(f"Player {ctx.author.display_name} has successfully left the game. \n{ctx.message.author.mention} Your server balance was updated!")

    @staticmethod
    async def command_bet(game: RNGGame, ctx: commands.Context, argv: list[str]):
        pass

    @staticmethod
    async def command_ready(game: RNGGame, ctx: commands.Context, argv: list[str]):
        cmd_status: E = game.ready_up(ctx.author.id)
        if cmd_status == E.INV_PLAYER:
            await ctx.send(f"{ctx.message.author.mention} You are not in the game! You must use !{game.name} join to participate")
            return
        if cmd_status == E.INV_STATE:
            await ctx.send(f"{ctx.message.author.mention} You are already ready for the roll!")
            return
        await ctx.send(f"Player {ctx.author.display_name} is ready for the roll!")

    @staticmethod
    async def command_unready(game: RNGGame, ctx: commands.Context, argv: list[str]):
        cmd_status: E = game.unready(ctx.author.id)
        if cmd_status == E.INV_PLAYER:
            await ctx.send(f"{ctx.message.author.mention} You are not in the game! You must use !{game.name} join to participate")
            return
        await ctx.send(f"Player {ctx.author.display_name} needs more time to think and is now not ready")

    @staticmethod
    async def subcommand_roll(game: RNGGame, ctx: commands.Context, argv: list[str]):
        winning_bets: list[Bet] = game.roll()
        await ctx.send(f"The winning number is: {game.last_roll}!")
        await ctx.send(game.build_winners_message(winning_bets))
        if game.give_winnings(winning_bets) == E.INV_PLAYER:
            await ctx.send(f"One or more players could not collect their winning because they left the game :(")
        game.restart_game()
        await ctx.send(f"The game has been restarted, bet and try your luck again!")

    @staticmethod
    async def command_help(game: RNGGame, ctx: commands.Context, argv: list[str]):
        await ctx.send("Please use !help [game] to display the help dialog")

    @staticmethod
    async def command_status(game: RNGGame, ctx: commands.Context, argv: list[str]):
        if not game.check_valid_player(ctx.author.id):
            await ctx.send(f"{ctx.message.author.mention} You are not in the game! You must use !{game.name} join to participate")
            return
        message = game.get_status_msg()
        await ctx.send(f"```{message}```")
    
    @staticmethod
    async def command_betlist(game: RNGGame, ctx: commands.Context, argv: list[str]):
        if not game.check_valid_player(ctx.author.id):
            await ctx.send(f"{ctx.message.author.mention} You are not in the game! You must use !{game.name} join to participate")
            return
        message = game.get_bets_msg()
        if message is None:
            await ctx.send("An error occured listing the bets")
            return
        await ctx.send(f"```{message}```")

    commands_dict: dict[str, Callable[[commands.Context, list[str]], Awaitable[None]]] = {
            "join": command_join,
            "bet": command_bet,
            "leave": command_leave,
            "ready": command_ready,
            "unready": command_unready,
            "help": command_help,
            "status": command_status,
            "betlist": command_betlist
        }
    
class CoinflipCmdHandler(RNGCmdHandler):
    # Override
    @staticmethod
    async def command_run(game: Coinflip, ctx: commands.Context, argv: list[str]):
        command = argv[0]
        if CoinflipCmdHandler.commands_dict.get(command, None) is None:
            if RNGCmdHandler.commands_dict.get(command, None) is None:
                await ctx.send(f"Unknown command, run !help {game.name} for available commands")
                return
            await RNGCmdHandler.commands_dict[command](game, ctx, argv)
            return
        await CoinflipCmdHandler.commands_dict[command](game, ctx, argv)

    # Override
    @staticmethod 
    async def command_bet(game: Coinflip, ctx, argv):
        if len(argv) != 3:
            await RNGCmdHandler.inv_args_message(game, ctx)
            return
        if argv[1] == "heads":
            number = int(CoinflipSides.HEADS)
        elif argv[1] == "tails":
            number = int(CoinflipSides.TAILS)
        else:
            await ctx.send(f"{ctx.author.mention} You passed an invalid bet, type !{game.name} bet [heads/tails] [amount] to place a bet")
            return
        try:
            bet = int(argv[2])
        except ValueError:
            await ctx.send(f"Invalid format of the command, both number and the value of the bet must be whole numbers.")
            return
        cmd_status: E = game.place_bet(ctx.author.id, bet, number, (game.highest - game.lowest + 1))
        if cmd_status == E.INV_PLAYER:
            await ctx.send(f"{ctx.message.author.mention} You are not in the game! You must use !{game.name} join to participate")
        if cmd_status == E.INSUFFICIENT_FUNDS:
            await ctx.send(f"{ctx.message.author.mention} You don't have enough money in your balance. Try again with less!")
            return
        if cmd_status == E.DUPLICITE_BET:
            await ctx.send(f"Player {ctx.author.display_name} has successfully bet another {bet} on {argv[1]}")
            return
        await ctx.send(f"Player {ctx.author.display_name} has successfully bet {bet} on {argv[1]}")

    #Override
    @staticmethod
    async def command_ready(game, ctx, argv):
        await RNGCmdHandler.command_ready(game, ctx, argv)
        if game.check_ready():
            await ctx.send("All players are ready! Rolling!")
            await CoinflipCmdHandler.subcommand_roll(game, ctx, argv)

    #Override
    @staticmethod
    async def subcommand_roll(game, ctx, argv):
        winning_bets: list[Bet] = game.roll()
        side = "HEADS" if CoinflipSides(game.last_roll) == CoinflipSides.HEADS else "TAILS"
        await ctx.send(f"The winning side is: {side}!")
        await ctx.send(game.build_winners_message(winning_bets))
        if game.give_winnings(winning_bets) == E.INV_PLAYER:
            await ctx.send(f"One or more players could not collect their winning because they left the game :(")
        game.restart_game()
        await ctx.send(f"The game has been restarted, bet and try your luck again!")

    commands_dict: dict[str, Callable[[commands.Context, list[str]], Awaitable[None]]] = {
        "bet": command_bet,
        "ready": command_ready
    }

class RollTheDiceCmdHandler(RNGCmdHandler):
    # Override
    @staticmethod
    async def command_run(game: RollTheDice, ctx: commands.Context, argv: list[str]):
        command = argv[0]
        if RollTheDiceCmdHandler.commands_dict.get(command, None) is None:
            if RNGCmdHandler.commands_dict.get(command, None) is None:
                await ctx.send(f"Unknown command, run !help {game.name} for available commands")
                return
            await RNGCmdHandler.commands_dict[command](game, ctx, argv)
            return
        await RollTheDiceCmdHandler.commands_dict[command](game, ctx, argv)

    @staticmethod
    async def command_bet(game: RollTheDice, ctx, argv):
        if len(argv) != 4 or argv[1] not in ["sum", "doubles"]:
            await RNGCmdHandler.inv_args_message(game, ctx)
            return
        try:
            bet_type = argv[1]
            input_number = int(argv[2])
            bet = int(argv[3])
        except ValueError:
            await ctx.send(f"Invalid format of the command, both selected sum/number for doubles and the value of the bet must be whole numbers.")
            return
        number = -input_number if bet_type == "doubles" else input_number
        cmd_status: E = game.place_bet(ctx.author.id, bet, number, game.get_rate(number))
        if cmd_status == E.INV_PLAYER:
            await ctx.send(f"{ctx.message.author.mention} You are not in the game! You must use !{game.name} join to participate")
        if cmd_status == E.OUT_OF_RANGE:
            await ctx.send(f"{ctx.message.author.mention} The number you have written is out of range, bet on sums between 2 and 12 or on doubles")
        if cmd_status == E.INSUFFICIENT_FUNDS:
            await ctx.send(f"{ctx.message.author.mention} You don't have enough money in your balance. Try again with less!")
            return
        bet_type_message = "sum of" if bet_type == "sum" else "double"
        if cmd_status == E.DUPLICITE_BET:
            await ctx.send(f"Player {ctx.author.display_name} has successfully bet another {bet} on {bet_type_message} {str(input_number)}")
            return
        await ctx.send(f"Player {ctx.author.display_name} has successfully bet {bet} on {bet_type_message} {str(input_number)}")
    
    #Override
    @staticmethod
    async def command_ready(game, ctx, argv):
        await RNGCmdHandler.command_ready(game, ctx, argv)
        if game.check_ready():
            await ctx.send("All players are ready! Rolling!")
            await RollTheDiceCmdHandler.subcommand_roll(game, ctx, argv)

    #Override
    @staticmethod
    async def subcommand_roll(game: RollTheDice, ctx, argv):
        winning_bets: list[Bet] = game.roll()
        await ctx.send(game.build_conclusion_message(winning_bets))
        if game.give_winnings(winning_bets) == E.INV_PLAYER:
            await ctx.send(f"One or more players could not collect their winning because they left the game :(")
        game.restart_game()
        await ctx.send(f"The game has been restarted, bet and try your luck again!")

    commands_dict: dict[str, Callable[[commands.Context, list[str]], Awaitable[None]]] = {
        "bet": command_bet,
        "ready": command_ready
    }

class GuessNumberCmdHandler(RNGCmdHandler):

    @staticmethod
    async def command_ready(game, ctx, argv):      # TODO add check if everyone has a bet
        await RNGCmdHandler.command_ready(game, ctx, argv)
        if game.check_ready():
            await ctx.send("All players are ready! Evaluating!")
            await GuessNumberCmdHandler.subcommand_roll(game, ctx, argv)
    
    @staticmethod
    async def subcommand_roll(game: GuessTheNumber, ctx, argv):
        winning_number = game.last_roll
        if winning_number is None:
            game.roll()
            winning_number = game.last_roll

        winning_bets: list[Bet] = game.bets[winning_number]
        game.remaining_rounds -= 1
        if len(winning_bets) > 0:
            game.give_winnings(winning_bets)
            await ctx.send(game.build_winners_message(winning_bets))
            game.restart_game()
            await ctx.send(f"The game has been restarted, winning number was: {winning_number}, bet and try your luck again!")
            return

        if game.remaining_rounds == 0:
            game.restart_game()
            await ctx.send(f"The game has no champion, the winning number was: {winning_number}! Game has been restarted, bet and try your luck again!")
            return

        await ctx.send(f"No winners this round! Change your guesses and try again!")
        for player in game.players.values():
            player.ready = False
        
        for number, bets in game.bets.items():
            for bet in bets:
                user = ctx.guild.get_member(bet.player.player_id)       # TODO change player_id in RNGplayer to discord author.
                if number > winning_number:
                    await user.send(f"{bet.player.name} your number was too **high**!")   # TODO Change to ephemeral interaction
                else:
                    await user.send(f"{bet.player.name} your number was too **low**!")
            
    # TODO only one guess
    @staticmethod
    async def command_guess(game: GuessTheNumber, ctx, argv):   # !gtn guess [number] [amount]
        if len(argv) != 3:      # TODO possible 2 args when u dont want to change amount
            await RNGCmdHandler.inv_args_message(game, ctx)
            return
        try:
            number = int(argv[1])
            amount = int(argv[2])
        except ValueError:
            await ctx.send(f"Invalid format of the command, the number and the amount must be a whole number.")
            return
        cmd_status: E = game.change_bet(ctx.author.id, amount, number, (game.highest - game.lowest + 1) // game.rounds)     # TODO change odds with logarithm
        if cmd_status == E.INV_PLAYER:
            await ctx.send(f"{ctx.message.author.mention} You are not in the game! You must use !{game.name} join to participate")
        if cmd_status == E.INSUFFICIENT_FUNDS:
            await ctx.send(f"{ctx.message.author.mention} You don't have enough money in your balance. Try again with less!")
            return
        await ctx.send(f"Player {ctx.author.display_name} has successfully bet {amount} on number {number}, good luck!")
    

    @staticmethod
    async def command_run(game: GuessTheNumber, ctx: commands.Context, argv: list[str]):
        command = argv[0]
        if GuessNumberCmdHandler.commands_dict.get(command, None) is None:
            if RNGCmdHandler.commands_dict.get(command, None) is None:
                await ctx.send(f"Unknown command, run !help {game.name} for available commands")
                return
            await RNGCmdHandler.commands_dict[command](game, ctx, argv)
            return
        await GuessNumberCmdHandler.commands_dict[command](game, ctx, argv)
    
    commands_dict: dict[str, Callable[[commands.Context, list[str]], Awaitable[None]]] = {
        "guess": command_guess,
        "ready": command_ready,
    }