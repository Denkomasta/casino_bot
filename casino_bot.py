import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

# command hello
@bot.command(name='hello', help='Replies with Hello!')
async def hello(ctx):
    await ctx.send(f'Hello, {ctx.author}!')


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    await bot.process_commands(message)


bot.run(token)