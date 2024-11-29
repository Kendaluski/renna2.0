from discord.ext import commands
import random
import requests
import discord
from utils import translate, calculate_typing

@commands.command(name='ping', help="Este comando retorna pong, sirve para comprobar si el bot está activo")
async def ping(ctx):
    await ctx.send('pong')

@commands.command(name='mondongo', help="Sorpresa lokete")
async def mondongo(ctx):
    await ctx.send('jeje goz')

@commands.command(name='da2', help="Este comando tira un dado de X caras")
async def da2(ctx, caras: int):
    res = random.randint(1, caras)
    await ctx.send("Y ha salido un... " + str(res))

@commands.command(name="pkinfo", help="Este comando muestra información del pokémon deseado, el nombre, los tipos y sus estadísticas")
async def pkinfo(ctx, name: str):
    response = requests.get(f'https://pokeapi.co/api/v2/pokemon/{name.lower()}')
    if response.status_code == 200:
        data = response.json()
        stats = []
        total = 0
        for stat in data['stats']:
            sname = stat['stat']['name']
            if sname == "hp":
                sname = "PS"
            if sname == "attack":
                sname = "Ataque"
            if sname == "defense":
                sname = "Defensa"
            if sname == "special-attack":
                sname = "Ataque Especial"
            if sname == "special-defense":
                sname = "Defensa Especial"
            if sname == "speed":
                sname = "Velocidad"
            
            svalue = stat['base_stat']
            total += svalue
            bar = "█" * int(svalue / 5)
            stats.append(f"{sname}: {svalue} \n {bar}")
        image_url = data['sprites']['front_default']

        avg_stats = total / len(data['stats'])
        avg_stats = round(avg_stats, 1)
        if avg_stats < 50:
            color = 0xff0000
            info = "es un mierdón"
        elif avg_stats < 100:
            color = 0xffff00
            info = "cumple su función"
        else:
            color = 0x0000ff
            info = "es god lokete"

        types = [translate(t['type']['name']) for t in data['types']]
        des = f"**Este pokémon {info}**"

        embed = discord.Embed(title=name.capitalize(), description=des, color=color)
        embed.set_thumbnail(url=image_url)
        embed.add_field(name="Tipos", value=", ".join(types), inline=False)
        embed.add_field(name="Promedio de stats", value=avg_stats, inline=False)
        embed.add_field(name="Estadísticas", value="\n".join(stats), inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("Pokémon no encontrado, comprueba que has escrito bien el nombre y que el pokémon existe")

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
