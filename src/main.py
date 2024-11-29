import os
import discord
from dotenv import load_dotenv
from discord.ext import commands
import cmds
import cmd_db

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
SPECIFIC_CHANNEL_ID1 = int(os.getenv('SPECIFIC_CHANNEL_ID1'))
SPECIFIC_CHANNEL_ID2 = int(os.getenv('SPECIFIC_CHANNEL_ID2'))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='+', intents=intents)

@bot.event
async def on_ready():
	print(f'{bot.user.name} has connected to Discord!')

def is_in_specific_channel(ctx):
    return ctx.channel.id == SPECIFIC_CHANNEL_ID1 or ctx.channel.id == SPECIFIC_CHANNEL_ID2

bot.add_command(cmds.ping)
bot.add_command(cmds.mondongo)
bot.add_command(cmds.da2)
bot.add_command(cmds.pkinfo)
bot.add_command(cmds.tipos)
bot.add_command(cmd_db.muertes)
bot.add_command(cmd_db.addUser)
bot.add_command(cmd_db.addDeath)

@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, commands.errors.MissingRequiredArgument) and ctx.command.name == "da2":
		await ctx.send("Falta la cantidad de caras del dado, usa +da2 <cantidad_de_caras>")
	if isinstance(error, commands.errors.MissingRequiredArgument) and ctx.command.name == "pkinfo":
		await ctx.send("Falta el nombre del pokémon, usa +pkinfo <nombre_del_pokemon>")
	if isinstance(error, commands.errors.MissingRequiredArgument) and ctx.command.name == "tipos":
		await ctx.send("Falta uno o dos tipos, usa +tipos <tipo1> (<tipo2>) ")

bot.run(TOKEN)