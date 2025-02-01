from enums import GameType, GameState, E, PlayerState, BaccaratBetType
from typing import Callable, Awaitable
from discord.ext import commands
from base_classes import Game
from black_jack import BlackJack
from baccarat import Baccarat
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
            from ui import BlackJackHitStandUI
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
        await game.channel.send("Do you want to change your bet??", view=BetUI(game))
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
        from ui import ReadyUI, BaccaratBetUI, JoinLeaveUI
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