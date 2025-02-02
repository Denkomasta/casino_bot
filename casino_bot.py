import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio
import signal
import sys
from database import Database
from blackjack.black_jack import BlackJack, Card, Player
from blackjack.cmd_handler_blackjack import BlackJackCmdHandler
from baccarat.baccarat import Baccarat
from baccarat.cmd_handler_baccarat import BaccaratCmdHandler
from base_classes import Game
from cmd_handler import CommandHandler
from enums import GameType
from ui import JoinUI, PlayUI, CreateUI
from rng_games.rng_games import Coinflip, RollTheDice, GuessTheNumber, Roulette
from rng_games.cmd_handler_rng import CoinflipCmdHandler, RollTheDiceCmdHandler, GuessNumberCmdHandler
from time import time
import traceback

Games: dict[(int, int), Game] = {}
Data: Database = Database()

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
BOTNAME = "DisCas"
CMD_PREFIX = "!"
CHAIN_DELIM = ";"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix=CMD_PREFIX, case_insensitive=True, intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

# command hello
@bot.command(name='hello', help='Replies with Hello!')
async def hello(ctx):
    await ctx.send(f'Hello, {ctx.author}!')

# command for testing
@bot.command(name='debug', help='Debugging')
async def debug(ctx):
    game = BlackJack()
    add_p1 =  game.add_player("Grazl", 10)
    game.deal_cards()
    show_card1 = game.show_game()
    game.player_hit("Grazl")
    game.player_stand("Grazl")
    show_card2 = game.show_game()
    game.crupiers_turn()
    show_card3 = game.show_game()
    game.evaluate()
    results = game.show_results()
    await ctx.send(f'show_cards1 =\n{show_card1}\nshow_cards2 =\n{show_card2}\nshow_cards3 =\n{show_card3}\nresults =\n{results}')

# command for playing
@bot.command(name='play', help='Choose game to play')
async def play(ctx: commands.Context):
    global Games
    global Data
    await CommandHandler.play(ctx, Games, Data)

# command for creating
@bot.command(name='create', help='Choose game to create')
async def create(ctx: commands.Context):
    global Games
    global Data
    await CommandHandler.create(ctx, Games, Data)

# command for daily drop
@bot.command(name='drop', help="Get your daily drop of money!")
async def drop(ctx: commands.Context):
    try:
        global Data
        if Data.data.get(str(ctx.author.id)) is None:
            await ctx.send(f"{ctx.author.mention} You must be a member of {BOTNAME} to participate!")
            return
        time_since_last = time() - Data.get_last_drop(ctx.author.id)
        if time_since_last < 86400:
            time_to_next = 86400 - time_since_last
            await ctx.send(f"You'll be able to get your next drop in {int(time_to_next // 3600)} hours and {int(time_to_next // (3600))} minutes")
            return
        Data.change_player_balance(ctx.author.id, 2000)
        Data.update_last_drop(ctx.author.id)
        await ctx.send(f"{ctx.author.mention} You got your daily drop of 2000 coins!")
    except Exception as e:
        traceback.print_exc()
        
# command subsribe
@bot.command(name='subscribe', help='Subscribe to casino to be able to play')
async def subscribe(ctx):
    if Data.add_player(ctx):
        await ctx.send(f'{ctx.author.global_name} is a new member of {BOTNAME}')
    else:
        await ctx.send(f'{ctx.author.global_name} is already a member of {BOTNAME}')

# command unsubsribe
@bot.command(name='unsubscribe', help='Delete your casino account', aliases=["delete", "leave"])
async def subscribe(ctx):
    curr_balance = Data.get_player_balance(ctx.author.id)
    if curr_balance < 0:
        await ctx.send(f'{ctx.author.global_name}, you cannot delete your account, because you are in debt ({curr_balance} coins)!')
        return
    Data.delete_player(ctx)
    await ctx.send(f'{ctx.author.global_name}\'s account was deleted.')

# command info
@bot.command(name='info', help=f'Displays information about {BOTNAME}!')
async def info(ctx):
    info_text = (
        f"**{BOTNAME}** is a fun and interactive casino bot for Discord!\n\n"
        "With this bot, you can:\n"
        "- Play various casino games like poker and more (coming soon!)\n"
        "- Check your balance and see how wealthy you are\n"
        "- Compete with others on the leaderboard\n"
        "- Pay other users and manage your casino account\n\n"
        "Some commands:\n"
        "- `!subscribe`: Subscribe to the casino and create an account\n"
        "- `!unsubscribe`: Delete your casino account\n"
        "- `!balance`: Check your current casino balance\n"
        "- `!leaderboard`: View the top players by balance\n"
        "- `!pay @user amount`: Pay another user a specified amount\n\n"
        "Stay tuned for more exciting features and games!"
    )
    await ctx.send(info_text)

# command balance
@bot.command(name='balance', help='Check your casino balance.')
async def balance(ctx):
    await ctx.send(f'{Data.get_player_name(ctx.author.id)} has casino balance: {Data.get_player_balance(ctx.author.id)}')

# command leaderboard
@bot.command(name='leaderboard', help='Check how wealthy are you.')
async def leaderboard(ctx):
    header = f"{'Rank':<5} {'Name':<25} {'Balance':<10}\n"
    header += "-" * 40 + "\n"
    
    rows = ""
    for i, (name, balance) in enumerate(Data.get_leaderboard()):
        rank = i + 1
        name = name[:25]
        rows += f"{rank:<5} {name:<25} {balance:<10}\n"

    table = header + rows 
    await ctx.send(f"```\n{table}\n```")    # Code formatting

# command pay
@bot.command(name='pay', help='Pay another user with !pay @user amount')
async def pay(ctx, mention: str = None, amount_s: str = None):
    sender = ctx.author
    if mention is None or amount_s is None:
        await ctx.send(f'{sender.mention}, please specify both a user and an amount. Example: `!pay @user 100`')
        return

    if any(role in ctx.message.content for role in ['@everyone', '@here']):
        await ctx.send(f'{sender.mention}, you cannot pay everyone.')
        return

    try:
        amount = int(amount_s)
    except ValueError:
        await ctx.send(f'{sender.mention}, the amount must be a valid integer.')
        return

    receiver = mention
    receiver_id = int(mention.strip('<>@!'))

    if not Data.is_player(receiver_id):
        await ctx.send(f'{sender.mention}, you cannot send money to {receiver} as he is not a DisCas member.')
        return

    if amount <= 0:
        await ctx.send(f'{sender.mention}, the amount must be positive.')
        return

    if sender.id == receiver_id:
        await ctx.send(f'{sender.mention}, you cannot pay yourself.')
        return

    if Data.get_player_balance(sender.id) < amount:
        await ctx.send(f'{sender.mention}, you do not have enough money to pay {amount} to {receiver}.')
        return

    #critical section
    Data.change_player_balance(sender.id, -amount)
    Data.change_player_balance(receiver_id, amount)
    #critical section

    await ctx.send(f'{sender.mention} paid {receiver} {amount} coins!')

# command blackjack
@bot.command(name='blackjack', aliases=["bj"])
async def blackjack(ctx: commands.Context, *, arg_str):
    """
    Play a game of blackjack!

    bj commands:
    * bj create - creates a new game of blackjack
    * bj join - joins existing game
    * bj leave - leaves existing game
    * bj bet [amount]
    * bj ready - you are ready for your game
    * bj unready
    * bj start - starts blackjack game
    * bj hit
    * bj stand
    * bj status
    * bj exit
    """

    argv = arg_str.split(' ')
    if (len(argv) > 2 or len(argv) < 1):
        await ctx.send(f'Invalid number of arguments')
    global Games
    if (argv[0] == "create"):
        if ((ctx.channel.id, GameType.BLACKJACK) in Games.keys()):
            await ctx.send(f'Game already exists in your channel, use \'exit\' first')
            return
        Games[(ctx.channel.id, GameType.BLACKJACK)] = BlackJack(Data, ctx.channel)
        await ctx.send(f'Game was created, join the game using \'join -bet-\' and start the game using \'start\'')
        await ctx.send(view=JoinUI(Games[(ctx.channel.id, GameType.BLACKJACK)], GameType.BLACKJACK))
        return
    if (argv[0] == "exit"):
        if ((ctx.channel.id, GameType.BLACKJACK) not in Games.keys()):
            await ctx.send(f'Game does not exist')
            return
        Games.pop((ctx.channel.id, GameType.BLACKJACK))
        await ctx.send(f'Game was exited')
        return
    if ((ctx.channel.id, GameType.BLACKJACK) not in Games.keys()):
            await ctx.send(f'Game does not exist, use \'!bj create\' to use commands')
            return
    await BlackJackCmdHandler.cmd_run(Games[(ctx.channel.id, GameType.BLACKJACK)], ctx, argv)

        # TODO add implementation of blackjack game

# command baccarat
@bot.command(name='baccarat', aliases=["bc"])
async def baccarat(ctx: commands.Context, *, arg_str):
    """
    Play a game of baccarat!

    bj commands:
    * bj create - creates a new game of blackjack
    * bj join - joins existing game
    * bj leave - leave existing game
    * bj bet [amount] [type]
    * bj ready - you are ready for your game
    * bj unready
    * bj exit
    """

    argv = arg_str.split(' ')
    if (len(argv) > 3 or len(argv) < 1):
        await ctx.send(f'Invalid number of arguments')
    global Games
    if (argv[0] == "create"):
        if ((ctx.channel.id, GameType.BACCARAT) in Games.keys()):
            await ctx.send(f'Game already exists in your channel, use \'exit\' first')
            return
        Games[(ctx.channel.id, GameType.BACCARAT)] = Baccarat(Data, ctx.channel)
        await ctx.send(f'Game was created, join the game using \'join -bet- -type-\' and start the game using \'start\'')
        await ctx.send(view=JoinUI(Games[(ctx.channel.id, GameType.BACCARAT)], GameType.BACCARAT))
        return
    if (argv[0] == "exit"):
        if ((ctx.channel.id, GameType.BACCARAT) not in Games.keys()):
            await ctx.send(f'Game does not exist')
            return
        Games.pop((ctx.channel.id, GameType.BACCARAT))
        await ctx.send(f'Game was exited')
        return
    if (argv[0] == "join" and len(argv) == 1):
        if ((ctx.channel.id, GameType.BACCARAT) not in Games.keys()):
            await ctx.send(f'Game does not exist')
            return
        await ctx.send(view=JoinUI(Games[(ctx.channel.id, GameType.BACCARAT)], GameType.BACCARAT))
        return
    if ((ctx.channel.id, GameType.BACCARAT) not in Games.keys()):
            await ctx.send(f'Game does not exist, use \'!bj create\' to use commands')
            return
    await BaccaratCmdHandler.cmd_run(Games[(ctx.channel.id, GameType.BACCARAT)], ctx, argv)

# command coinflip
@bot.command(name='coinflip', aliases=["cf"])
async def coinflip(ctx: commands.Context, *, arg_str: str):
    """
    Play a game of Coinflip!

    Coinflip commands:
    * cf create - creates a new game of coinflip
    * cf exit - removes existing game of coinflip from the current room
    * cf join - joins an existing game
    * cf leave - leaves the game you participate in
    * cf bet [heads/tails] [amount] - places a bet of "amount" on the selected option
    * cf ready - sets a player ready to flip the coin
    * cf unready - unsets the ready status
    * cf status - displays the status of the game
    * cf betlist - displays all currently placed bets
    """
    argv = arg_str.split(' ')
    if (len(argv) < 1):
        await ctx.send(f"No argument, run {CMD_PREFIX}cf help for available commands")
        return
    global Games
    if (argv[0] == "create"):
        if ((ctx.channel.id, GameType.COINFLIP) in Games.keys()):
            await ctx.send(f'Game already exists in your channel, use \'exit\' first')
            return
        Games[(ctx.channel.id, GameType.COINFLIP)] = Coinflip(Data, ctx.channel)
        await ctx.send(f"Game was created, join the game using \'join\'")
        return
    if (argv[0] == "exit"):
        if ((ctx.channel.id, GameType.COINFLIP) not in Games.keys()):
            await ctx.send(f'Game does not exist')
            return
        Games.pop((ctx.channel.id, GameType.COINFLIP))
        await ctx.send(f'Game was exited')
        return
    if ((ctx.channel.id, GameType.COINFLIP) not in Games.keys()):
            await ctx.send(f'Game does not exist, use \'!cf create\' to use commands')
            return
    try:
        await CoinflipCmdHandler.command_run(Games[(ctx.channel.id, GameType.COINFLIP)], ctx, argv)
    except Exception as e:
        print(e)

# command rollthedice
@bot.command(name='rollthedice', aliases=["rtd"])
async def rollthedice(ctx: commands.Context, *, arg_str: str):
    """
    Play a game of Roll the dice!

    Roll the dice commands:
    * rtd create - creates a new game of coinflip
    * rtd exit - removes existing game of coinflip from the current room
    * rtd join - joins an existing game
    * rtd leave - leaves the game you participate in
    * rtd bet [sum/doubles] [selected sum/number for doubles] [amount] - places a bet of "amount" on the selected option
    * rtd ready - sets a player ready to flip the coin
    * rtd unready - unsets the ready status
    * rtd status - displays the status of the game
    * rtd betlist - displays all currently placed bets
    """
    argv = arg_str.split(' ')
    if (len(argv) < 1):
        await ctx.send(f"No argument, run {CMD_PREFIX}rtd help for available commands")
        return
    global Games
    if (argv[0] == "create"):
        if ((ctx.channel.id, GameType.ROLLTHEDICE) in Games.keys()):
            await ctx.send(f'Game already exists in your channel, use \'exit\' first')
            return
        Games[(ctx.channel.id, GameType.ROLLTHEDICE)] = RollTheDice(Data, ctx.channel)
        await ctx.send(f'Game was created, join the game using \'join\'')
        return
    if (argv[0] == "exit"):
        if ((ctx.channel.id, GameType.ROLLTHEDICE) not in Games.keys()):
            await ctx.send(f'Game does not exist')
            return
        Games.pop((ctx.channel.id, GameType.ROLLTHEDICE))
        await ctx.send(f'Game was exited')
        return
    if ((ctx.channel.id, GameType.ROLLTHEDICE) not in Games.keys()):
            await ctx.send(f'Game does not exist, use \'!rtd create\' to use commands')
            return
    await RollTheDiceCmdHandler.command_run(Games[(ctx.channel.id, GameType.ROLLTHEDICE)], ctx, argv)

# command roulette
@bot.command(name='roulette', aliases=['rl'])
async def roulette(ctx: commands.Context, *, arg_str: str):
    """
    Play a game of Roll the dice!

    Coinflip commands:
    * rlt create - creates a new game of coinflip
    * rlt exit - removes existing game of coinflip from the current room
    * rlt join - joins an existing game
    * rlt leave - leaves the game you participate in
    * rlt bet [sum/doubles] [selected sum/number for doubles] [amount] - places a bet of "amount" on the selected option
    * rlt ready - sets a player ready to flip the coin
    * rlt unready - unsets the ready status
    * rlt status - displays the status of the game
    * rlt betlist - displays all currently placed bets
    """
    argv = arg_str.split(' ')
    if (len(argv) < 1):
        await ctx.send(f"No argument, run {CMD_PREFIX}rlt help for available commands")
        return
    global Games
    if (argv[0] == "create"):
        if ((ctx.channel.id, GameType.ROULETTE) in Games.keys()):
            await ctx.send(f'Game already exists in your channel, use \'exit\' first')
            return
        Games[(ctx.channel.id, GameType.ROULETTE)] = Roulette(Data, ctx.channel)
        await ctx.send(f'Game was created, join the game using \'join\'')
        return
    if (argv[0] == "exit"):
        if ((ctx.channel.id, GameType.ROULETTE) not in Games.keys()):
            await ctx.send(f'Game does not exist')
            return
        Games.pop((ctx.channel.id, GameType.ROULETTE))
        await ctx.send(f'Game was exited')
        return
    if ((ctx.channel.id, GameType.ROULETTE) not in Games.keys()):
            await ctx.send(f'Game does not exist, use \'!rlt create\' to use commands')
            return
    await RollTheDiceCmdHandler.command_run(Games[(ctx.channel.id, GameType.ROULETTE)], ctx, argv)

# command slots
@bot.command(name='slots', help='Play slot machine.')
async def slots(ctx):
    await ctx.send('Slots TBD')      # TODO add implementation of slots

@bot.command(name='GuessNumber', aliases=["gtn"])
async def GuessNumber(ctx: commands.Context, *, arg_str: str):
    """
    Play a game of Guess The Number (gtn)!

    gtn commands:
    * gtn create - creates a new game of guess then number
    * gtn exit - removes existing game of gtn from the current room
    * gtn join - joins an existing game
    * gtn leave - leaves the game you participate in
    * gtn guess [number] [amount] - places a bet of "amount" on the selected option
    * gtn ready - sets a player ready to flip the coin
    * gtn unready - unsets the ready status
    * gtn status - displays the status of the game
    * gtn bets - displays all currently placed bets
    """

    argv = arg_str.split(' ')
    if (len(argv) < 1):
        await ctx.send(f"No argument, run !cf help for available commands")
        return
    global Games
    key = (ctx.channel.id, GameType.GUESSNUMBER)
    if (argv[0] == "create"):
        if (key in Games.keys()):
            await ctx.send(f'Game already exists in your channel, use \'exit\' first')
            return

        try:
            Games[key] = GuessTheNumber(Data, ctx.channel)
        except Exception as e:
            print(f"Error creating game: {e}")
            await ctx.send(f'Error creating game')
            return

        await ctx.send(f'Game was created, join the game using \'join\'')
        return
    if (argv[0] == "exit"):
        if (key not in Games.keys()):
            await ctx.send(f'Game does not exist')
            return
        Games.pop(key)
        await ctx.send(f'Game was exited')
        return
    if (key not in Games.keys()):
        await ctx.send(f'Game does not exist, use \'{CMD_PREFIX}gtn create\' to use commands')
        return
    try:
        await GuessNumberCmdHandler.command_run(Games[key], ctx, argv)
    except Exception as e:
        print(e)

# command poker
@bot.command(name='poker', help='Play a game of poker.')
async def poker(ctx):
    await ctx.send('Poker TBD')      # TODO add implementation of poker

@bot.event
async def on_message(message):
    if message.author == bot.user or not message.content.startswith(CMD_PREFIX):
        return

    # nonsubscriber handling
    if not Data.is_player(message.author.id):
        if not (message.content.startswith(f"{CMD_PREFIX}subscribe") or message.content.startswith(f"{CMD_PREFIX}help") or message.content.startswith(f"{CMD_PREFIX}hello")):
            await message.channel.send(f'{message.author.mention}, you need to subscribe to be able to use {BOTNAME}, use {CMD_PREFIX}help if you are lost.')
            return

    # Command chaining
    cmds = message.content.split(CHAIN_DELIM)

    # Each command function needs to get its args using split.
    for cmd in cmds:
        message.content = cmd.strip()
        await bot.process_commands(message)


@bot.event
async def on_close():
    Data.save_stats()
    print("Bot disconnected, stats saved.")

def signal_handler(signal, frame):
    print("Gracefully shutting down...")
    Data.save_stats()
    asyncio.create_task(bot.close())
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

async def start_bot():
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(start_bot())