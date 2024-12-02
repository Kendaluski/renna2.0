import psycopg2, requests, discord, os
from discord.ext import commands
from dotenv import load_dotenv
from basics.utils import translate
from leagues.league import get_league
from catches.embeds import all_embeds, one_embed, set_img

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
        if args is not None and len(args) == 1:
            if args[0] == "l":
                cursor = conn.cursor()
                cursor.execute("SELECT pk_id, shiny, stats FROM pcatches WHERE user_id = %s", (ctx.author.id,))
                result = cursor.fetchall()
                if not result:
                    await ctx.send("Aún no has atrapado ningún pokémon")
                    return
                embeds = []
                l = get_league(ctx.author.id)
                embed = discord.Embed(title=f"Pokémon atrapados por {ctx.author.name} que están en su liga", color=0x00FF00)
                for pk_id, shiny, stats in result:
                    if l_check(stats, l):
                        embeds = all_embeds(embeds, pk_id, shiny, ctx, None, embed)
                    else:
                        continue
                if len(embed.fields) > 0:
                    embeds.append(embed)
                    for embed in embeds:
                        await ctx.send(embed=embed)
                else:
                    await ctx.send("No tienes pokémon para tu liga, puedes bajarte de liga usando +dl")
            else:
                cursor = conn.cursor()
                cursor.execute("SELECT pk_id, shiny FROM pcatches WHERE user_id = %s AND pk_id = %s", (ctx.author.id, args[0],))
                result = cursor.fetchone()
                if result is None:
                    await ctx.send("No tienes ese pokémon")
                    return
                pk_id, shiny = result
                embed = one_embed(shiny, pk_id, ctx)
                await ctx.send(embed=embed)
        else:
            cursor = conn.cursor()
            cursor.execute("SELECT pk_id, shiny FROM pcatches WHERE user_id = %s", (ctx.author.id,))
            records = cursor.fetchall()
            if not records:
                await ctx.send("Aún no has atrapado ningún pokémon")
                return
            
            image_url = set_img(ctx, cursor, records)
            embeds = []
            embed = discord.Embed(title=f"Pokémon atrapados por {ctx.author.name}", color=0x00FF00)
            for pk_id, shiny in records:
                embeds = all_embeds(embeds, pk_id, shiny, ctx, image_url, embed)
            
            embeds.append(embed)
            for embed in embeds:
                await ctx.send(embed=embed)
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
        await ctx.send("Ha ocurrido un error, inténtalo de nuevo más tarde")
    finally:
        if conn:
            cursor.close()
            conn.close()