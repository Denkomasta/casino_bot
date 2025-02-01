from rng_games import RNGGame, Bet, Coinflip, RollTheDice, GuessTheNumber
from discord.ext import commands
from enums import E, CoinflipSides
from typing import Callable, Awaitable
from cmd_handler import CommandHandler

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
        conclusion_message = game.build_conclusion_message(winning_bets) + 25 * '-' + '\n'
        if game.give_winnings(winning_bets) == E.INV_PLAYER:
           conclusion_message += f"One or more players could not collect their winning because they left the game :(\n"
        game.restart_game()
        conclusion_message += f"The game has been restarted, bet and try your luck again!"
        await ctx.send(f"```{conclusion_message}```")

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