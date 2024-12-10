import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
botname = "DisCas"

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

# command hello
@bot.command(name='hello', help='Replies with Hello!')
async def hello(ctx):
    await ctx.send(f'Hello, {ctx.author}!')

# command info
@bot.command(name='info', help=f'Information about {botname}!')
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
async def coinflip(ctx):
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
    if message.author == bot.user:
        return

    await bot.process_commands(message)


bot.run(token)