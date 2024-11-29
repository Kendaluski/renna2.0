import discord
import os
from dotenv import load_dotenv

def translate(str):
    if str == "bug":
        return "Bicho"
    if str == "dark":
        return "Siniestro"
    if str == "dragon":
        return "Dragón"
    if str == "electric":
        return "Eléctrico"
    if str == "fairy":
        return "Hada"
    if str == "fighting":
        return "Lucha"
    if str == "fire":
        return "Fuego"
    if str == "flying":
        return "Volador"
    if str == "ghost":
        return "Fantasma"
    if str == "grass":
        return "Planta"
    if str == "ground":
        return "Tierra"
    if str == "ice":
        return "Hielo"
    if str == "normal":
        return "Normal"
    if str == "poison":
        return "Veneno"
    if str == "psychic":
        return "Psíquico"
    if str == "rock":
        return "Roca"
    if str == "steel":
        return "Acero"
    if str == "water":
        return "Agua"
    if str.lower() == "bicho":
        return "Bug"
    if str.lower() == "siniestro":
        return "Dark"
    if str.lower() == "dragón" or str.lower() == "dragon":
        return "Dragon"
    if str.lower() == "eléctrico" or str.lower() == "electrico":
        return "Electric"
    if str.lower() == "hada":
        return "Fairy"
    if str.lower() == "lucha":
        return "Fighting"
    if str.lower() == "fuego":
        return "Fire"
    if str.lower() == "volador":
        return "Flying"
    if str.lower() == "fantasma":
        return "Ghost"
    if str.lower() == "planta":
        return "Grass"
    if str.lower() == "tierra":
        return "Ground"
    if str.lower() == "hielo":
        return "Ice"
    if str.lower() == "normal":
        return "Normal"
    if str.lower() == "veneno":
        return "Poison"
    if str.lower() == "psíquico" or str.lower() == "psiquico":
        return "Psychic"
    if str.lower() == "roca":
        return "Rock"
    if str.lower() == "acero":
        return "Steel"
    if str.lower() == "agua":
        return "Water"
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

def calculate_typing(response1, response2):
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

    des = "Debilidades y resistencias de: " + translate(response1['name'])
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
