import psycopg2, discord, os, requests
from discord.ext import commands
from dotenv import load_dotenv
from leagues.league import get_league
from catches.embeds import gen_embed
from catches.pages import PagesView
from basics.utils import get_pk_info

load_dotenv()
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASS')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')

def l_check(stats, l):
    if l == 100 and stats <= 100:
        return True
    elif l == 300 and stats > 100 and stats <= 300:
        return True
    elif l == 500 and stats > 300 and stats <= 500:
        return True
    elif l == 600 and stats > 500 and stats <= 600:
        return True
    elif l == 800 and stats > 600 and stats <= 800:
        return True
    else:
        return False

@commands.command(name="pkl", help="Este comando muestra los pokémon que ha atrapado un usuario")
async def pkl(ctx, *args):
    try:
        conn = psycopg2.connect(
            database=db_name,
            user=db_user,
            password=db_pass,
            host=db_host,
            port=db_port
        )
        cursor = conn.cursor()
        if args and args[0] != "l":
            pkid = (int)(args[0])
            cursor.execute("SELECT pk_id, stats, shiny, count(pk_id) FROM pcatches WHERE user_id = %s AND pk_id = %s ORDER BY stats DESC", (ctx.author.id, pkid,))
            result = cursor.fetchall()
            if len(result) == 0:
                await ctx.send("No tienes ese pokémon atrapado <:Sadge:1259834661622910988>")
                return
            req = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pkid}")
            if req.status_code == 200:
                data = req.json()
                name = data['name'].capitalize()
                shiny = False
                count = result[0][3]
                for res in result:
                    if res[2] is True:
                        shiny = True
            await get_pk_info(ctx, name, True, shiny, count)
        else:
            cursor.execute("SELECT pk_id, stats, shiny FROM pcatches WHERE user_id = %s ORDER BY stats DESC", (ctx.author.id,))
            result = cursor.fetchall()
            if not result:
                await ctx.send("No tienes ningún pokémon atrapado <:Sadge:1259834661622910988>")
                return

            if args and args[0] == "l":
                embeds = gen_embed(result, ctx, cursor, True)
            elif len(args) == 0:
                embeds = gen_embed(result, ctx, cursor)
            if len(embeds) == 1:
                await ctx.send(embed=embeds[0])
                return
            embeds[0].set_footer(text=f"Página 1/{len(embeds)}")
            view = PagesView(embeds)
            await ctx.send(embed=embeds[0], view=view)
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
        await ctx.send("Ha ocurrido un error, inténtalo de nuevo más tarde")
    finally:
        if conn:
            cursor.close()
            conn.close()
pkl.category = "Atrapar Pokémon"