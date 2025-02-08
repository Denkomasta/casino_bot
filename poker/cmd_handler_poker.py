from enums import GameType, GameState, E, PlayerState, BaccaratBetType, CoinflipSides, PokerPlayerState
from typing import Callable, Awaitable
from discord.ext import commands
from base_classes import Game
from poker.poker import Poker
from poker.ui_poker import Poker_ingame
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
        coroutine = PokerCmdHandler.game_coroutine(game)
        for round in range(4):
            while True:
                coroutine_res = next(coroutine)
                if coroutine_res == -1:
                    break
                view = Poker_ingame(game, coroutine_res)
                message = game.channel.send(f"{game.players[coroutine_res].player_info.mention} has his turn:\n", view=view)
                if view.wait():
                    await PokerCmdHandler.cmd_default_action(game, source, ["whtvr"])
                msg_txt = f"Player {game.players[coroutine_res].player_info.mention} {PokerPlayerState(view.value).name}"
                if view.value == PokerPlayerState.RAISED:
                    msg_txt += f" on {game.round_bet}"
                await message.edit(msg_txt)
            if (round == 3):
                break
            if (round == 0):
                game.draw_cards(3)
            else:
                game.draw_cards(1)
            await game.channel.send(f"{game.show_game()}")

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
        player.raise_bet(bet_value)
        game.round_bet = bet_value
        await CommandHandler.send(f"You have RAISED to {bet_value}", source, ephemeral=True)

    @staticmethod
    async def cmd_call(game: Poker, source: commands.Context | discord.Interaction, args: list[str]) -> None:
        player = game.players.get(CommandHandler.get_id(source))
        player.state = PokerPlayerState.CALLED
        player.raise_bet(game.round_bet)
        await CommandHandler.send(f"You have CALLED to {game.round_bet}", source, ephemeral=True)

    @staticmethod
    async def cmd_fold(game: Poker, source: commands.Context | discord.Interaction, args: list[str]) -> None:
        player = game.players.get(CommandHandler.get_id(source))
        player.state = PokerPlayerState.FOLDED
        await CommandHandler.send("You have FOLDED", source, ephemeral=True)

    @staticmethod
    async def cmd_status(game: Poker, source: commands.Context | discord.Interaction, args: list[str]) -> None:
        pass

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
        await CommandHandler.send(f"```{show}{player.show_cards()}```")

    @staticmethod
    def game_coroutine(game: Poker):
        for round in range(4):
            index_player = (game.blind_index + 2) % len(game.players)
            last_player = (index_player - 1) % len(game.players)
            while (index_player) != last_player:
                if game.players[index_player].state == PokerPlayerState.FOLDED:
                    index_player = (index_player + 1) % len(game.players)
                    continue
                yield game.players[index_player].player_info.id
                if game.players[index_player].state == PokerPlayerState.RAISED:
                    last_player = (index_player - 1) % len(game.players)
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
    }