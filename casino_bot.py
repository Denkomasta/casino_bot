import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import json

import black_jack

def load_stats():   # returns dict
    try:
        with open("player_stats.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_stats():
    with open("player_stats.json", "w") as f:
        json.dump(player_stats, f, indent=4)

player_stats = load_stats() # TODO how to handle this global variable

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
    game = black_jack.BlackJack()
    add_p1 =  game.add_player("Grazl", 10)
    add_p2 =  game.add_player("Čurin")
    add_p3 =  game.add_player("Šmajdalf", 10)
    add_p4 =  game.add_player("Grazl")
    game.give_cards()
    format_cards = game.format_cards()
    await ctx.send(f'Blackjack debug:\nadd_player1 = {add_p1}\nadd_player2 = {add_p2}\nadd_player3 = {add_p3}\nadd_player4 = {add_p4}\n format_cards = {format_cards}')

# command subsribe
@bot.command(name='subscribe', help='Subscribe to casino to be able to play')
async def subscribe(ctx):
    if ctx.author not in player_stats.keys():
        player_stats[(ctx.author.id, ctx.author.global_name)] = 10     # TODO What do we want to save?
        await ctx.send(f'{ctx.author} is new member of {BOTNAME}')
    else:
        await ctx.send(f'{ctx.author} is already a member of {BOTNAME}')

# command info
@bot.command(name='info', help=f'Information about {BOTNAME}!')
async def info(ctx):
    await ctx.send('I am nothing')     # TODO add info about bot

# command balance
@bot.command(name='balance', help='Check your casino balance.')
async def balance(ctx):
    await ctx.send('Balance TBD')      # TODO add implementation of balance

# command leaderboard
@bot.command(name='leaderboard', help='Check how wealthy are you.')
async def leaderboard(ctx):
    await ctx.send('Leaderboard TBD')      # TODO add implementation of leaderboard

# command pay
@bot.command(name='pay', help='Pay another user money.')
async def pay(ctx):
    await ctx.send('Pay TBD')      # TODO add implementation of pay

# command blackjack
@bot.command(name='blackjack', help='Play a game of blackjack.')
async def blackjack(ctx):
    await ctx.send('Blackjack TBD')     # TODO add implementation of blackjack game

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

    # Command chaining
    cmds = message.content.split(CHAIN_DELIM)

    # Each command function needs to get its args using split.
    for cmd in cmds:
        message.content = cmd.strip()
        await bot.process_commands(message)


# saving data about players to json file - TODO doesnt work with signals
@bot.event
async def on_close():
    save_stats()

bot.run(TOKEN)