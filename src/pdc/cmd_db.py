import psycopg2
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASS')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')

@commands.command(name='addUser', help="Este comando añade un usuario a la base de datos")
@commands.has_permissions(administrator=True)
async def addUser(ctx, name: str):
    try:
        conn = psycopg2.connect(
            database=db_name,
            user=db_user,
            password=db_pass,
            host=db_host,
            port=db_port
        )
        cursor = conn.cursor()
        cursor.execute("INSERT INTO pdc (name) VALUES (%s)", (name,))
        conn.commit()
        await ctx.send(f"Usuario {name} añadido correctamente")

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)

    finally:
        if conn:
            cursor.close()
            conn.close()

@addUser.error
async def addUser_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("No tienes permisos para ejecutar este comando")
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Falta el nombre del usuario")
addUser.category = "Pokémon Discord Cup"

@commands.command(name="muertes", help="Este comando muestra el número de muertes de todos los jogadores o de uno en concreto")
async def muertes(ctx, *args):
    try:
        conn = psycopg2.connect(
            database=db_name,
            user=db_user,
            password=db_pass,
            host=db_host,
            port=db_port
        )
        cursor = conn.cursor()
        if len(args) == 0:
            cursor.execute("SELECT name, COALESCE(deaths, 0) FROM pdc")
        else:
            cursor.execute("SELECT name, COALESCE(deaths, 0) FROM pdc WHERE name = %s", (args[0],))
        
        records = cursor.fetchall()
        if not records:
            await ctx.send("No se han encontrado resultados")
            return
        
        res = []
        max = 0
        max_name = []
        for record in records:
            name, deaths = record
            if deaths > max:
                max = deaths
                max_name.append(name)
            if deaths == max:
                max_name.append(name)
            res.append((name, deaths))
        
        res = "\n".join([f"A {r[0]} se le han muerto {r[1]} pokémon" for r in res])
        if len(max_name) > 1:
            res += f"\nLos que más muertes tienen son: {', '.join(max_name)} con {max} muertes"
        await ctx.send(res)

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)

    finally:
        if conn:
            cursor.close()
            conn.close()
muertes.category = "Pokémon Discord Cup"

@commands.command(name="addDeath", help="Este comando suma una muerte a un jugador")
@commands.has_permissions(administrator=True)
async def addDeath(ctx, name: str):
    try:
        conn = psycopg2.connect(
            database=db_name,
            user=db_user,
            password=db_pass,
            host=db_host,
            port=db_port
        )
        cursor = conn.cursor()
        cursor.execute("UPDATE pdc SET deaths = COALESCE(deaths, 0) + 1 WHERE name = %s", (name,))
        conn.commit()
        await ctx.send(f"Muerte añadida a {name}")

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)

    finally:
        if conn:
            cursor.close()
            conn.close()
@addDeath.error
async def addDeath_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("No tienes permisos para ejecutar este comando")
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Falta el nombre del usuario")
addDeath.category = "Pokémon Discord Cup"