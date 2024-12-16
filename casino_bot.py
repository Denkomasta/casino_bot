import discord
from discord.ext import commands
from dotenv import load_dotenv
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

# command info
@bot.command(name='info', help=f'Information about {BOTNAME}!')
async def info(ctx):
    await ctx.send('I am nothing')     # TODO add info about bot

# command balance
@bot.command(name='balance', help='Check your casino balance.')
async def balance(ctx):
    await ctx.send(f'{Data.get_player_name(ctx.author.id)} has casino balance: {Data.get_player_balance(ctx.author.id)}')

# command leaderboard
@bot.command(name='leaderboard', help='Check how wealthy are you.')
async def leaderboard(ctx):
    await ctx.send('Leaderboard TBD')      # TODO add implementation of leaderboard

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
@bot.command(name='blackjack', help='Play a game of blackjack.', aliases=["bj"])
async def blackjack(ctx, *, arg_str):
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
    await Games[ctx.channel.id].cmd_run(ctx, argv)

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

    # TODO notsubscriber handling

    # Command chaining
    cmds = message.content.split(CHAIN_DELIM)

    # Each command function needs to get its args using split.
    for cmd in cmds:
        message.content = cmd.strip()
        await bot.process_commands(message)


# saving data about players to json file - TODO doesnt work with signals
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

async def start_bot():
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(start_bot())