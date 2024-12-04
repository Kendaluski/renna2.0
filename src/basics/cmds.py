from discord.ext import commands
import random
import requests
import discord
from basics.utils import translate, calculate_typing, get_pk_info

@commands.command(name='ping', help="Este comando retorna pong, sirve para comprobar si el bot está activo")
async def ping(ctx):
    await ctx.send('pong')
ping.category = "Básicos"

@commands.command(name='mondongo', help="Sorpresa lokete")
async def mondongo(ctx):
    await ctx.send('jeje goz')
mondongo.category = "Básicos"

@commands.command(name='da2', help="Este comando tira un dado de X caras")
async def da2(ctx, caras: int):
    res = random.randint(1, caras)
    await ctx.send("Y ha salido un... " + str(res))
da2.category = "Básicos"

@commands.command(name="pkinfo", help="Este comando muestra información del pokémon deseado, el nombre, los tipos y sus estadísticas")
async def pkinfo(ctx, name: str):
    await get_pk_info(ctx, name)
pkinfo.category = "Info Pokémon"

@commands.command(name="tipos", help="Este comando recibe uno o varios tipos de pokémon y retorna sus debilidades y resistencias")
async def tipos(ctx, *args):
    if len(args) == 0 or len(args) > 2:
        await ctx.send("Debes ingresar uno o dos tipos")
        return
    if len(args) == 1:
        type1 = translate(args[0])
        response1 = requests.get(f'https://pokeapi.co/api/v2/type/{type1.lower()}')
        type2 = None
        response2 = None
    else:
        type1 = translate(args[0])
        type2 = translate(args[1])
        response1 = requests.get(f'https://pokeapi.co/api/v2/type/{type1.lower()}')
        response2 = requests.get(f'https://pokeapi.co/api/v2/type/{type2.lower()}')
    if response1.status_code != 200:
        await ctx.send(f"Tipo **{type1}** no encontrado, asegúrate que existe y lo has escrito bien")
        return
    if response2 is not None and response2.status_code != 200:
        await ctx.send(f"Tipo **{type2}** no encontrado, asegúrate que existe y lo has escrito bien")
        return
    embed = calculate_typing(response1.json(), response2)
    await ctx.send(embed=embed)
tipos.category = "Info Pokémon"