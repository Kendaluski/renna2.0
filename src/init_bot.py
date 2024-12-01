import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import cmds, cmd_db, catches, fights, shared


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
SECRET = os.getenv('SECRET_MESSAGE')
SECRET2 = os.getenv('SECRET_MESSAGE2')
ENV = os.getenv('ENV')
TEST_SERVER_ID = os.getenv('TEST_SERVER_ID')

intents = discord.Intents.default()
intents.message_content = True
shared.bot = commands.Bot(command_prefix='+', intents=intents)

@shared.bot.event
async def on_ready():
    print(f'{shared.bot.user.name} has connected to Discord!')

@shared.bot.event
async def on_message(message):
    if message.author == shared.bot.user:
        return
    if ENV == "dev" and message.guild.id != int(TEST_SERVER_ID):
        return
    if ENV == "prod" and message.guild.id == int(TEST_SERVER_ID):
        return
    cont = message.content.lower()
    if SECRET.lower() in cont:
        await message.channel.send("Que sí locu que sí")
    if SECRET2.lower() in cont:
        await message.channel.send("Que sí any que tienes novio")
    await shared.bot.process_commands(message)

@shared.bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument) and ctx.command.name == "da2":
        await ctx.send("Falta la cantidad de caras del dado, usa +da2 <cantidad_de_caras>")

# Register commands
shared.bot.add_command(cmds.ping)
shared.bot.add_command(cmds.mondongo)
shared.bot.add_command(cmds.da2)
shared.bot.add_command(cmds.pkinfo)
shared.bot.add_command(cmds.tipos)
shared.bot.add_command(cmd_db.muertes)
shared.bot.add_command(cmd_db.addUser)
shared.bot.add_command(cmd_db.addDeath)
shared.bot.add_command(catches.pkc)
shared.bot.add_command(catches.pkl)
shared.bot.add_command(fights.fight)
shared.bot.add_command(fights.cp)
shared.bot.add_command(fights.wins)
shared.bot.add_command(fights.rcd)

def run_bot():
    shared.bot.run(TOKEN)