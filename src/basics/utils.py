import discord, os, requests
from dotenv import load_dotenv
from shared import type_dict

load_dotenv()
SECRET_CHANNEL_ID = os.getenv('SECRET_CHANNEL_ID')

def is_secret_channel(ctx):
    return ctx.channel.id == int(SECRET_CHANNEL_ID)

def translate(str):
    if str.lower() in type_dict:
        return type_dict[str.lower()]
    else:
        return str

def merge(l1, l2, r1, r2, n1, n2):
    merge = set(l1)
    for w in l2:
        if w not in r1 and w not in r2 and w not in n1 and w not in n2:
            merge.add(w)
    for r in r2:
        if r in merge:
            merge.remove(r)
    for n in n1:
        if n in merge:
            merge.remove(n)
    for n in n2:
        if n in merge:
            merge.remove(n)
    for w in merge:
        if w in l1 and w in l2:
            merge.remove(w)
            w += " (x4)"
            merge.add(w)
    return merge

def calculate_typing(response1, response2, user):
    ddf1 = response1['damage_relations']['double_damage_from']
    ddt1 = response1['damage_relations']['double_damage_to']
    hdf1 = response1['damage_relations']['half_damage_from']
    ndf1 = response1['damage_relations']['no_damage_from']
    ndt1 = response1['damage_relations']['no_damage_to']

    ddf1 = [translate(d['name']) for d in ddf1]
    ddt1 = [translate(s['name']) for s in ddt1]
    hdf1 = [translate(r['name']) for r in hdf1]
    ndf1 = [translate(nd['name']) for nd in ndf1]
    ndt1 = [translate(nd['name']) for nd in ndt1]

    if response2 is not None:
        response2 = response2.json()
        ddf2 = response2['damage_relations']['double_damage_from']
        ddt2 = response2['damage_relations']['double_damage_to']
        hdf2 = response2['damage_relations']['half_damage_from']
        ndf2 = response2['damage_relations']['no_damage_from']
        ndt2 = response2['damage_relations']['no_damage_to']

        ddf2 = [translate(d['name']) for d in ddf2]
        ddt2 = [translate(s['name']) for s in ddt2]
        hdf2 = [translate(r['name']) for r in hdf2]
        ndf2 = [translate(nd['name']) for nd in ndf2]
        ndt2 = [translate(nd['name']) for nd in ndt2]

        mddf = merge(ddf1, ddf2, hdf1, hdf2, ndf1, ndf2)
        mddt = ddt1 + ddt2
        mhdf = merge(hdf1, hdf2, ddf1, ddf2, ndf1, ndf2)
        mndf = ndf1 + ndf2
    else:
        mddf = ddf1
        mddt = ddt1
        mhdf = hdf1
        mndf = ndf1

    des = f"{user}, aquí tienes las debilidades y resistencias de: " + translate(response1['name'])
    if response2 is not None:
        des += " y " + translate(response2['name'])
    embed = discord.Embed(title=des, description="", color=0xFFA500)
    if len(mddf) > 0:
        embed.add_field(name="Debilidades", value=", ".join(mddf), inline=False)
    else:
        embed.add_field(name="Este pokémon no tiene debilidades", value="Ninguna", inline=False)
    if len(mhdf) > 0:
        embed.add_field(name="Resistencias", value=", ".join(mhdf), inline=False)
    else:
        embed.add_field(name="Este pokémon no tiene resistencias", value="Ninguna", inline=False)
    if len(mddt) > 0:
        embed.add_field(name="Hace más daño a", value=", ".join(mddt), inline=False)
    else:
        embed.add_field(name="Este pokémon no hace x2 de daño a ningún tipo", value="Ninguno", inline=False)
    if len(mndf) > 0:
        embed.add_field(name="Inmunidades", value=", ".join(mndf), inline=False)
    else:
        embed.add_field(name="Este pokémon no tiene inmunidades", value="Ninguna", inline=False)
    
    return embed

def get_color(avg):
    if avg < 50:
        return(0xff0000)
    elif avg < 100:
        return(0xffff00)
    else:
        return(0x0000ff)
    
async def get_pk_info(ctx, name, f=False, s=False, count=0):
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
        if f and s:
            name = f"{name} ✨"
            image_url = data['sprites']['other']['showdown']['front_shiny']
            if image_url is None:
                image_url = data['sprites']['front_shiny']
        else:
            image_url = data['sprites']['other']['showdown']['front_default']
            if image_url is None:
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
        des = f"**[{data['id']}] Este pokémon {info}**"
        name = data['name'].capitalize()
        if f:
            if s:
                name = name + " ✨"
            name = name + " de " + ctx.author.name + f" ({count})"
        embed = discord.Embed(title=name.capitalize(), description=des, color=color)
        embed.set_thumbnail(url=image_url)
        embed.add_field(name="Tipos", value=", ".join(types), inline=False)
        embed.add_field(name="Total de stats", value=total, inline=False)
        embed.add_field(name="Estadísticas", value="\n".join(stats), inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("Pokémon no encontrado, comprueba que has escrito bien el nombre y que el pokémon existe")