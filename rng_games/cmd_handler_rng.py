from rng_games.rng_games import RNGGame, RNGBet, Coinflip, RollTheDice, GuessTheNumber, Roulette
from discord.ext import commands
from enums import E, CoinflipSides
from typing import Callable, Awaitable
from cmd_handler import CommandHandler
import discord

class RNGCmdHandler(CommandHandler):
    
    @staticmethod
    async def command_run(game: RNGGame, source: commands.Context | discord.Interaction, argv: list[str]):
        pass

    @staticmethod
    async def inv_args_message(game: RNGGame, source: commands.Context | discord.Interaction):
        await CommandHandler.send(f"Invalid arguments, run !{game.name} help for available commands", source, ephemeral=True)

    @staticmethod
    async def command_join(game: RNGGame, source: commands.Context | discord.Interaction, argv: list[str]):
        if len(argv) > 2:
            await RNGCmdHandler.inv_args_message(game, source)
            return
        cmd_status: E = game.add_player(CommandHandler.get_info(source))
        if cmd_status == E.INV_PLAYER:
            await CommandHandler.send(f"Player {CommandHandler.get_info(source).mention} is already in-game", source, ephemeral=True)
            return
        if cmd_status == E.INSUFFICIENT_FUNDS:
            await CommandHandler.send(f"{CommandHandler.get_info(source).mention} You don't have enough money in your server balance!", source, ephemeral=True)
            return
        await CommandHandler.send(f"Player {CommandHandler.get_info(source).display_name} has successfully joined the game! You can now place bets with !{game.name} bet!", source)

    @staticmethod
    async def command_leave(game: RNGGame, source: commands.Context | discord.Interaction, argv: list[str]):
        cmd_status: E = game.remove_player(CommandHandler.get_info(source))
        if cmd_status == E.INV_PLAYER:
            await CommandHandler.send(f"{CommandHandler.get_info(source).mention} You are not in the game!", source, ephemeral=True)
        await CommandHandler.send(f"Player {CommandHandler.get_info(source).display_name} has successfully left the game. \n{CommandHandler.get_info(source).mention} Your server balance was updated!", source)

    @staticmethod
    async def command_bet(game: RNGGame, source: commands.Context | discord.Interaction, argv: list[str]):
        pass

    @staticmethod
    async def command_ready(game: RNGGame, source: commands.Context | discord.Interaction, argv: list[str]):
        cmd_status: E = game.ready_up(CommandHandler.get_info(source))
        if cmd_status == E.INV_PLAYER:
            await CommandHandler.send(f"{CommandHandler.get_info(source).mention} You are not in the game! You must use !{game.name} join to participate", source, ephemeral=True)
            return
        if cmd_status == E.INV_STATE:
            await CommandHandler.send(f"{CommandHandler.get_info(source).mention} You are already ready for the roll!", source, ephemeral=True)
            return
        await CommandHandler.send(f"Player {CommandHandler.get_info(source).display_name} is ready for the roll!", source)

    @staticmethod
    async def command_unready(game: RNGGame, source: commands.Context | discord.Interaction, argv: list[str]):
        cmd_status: E = game.unready(CommandHandler.get_info(source))
        if cmd_status == E.INV_PLAYER:
            await CommandHandler.send(f"{CommandHandler.get_info(source).mention} You are not in the game! You must use !{game.name} join to participate", source)
            return
        await CommandHandler.send(f"Player {CommandHandler.get_info(source).display_name} needs more time to think and is now not ready", source)

    @staticmethod
    async def subcommand_roll(game: RNGGame, source: commands.Context | discord.Interaction, argv: list[str]):
        winning_bets: list[RNGBet] = game.roll()
        await CommandHandler.send(f"The winning number is: {game.last_roll}!", source)
        await CommandHandler.send(game.build_winners_message(winning_bets), source)
        if game.give_winnings(winning_bets) == E.INV_PLAYER:
            await CommandHandler.send(f"One or more players could not collect their winning because they left the game :(", source)
        game.restart_game()
        await CommandHandler.send(f"The game has been restarted, bet and try your luck again!", source)

    @staticmethod
    async def command_help(game: RNGGame, source: commands.Context | discord.Interaction, argv: list[str]):
        await CommandHandler.send("Please use !help [game] to display the help dialog", source)

    @staticmethod
    async def command_status(game: RNGGame, source: commands.Context | discord.Interaction, argv: list[str]):
        if not game.check_valid_player(CommandHandler.get_info(source)):
            await CommandHandler.send(f"{CommandHandler.get_info(source).mention} You are not in the game! You must use !{game.name} join to participate", source, ephemeral=True)
            return
        message = game.get_status_msg()
        await CommandHandler.send(f"```{message}```", source)
    
    @staticmethod
    async def command_betlist(game: RNGGame, source: commands.Context | discord.Interaction, argv: list[str]):
        if not game.check_valid_player(CommandHandler.get_info(source)):
            await CommandHandler.send(f"{CommandHandler.get_info(source).mention} You are not in the game! You must use !{game.name} join to participate", source, ephemeral=True)
            return
        message = game.get_bets_msg()
        if message is None:
            await CommandHandler.send("An error occured listing the bets", source, ephemeral=True)
            return
        await CommandHandler.send(f"```{message}```", source)

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
    async def command_run(game: Coinflip, source: commands.Context | discord.Interaction, argv: list[str]):
        command = argv[0]
        if CoinflipCmdHandler.commands_dict.get(command, None) is None:
            if RNGCmdHandler.commands_dict.get(command, None) is None:
                await CommandHandler.send(f"Unknown command, run !help {game.name} for available commands", source, ephemeral=True)
                return
            await RNGCmdHandler.commands_dict[command](game, source, argv)
            return
        await CoinflipCmdHandler.commands_dict[command](game, source, argv)

    # Override
    @staticmethod 
    async def command_bet(game: Coinflip, source: commands.Context | discord.Interaction, argv):
        if len(argv) != 3:
            await RNGCmdHandler.inv_args_message(game, source)
            return
        if argv[1] == "heads":
            number = int(CoinflipSides.HEADS)
        elif argv[1] == "tails":
            number = int(CoinflipSides.TAILS)
        else:
            await CommandHandler.send(f"{CommandHandler.get_info(source).mention} You passed an invalid bet, type !{game.name} bet [heads/tails] [amount] to place a bet", source, ephemeral=True)
            return
        try:
            bet = int(argv[2])
        except ValueError:
            await CommandHandler.send(f"Invalid format of the command, both number and the value of the bet must be whole numbers.", source, ephemeral=True)
            return
        cmd_status: E = game.place_bet(CommandHandler.get_info(source), bet, number, (game.highest - game.lowest + 1))
        if cmd_status == E.INV_PLAYER:
            await CommandHandler.send(f"{CommandHandler.get_info(source).mention} You are not in the game! You must use !{game.name} join to participate", source, ephemeral=True)
        if cmd_status == E.INSUFFICIENT_FUNDS:
            await CommandHandler.send(f"{CommandHandler.get_info(source).mention} You don't have enough money in your balance. Try again with less!", source, ephemeral=True)
            return
        if cmd_status == E.DUPLICITE_BET:
            await CommandHandler.send(f"Player {CommandHandler.get_info(source).display_name} has successfully bet another {bet} on {argv[1]}", source)
            return
        await CommandHandler.send(f"Player {CommandHandler.get_info(source).display_name} has successfully bet {bet} on {argv[1]}", source)

    #Override
    @staticmethod
    async def command_ready(game, source, argv):
        await RNGCmdHandler.command_ready(game, source, argv)
        if game.check_ready():
            await CommandHandler.send("All players are ready! Rolling!", source)
            await CoinflipCmdHandler.subcommand_roll(game, source, argv)

    #Override
    @staticmethod
    async def subcommand_roll(game, source, argv):
        winning_bets: list[RNGBet] = game.roll()
        side = "HEADS" if CoinflipSides(game.last_roll) == CoinflipSides.HEADS else "TAILS"
        await CommandHandler.send(f"The winning side is: {side}!", source)
        await CommandHandler.send(game.build_winners_message(winning_bets), source)
        if game.give_winnings(winning_bets) == E.INV_PLAYER:
            await CommandHandler.send(f"One or more players could not collect their winning because they left the game :(", source)
        game.restart_game()
        await CommandHandler.send(f"The game has been restarted, bet and try your luck again!", source)

    commands_dict: dict[str, Callable[[commands.Context, list[str]], Awaitable[None]]] = {
        "bet": command_bet,
        "ready": command_ready
    }

class RollTheDiceCmdHandler(RNGCmdHandler):
    # Override
    @staticmethod
    async def command_run(game: RollTheDice, source: commands.Context | discord.Interaction, argv: list[str]):
        command = argv[0]
        if RollTheDiceCmdHandler.commands_dict.get(command, None) is None:
            if RNGCmdHandler.commands_dict.get(command, None) is None:
                await CommandHandler.send(f"Unknown command, run !help {game.name} for available commands", source, ephemeral=True)
                return
            await RNGCmdHandler.commands_dict[command](game, source, argv)
            return
        await RollTheDiceCmdHandler.commands_dict[command](game, source, argv)

    @staticmethod
    async def command_bet(game: RollTheDice, source, argv):
        if len(argv) != 4 or argv[1] not in ["sum", "doubles"]:
            await RNGCmdHandler.inv_args_message(game, source)
            return
        try:
            bet_type = argv[1]
            input_number = int(argv[2])
            bet = int(argv[3])
        except ValueError:
            await CommandHandler.send(f"Invalid format of the command, both selected sum/number for doubles and the value of the bet must be whole numbers.", source, ephemeral=True)
            return
        number = -input_number if bet_type == "doubles" else input_number
        cmd_status: E = game.place_bet(CommandHandler.get_info(source), bet, number, game.get_rate(number))
        if cmd_status == E.INV_PLAYER:
            await CommandHandler.send(f"{CommandHandler.get_info(source).mention} You are not in the game! You must use !{game.name} join to participate", source, ephemeral=True)
            return
        if cmd_status == E.OUT_OF_RANGE:
            await CommandHandler.send(f"{CommandHandler.get_info(source).mention} The number you have written is out of range, bet on sums between 2 and 12 or on doubles", source, ephemeral=True)
            return
        if cmd_status == E.INSUFFICIENT_FUNDS:
            await CommandHandler.send(f"{CommandHandler.get_info(source).mention} You don't have enough money in your balance. Try again with less!", source, ephemeral=True)
            return
        bet_type_message = "sum of" if bet_type == "sum" else "double"
        if cmd_status == E.DUPLICITE_BET:
            await CommandHandler.send(f"Player {CommandHandler.get_info(source).display_name} has successfully bet another {bet} on {bet_type_message} {input_number}", source)
            return
        await CommandHandler.send(f"Player {CommandHandler.get_info(source).display_name} has successfully bet {bet} on {bet_type_message} {input_number}", source)
    
    #Override
    @staticmethod
    async def command_ready(game: RollTheDice, source, argv):
        await RNGCmdHandler.command_ready(game, source, argv)
        if game.check_ready():
            await CommandHandler.send("All players are ready! Rolling!", source)
            await RollTheDiceCmdHandler.subcommand_roll(game, source, argv)

    #Override
    @staticmethod
    async def subcommand_roll(game: RollTheDice, source, argv):
        winning_bets: list[RNGBet] = game.roll()
        conclusion_message = game.build_conclusion_message(winning_bets) + 25 * '-' + '\n'
        if game.give_winnings(winning_bets) == E.INV_PLAYER:
           conclusion_message += f"One or more players could not collect their winning because they left the game :(\n"
        game.restart_game()
        conclusion_message += f"The game has been restarted, bet and try your luck again!"
        await CommandHandler.send(f"```{conclusion_message}```", source)

    commands_dict: dict[str, Callable[[commands.Context, list[str]], Awaitable[None]]] = {
        "bet": command_bet,
        "ready": command_ready
    }

class RouletteCmdHandler(RNGCmdHandler):

    # Override
    @staticmethod
    async def command_run(game: Roulette, ctx: commands.Context, argv: list[str]):
        command = argv[0]
        if RouletteCmdHandler.commands_dict.get(command, None) is None:
            if RNGCmdHandler.commands_dict.get(command, None) is None:
                await ctx.send(f"Unknown command, run !help {game.name} for available commands")
                return
            await RNGCmdHandler.commands_dict[command](game, ctx, argv)
            return
        await RouletteCmdHandler.commands_dict[command](game, ctx, argv)

    async def command_bet(game: RollTheDice, ctx, argv):
        if len(argv) != 4 or argv[1] not in ["number", "double", "quad", ]:
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
    
    commands_dict: dict[str, Callable[[commands.Context, list[str]], Awaitable[None]]] = {
        "bet": command_bet,
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

        winning_bets: list[RNGBet] = game.bets[winning_number]
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