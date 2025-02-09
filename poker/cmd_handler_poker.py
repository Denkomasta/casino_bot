from enums import GameType, GameState, E, PlayerState, BaccaratBetType, CoinflipSides, PokerPlayerState
from typing import Callable, Awaitable
from discord.ext import commands
from base_classes import Game
from poker.poker import Poker, PokerPot
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
            if not await PokerCmdHandler.check_blinds(game):
                return
            game_coroutine = PokerCmdHandler.game_coroutine(game)
            draw_coroutine = PokerCmdHandler.draw_coroutine(game)
            game.game_start()
            for round in range(4):
                while True:
                    coroutine_res = next(game_coroutine)
                    if coroutine_res == -1:
                        break
                    from poker.ui_poker import Poker_ingame
                    view = Poker_ingame(game, coroutine_res)
                    message = await game.channel.send(f"{game.players[coroutine_res].player_info.mention} has his turn:\n", view=view)
                    if (await view.wait()):
                        await PokerCmdHandler.cmd_default_action(game, source, ["whtvr"])
                    msg_txt = f"Player {game.players[coroutine_res].player_info.name} {PokerPlayerState(view.value).name}"
                    if view.value == PokerPlayerState.RAISED:
                        msg_txt += f" on {game.round_bet}"
                    if game.players[coroutine_res].state == PokerPlayerState.ALL_IN_CALLED or game.players[coroutine_res].state == PokerPlayerState.ALL_IN_RAISED:
                        msg_txt += " as ALL IN"
                    await message.edit(content=f"```\n   {msg_txt}   ```", view=None)
                if game.is_instand_win():
                    await PokerCmdHandler.poker_finish(game)
                    return
                if game.is_ready_to_get_all_cards():
                    while next(draw_coroutine):
                        continue
                    await PokerCmdHandler.poker_finish(game)
                    return
                if not next(draw_coroutine):
                    break
                await game.channel.send(f"```\n{game.show_game()}\n```")
                game.round_restart()
            await PokerCmdHandler.poker_finish(game)
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
        if (bet_value <= game.round_bet or bet_value > player.bet.value):
            await CommandHandler.send("Your input is not in the range, try again", source, ephemeral=True)
            return
        player.state = PokerPlayerState.RAISED
        if (bet_value == player.bet.value):
            player.state = PokerPlayerState.ALL_IN_RAISED
        game.raise_bet(bet_value, player.player_info)
        await CommandHandler.send(f"You have RAISED to {bet_value}{('' if player.state != PokerPlayerState.ALL_IN_RAISED else ' as ALL IN')}", source, ephemeral=True)

    @staticmethod
    async def cmd_call(game: Poker, source: commands.Context | discord.Interaction, args: list[str]) -> None:
        player = game.players.get(CommandHandler.get_id(source))
        if (game.round_bet >= player.bet.value):
            player.state = PokerPlayerState.ALL_IN_CALLED
            game.raise_bet(player.bet.value, player.player_info)
            await CommandHandler.send(f"You went ALL IN for {player.round_bet}", source, ephemeral=True)
            return
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
    async def poker_finish(game: Poker) -> None:
        if not game.is_instand_win():
            game.divide_pots()
            game.evaluate_winners()
        else:
            game.insta_win()
        await game.channel.send(f"```\n{game.show_game()}\n{game.show_players_after_game()}\n{game.show_winners()}```")
        game.game_restart()
        from ui import BetUI, JoinLeaveUI
        await game.channel.send("Are you new here? Do you want to join? Or you are bored already?", view=JoinLeaveUI(game, GameType.POKER))
        from poker.ui_poker import PokerBetUI
        await game.channel.send("Do you want to change your bank??", view=PokerBetUI(game))

    @staticmethod
    async def check_blinds(game: Poker) -> bool:
        rv = True
        small_blind_player = game.get_player_by_index(game.blind_index)
        big_blind_player = game.get_player_by_index(game.blind_index + 1)

        if small_blind_player.bet.value < game.blind // 2:
            rv = False
            small_blind_player.state = PokerPlayerState.NOT_READY
            await game.channel.send(f"Player {small_blind_player.player_info.mention} has less in a bank than is a small blind ({game.blind // 2}), increase your bank please")
        if big_blind_player.bet.value < game.blind:
            rv = False
            big_blind_player.state = PokerPlayerState.NOT_READY
            await game.channel.send(f"Player {big_blind_player.player_info.mention} has less in a bank than is a big blind ({game.blind}), increase your bank please")
        return rv




    @staticmethod
    def game_coroutine(game: Poker):
        for _ in range(4):
            index_player = (game.blind_index + 2) % len(game.players)
            last_player = index_player
            first = True
            while (first or index_player != last_player):
                first = False
                if game.get_player_by_index(index_player).state >= PokerPlayerState.FOLDED and game.get_player_by_index(index_player).state <= PokerPlayerState.ALL_IN_RAISED:
                    index_player = (index_player + 1) % len(game.players)
                    continue
                yield game.get_player_by_index(index_player).player_info.id
                if (game.get_player_by_index(index_player).state == PokerPlayerState.RAISED or game.get_player_by_index(index_player).state == PokerPlayerState.ALL_IN_RAISED):
                    last_player = index_player
                index_player = (index_player + 1) % len(game.players)
            yield (-1)

    @staticmethod
    def draw_coroutine(game: Poker):
        game.draw_cards(3)
        yield True
        game.draw_cards(1)
        yield True
        game.draw_cards(1)
        yield True
        yield False
    
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