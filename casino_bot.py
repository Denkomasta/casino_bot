import discord
from discord.ext import commands
from dotenv import load_dotenv
from cmd_handler import BlackJackCmdHandler
import os
import asyncio
import signal
import sys
from database import Database
from black_jack import BlackJack, Card, Player

Games: dict[int, BlackJack] = {}
Data: Database = Database()

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
BOTNAME = "DisCas"
CMD_PREFIX = "!"
CHAIN_DELIM = ";"

intents = discord.Intents.default()
intents.message_content = True
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
    for i, (_, player_info) in enumerate(Data.get_leaderboard()):
        rank = i + 1
        name = player_info['name'][:25]
        balance = player_info['balance']
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
async def blackjack(ctx, *, arg_str):
    """
    Play a game of blackjack!

    bj commands:
    * bj create - creates a new game of blackjack
    * bj join - joins existing game
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
        if (ctx.channel.id in Games.keys()):
            await ctx.send(f'Game already exists in your channel, use \'exit\' first')
            return
        Games[ctx.channel.id] = BlackJack(Data)
        await ctx.send(f'Game was created, join the game using \'join -bet-\' and start the game using \'start\'')
        return
    if (argv[0] == "exit"):
        if (ctx.channel.id not in Games.keys()):
            await ctx.send(f'Game does not exist')
            return
        Games.pop(ctx.channel.id)
        await ctx.send(f'Game was exited')
        return
    if (ctx.channel.id not in Games.keys()):
            await ctx.send(f'Game does not exist, use \'!bj create\' to use commands')
            return
    await BlackJackCmdHandler.cmd_run(Games[ctx.channel.id], ctx, argv)

        # TODO add implementation of blackjack game

# command coinflip
@bot.command(name='coinflip', help='Flip a coin.')
async def coinflip(ctx):
    await ctx.send('Coinflip TBD')      # TODO add implementation of coinflip

# command roulette
@bot.command(name='roulette', help='Spin a roulette.')
async def roulette(ctx):
    await ctx.send('Roulette TBD')      # TODO add implementation of roulette

# command slots
@bot.command(name='slots', help='Play slot machine.')
async def slots(ctx):
    await ctx.send('Slots TBD')      # TODO add implementation of slots

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