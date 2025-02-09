from enums import GameType, GameState, E, PlayerState, BaccaratBetType, CoinflipSides, PokerPlayerState
from typing import Callable, Awaitable
from discord.ext import commands
from base_classes import Game
from poker.poker import Poker
import traceback
from cmd_handler import CommandHandler
import discord

class PokerCmdHandler(CommandHandler):

    @staticmethod
    async def cmd_run(game: Poker, source: commands.Context | discord.Interaction, args: list[str]) -> None:
        if (len(args) == 0):
            await CommandHandler.send("There is no argument, use \"!help poker\" to see the options", source)
        if (args[0] not in PokerCmdHandler.command_dict.keys()):
            await CommandHandler.send("Invalid argument, use \"!help poker\" to see the options", source)
        await PokerCmdHandler.command_dict[args[0]](game, source, args)

    @staticmethod
    async def cmd_start(game: Poker, source: commands.Context | discord.Interaction, args: list[str]) -> None:
        try:
            coroutine = PokerCmdHandler.game_coroutine(game)
            game.game_start()
            for round in range(4):
                while True:
                    coroutine_res = next(coroutine)
                    if coroutine_res == -1:
                        break
                    from poker.ui_poker import Poker_ingame
                    view = Poker_ingame(game, coroutine_res)
                    message = await game.channel.send(f"{game.players[coroutine_res].player_info.mention} has his turn:\n", view=view)
                    if (await view.wait()):
                        await PokerCmdHandler.cmd_default_action(game, source, ["whtvr"])
                    msg_txt = f"Player {game.players[coroutine_res].player_info.mention} {PokerPlayerState(view.value).name}"
                    if view.value == PokerPlayerState.RAISED:
                        msg_txt += f" on {game.round_bet}"
                    await message.edit(content=msg_txt, view=None)
                if (round == 3):
                    break
                if (round == 0):
                    game.draw_cards(3)
                else:
                    game.draw_cards(1)
                await game.channel.send(f"```\n{game.show_game()}\n```")
                game.round_restart()
            await game.channel.send(f"```\n{game.show_game()}\n{game.show_players_after_game()}\n```")
            game.game_restart()
            from ui import BetUI, JoinLeaveUI
            await game.channel.send("Are you new here? Do you want to join? Or you are bored already?", view=JoinLeaveUI(game, GameType.POKER))
            from poker.ui_poker import PokerBetUI
            await game.channel.send("Do you want to change your bank??", view=PokerBetUI(game))
        except:
            traceback.print_exc()

    @staticmethod
    async def cmd_default_action(game: Poker, source: commands.Context | discord.Interaction, args: list[str]) -> None:
        player = game.players.get(CommandHandler.get_id(source))
        if player.round_bet < game.round_bet:
            await PokerCmdHandler.cmd_fold(game, source, args)
            return
        await PokerCmdHandler.cmd_check(game, source, args)

    @staticmethod
    async def cmd_check(game: Poker, source: commands.Context | discord.Interaction, args: list[str]) -> None:
        player = game.players.get(CommandHandler.get_id(source))
        player.state = PokerPlayerState.CHECKED
        await CommandHandler.send("You have CHECKED", source, ephemeral=True)


    @staticmethod
    async def cmd_raise(game: Poker, source: commands.Context | discord.Interaction, args: list[str]) -> None:
        try:
            bet_value = int(args[1])
        except:
            await CommandHandler.send("Enter a number", source, ephemeral=True)
            return
        player = game.players.get(CommandHandler.get_id(source))
        player.state = PokerPlayerState.RAISED
        game.raise_bet(bet_value, player.player_info)
        await CommandHandler.send(f"You have RAISED to {bet_value}", source, ephemeral=True)

    @staticmethod
    async def cmd_call(game: Poker, source: commands.Context | discord.Interaction, args: list[str]) -> None:
        player = game.players.get(CommandHandler.get_id(source))
        player.state = PokerPlayerState.CALLED
        game.raise_bet(game.round_bet, player.player_info)
        await CommandHandler.send(f"You have CALLED to {game.round_bet}", source, ephemeral=True)

    @staticmethod
    async def cmd_fold(game: Poker, source: commands.Context | discord.Interaction, args: list[str]) -> None:
        player = game.players.get(CommandHandler.get_id(source))
        player.state = PokerPlayerState.FOLDED
        await CommandHandler.send("You have FOLDED", source, ephemeral=True)

    @staticmethod
    async def cmd_status(game: Poker, source: commands.Context | discord.Interaction, args: list[str]) -> None:
        message = game.get_banklist_msg()
        await CommandHandler.send(f"```{message}```", source, ephemeral=True)

    @staticmethod
    async def cmd_bank(game: Poker, source: commands.Context | discord.Interaction, args: list[str]) -> None:
        message = f"You have {game.players[source.user.id].bet.value} in your in-game bank. You can change it between each game!\n"
        message += f"You have {game.players[source.user.id].round_bet} currently on the table!"
        await CommandHandler.send(f"```{message}```", source, ephemeral=True)

    # Only interaction
    @staticmethod
    async def cmd_show_cards(game: Poker, source: commands.Context | discord.Interaction, args: list[str]) -> None:
        player = game.players.get(CommandHandler.get_id(source))
        if player is None:
            await CommandHandler.send("You are not in the game, join after round ends", source, ephemeral=True)
            return
        show = ""
        if (game.players[CommandHandler.get_id(source)].state != PokerPlayerState.FOLDED):
            show += "Your cards are:\n"
        else:
            show += "Your cards were:\n"
        await CommandHandler.send(f"```{show}{player.show_cards()}```", source, ephemeral=True)

    @staticmethod
    def game_coroutine(game: Poker):
        for _ in range(4):
            index_player = (game.blind_index + 2) % len(game.players)
            last_player = index_player
            first = True
            while (first or index_player != last_player):
                first = False
                if list(game.players.values())[index_player].state == PokerPlayerState.FOLDED:
                    index_player = (index_player + 1) % len(game.players)
                    continue
                yield list(game.players.values())[index_player].player_info.id
                if list(game.players.values())[index_player].state == PokerPlayerState.RAISED:
                    last_player = index_player
                index_player = (index_player + 1) % len(game.players)
            yield (-1)

            

    
    command_dict: dict[str, Callable[[Poker, commands.Context | discord.Interaction, list[str]], Awaitable[None]]] = {
        "join": CommandHandler.cmd_join,
        "leave": CommandHandler.cmd_leave,
        "start": cmd_start,
        "ready": CommandHandler.cmd_ready,
        "unready": CommandHandler.cmd_unready,
        "check": cmd_check,
        "raise": cmd_raise,
        "fold": cmd_fold,
        "bet": CommandHandler.cmd_bet,
        "status": cmd_status,
        "bank": cmd_bank
    }