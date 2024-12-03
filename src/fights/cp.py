import requests, discord, os, random, shared, asyncio, psycopg2
from discord.ext import commands
from dotenv import load_dotenv
from leagues.l_utils import n_l, pk_in_league
from basics.utils import get_color

load_dotenv()
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASS')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
ALT_ID = int(os.getenv('ALT_ID'))

async def fight(cursor, ctx, cid, cpkid, dpkid, conn, result):
    s1 = result[1]
    cursor.execute("SELECT pk_id, shiny FROM pcatches WHERE user_id = %s AND pk_id = %s", (cid, cpkid,))
    result = cursor.fetchone()
    s2 = result[1]
    cpk = shared.fight_data[ctx.author.id]['cpkid']
    dpk = dpkid
    res = requests.get(f'https://pokeapi.co/api/v2/pokemon/{cpk}')
    res2 = requests.get(f'https://pokeapi.co/api/v2/pokemon/{dpk}')
    if res.status_code == 200 and res2.status_code == 200:
        data1 = res.json()
        data2 = res2.json()
        avg1 = sum([stat['base_stat'] for stat in data1['stats']])
        avg2 = sum([stat['base_stat'] for stat in data2['stats']])
        embed1 = discord.Embed(title=f"{data1['name']} Retador", description=f"Stats: {avg1}", color=get_color(round(avg1 / len(data1['stats']), 1)))
        img1 = data1['sprites']['other']['showdown']['front_shiny'] if s2 else data1['sprites']['other']['showdown']['front_default']
        if img1 is None:
            img1 = data1['sprites']['front_shiny'] if s2 else data1['sprites']['front_default']
        embed1.set_image(url=img1)
        embed2 = discord.Embed(title=f"{data2['name']} Defensor", description=f"Stats: {avg2}", color=get_color(round(avg2 / len(data2['stats']), 1)))
        img2 = data2['sprites']['other']['showdown']['front_shiny'] if s1 else data2['sprites']['other']['showdown']['front_default']
        if img2 is None:
            img2 = data2['sprites']['front_shiny'] if s1 else data2['sprites']['front_default']
        embed2.set_image(url=img2)
        
        if avg1 > avg2:
            winner = await shared.bot.fetch_user(cid)
            if winner is None:
                await ctx.send("No se ha encontrado al retador")
                return
        elif avg1 == avg2:
            winner = await shared.bot.fetch_user(random.choice([cid, ctx.author.id]))
            if winner is None:
                await ctx.send("No se ha encontrado al retador")
                return
        else:
            winner = ctx.author
        await ctx.send("**¡La pelea ha comenzado!**", embeds=[embed1, embed2])
        await asyncio.sleep(1)
        await ctx.send(f"¡{winner.name} ha ganado el combate! Puede capturar tres pokémon más hoy y recibe 6 tiradas")
        cursor.execute("UPDATE pusers set wins = COALESCE(wins, 0) + 1, count = 6, daily_catch_count = 3 WHERE user_id = %s", (winner.id,))
        conn.commit()
        l = n_l(winner.id)
        cursor.execute("UPDATE pusers set league = %s WHERE user_id = %s", (l, winner.id))
        conn.commit()

@commands.command(name='cp', help="Este comando elige el pokémon con el que se va a pelear")
async def cp(ctx, pk2: int):
    if ctx.author.id not in shared.fight_data:
        await ctx.send("No tienes ninguna pelea pendiente")
        return
    
    fight_data = shared.fight_data[ctx.author.id]
    challenger_id = fight_data['cid']
    pkid1 = fight_data['cpkid']

    try:
        conn = psycopg2.connect(
            database=db_name,
            user=db_user,
            password=db_pass,
            host=db_host,
            port=db_port
        )
        cursor = conn.cursor()
        cursor.execute("SELECT pk_id, shiny FROM pcatches WHERE user_id = %s AND pk_id = %s", (ctx.author.id, pk2,))
        result = cursor.fetchone()
        if result is None:
            await ctx.send("No tienes ese pokémon")
            return
        enemy = await shared.bot.fetch_user(challenger_id)
        if enemy is None:
            await ctx.send("No se ha encontrado al retador")
            return
        if not pk_in_league(pk2, ctx.author.id):
            await ctx.send("Tu pokémon seleccionado no puede pelear en tu liga")
            return
        await fight(cursor, ctx, challenger_id, pkid1, pk2, conn, result)

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
        await ctx.send("An error occurred while fighting.")
    finally:
        if conn:
            cursor.close()
            conn.close()
@cp.error
async def cp_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Debes ingresar el id del pokémon con el que quieres pelear")
    if isinstance(error, commands.BadArgument):
        await ctx.send("Debes ingresar el id del pokémon con el que quieres pelear")
    else:
        await ctx.send("Ha ocurrido un error al intentar pelear")
cp.category = "Combates"