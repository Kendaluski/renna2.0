import psycopg2
from discord.ext import commands
import requests
import discord
import os
import random
from dotenv import load_dotenv
from utils import translate
from datetime import datetime, timedelta

load_dotenv()
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASS')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')

class CatchButton(discord.ui.Button):
    def __init__(self, pkid, shiny, uid):
        super().__init__(style=discord.ButtonStyle.primary, label="¡Lo quiero (1 al día)!")
        self.pkid = pkid
        self.shiny = shiny
        self.uid = uid
    
    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        if user_id != self.uid:
            await interaction.response.send_message("No puedes atrapar un pokémon que no es tuyo", ephemeral=True)
            return
        try:
            conn = psycopg2.connect(
                database=db_name,
                user=db_user,
                password=db_pass,
                host=db_host,
                port=db_port
            )
            cursor = conn.cursor()
            cursor.execute("SELECT last_catched, daily_catch_count FROM pusers WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            last_catched, daily_catch_count = result
            if last_catched is None or last_catched < datetime.now().date():
                last_catched = datetime.now().date()
                daily_catch_count = 1
            if daily_catch_count is None or daily_catch_count < 3:
                daily_catch_count = daily_catch_count + 1
                cursor.execute("UPDATE pusers SET daily_catch_count = %s, last_catched = %s, daily_streak = daily_streak + 1 WHERE user_id = %s", (daily_catch_count, last_catched, user_id,))
                conn.commit()
                cursor.execute("INSERT INTO pcatches (user_id, pk_id, shiny) VALUES (%s, %s, %s)", (user_id, self.pkid, self.shiny,))
                conn.commit()
                await interaction.response.send_message("¡Has atrapado un pokémon!", ephemeral=True)
            else:
                await interaction.response.send_message("Ya has atrapado dos pokémon hoy", ephemeral=True)
        except (Exception, psycopg2.Error) as error:
            print("Error while connecting to PostgreSQL", error)
            await interaction.response.send_message("An error occurred while catching the Pokémon.", ephemeral=True)
        finally:
            if conn:
                cursor.close()
                conn.close()



@commands.command(name="pkc", help="Este comando hace que aparezca un pokémon salvaje aleatorio, siempre que el usuario haya ejecutado este comando menos de 5 veces al día")
async def pkc(ctx):
    today = datetime.now().date()
    try:
        conn = psycopg2.connect(
            database=db_name,
            user=db_user,
            password=db_pass,
            host=db_host,
            port=db_port
        )
        cursor = conn.cursor()
        cursor.execute("SELECT count, last_used, daily_streak FROM pusers WHERE user_id = %s", (ctx.author.id,))
        result = cursor.fetchone()
        if result is None:
            cursor.execute("INSERT INTO pusers (user_id, wins, daily_streak, count, last_used) VALUES (%s, 0, 0, 1, %s)", (ctx.author.id,today,))
            daily_streak = 0
            count = 1
        else:
            cursor.execute("SELECT count, last_used, daily_streak FROM pusers WHERE user_id = %s", (ctx.author.id,))
            result = cursor.fetchone()
            count, last_used, daily_streak = result
            if last_used is None:
                last_used = today
            last_used_date = last_used
            if last_used_date < today:
                count = 0
            if count >= 5:
                await ctx.send("Has alcanzado el límite de pokémon salvajes diarios, vuelve mañana")
                return
            cursor.execute("UPDATE pusers SET count = %s, last_used = %s WHERE user_id = %s", (count + 1, today, ctx.author.id,))
        conn.commit()
        res = requests.get('https://pokeapi.co/api/v2/pokemon?limit=1118')
        if res.status_code == 200:
            data = res.json()
            pokemon = random.choice(data['results'])
            response = requests.get(pokemon['url'])
            if response.status_code == 200:
                data = response.json()
                types = [translate(t['type']['name']) for t in data['types']]

                bchance = 1 / 128
                ap = bchance * (1 + daily_streak * 2)
                if random.random() < ap:
                    image_url = data['sprites']['front_shiny']
                    shiny = True
                    embed = discord.Embed(title="¡Un pokémon salvaje apareció!", description=f"Es un {translate(data['name'])} **SHINY** de tipo {', '.join(types)}", color=0xFFA500)
                else:
                    image_url = data['sprites']['front_default']
                    shiny = False
                    embed = discord.Embed(title="¡Un pokémon salvaje apareció!", description=f"Es un {translate(data['name'])} de tipo {', '.join(types)}", color=0xFFA500)

                embed.set_image(url=image_url)

                view = discord.ui.View()
                view.add_item(CatchButton(data['id'], shiny, ctx.author.id))
                await ctx.send(embed=embed, view=view)
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
        await ctx.send("Ha ocurrido un error, inténtalo de nuevo más tarde")
    
    finally:
        if conn:
            cursor.close()
            conn.close()



@commands.command(name="pkl", help="Este comando muestra los pokémon que ha atrapado un usuario")
async def pkl(ctx):
    try:
        conn = psycopg2.connect(
            database=db_name,
            user=db_user,
            password=db_pass,
            host=db_host,
            port=db_port
        )
        cursor = conn.cursor()
        cursor.execute("SELECT pk_id, shiny FROM pcatches WHERE user_id = %s", (ctx.author.id,))
        records = cursor.fetchall()
        if not records:
            await ctx.send("Aún no has atrapado ningún pokémon")
            return
        
        embeds = []
        embed = discord.Embed(title=f"Pokémon atrapados por {ctx.author.name}", color=0xFFA500)

        for pk_id, shiny in records:
            req = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pk_id}")
            if req.status_code == 200:
                data = req.json()
                image_url = data['sprites']['front_shiny'] if shiny else data['sprites']['front_default']
                avg_stats = sum(data['stats'][i]['base_stat'] for i in range(6))
                name = data['name']
                id = data['id']
                
                if len(embed.fields) < 25:
                    embed.add_field(name=name, value=f"ID: {id} \nTipo: {', '.join([translate(t['type']['name']) for t in data['types']])}\n Stats: {avg_stats}", inline=True)
                    embed.set_thumbnail(url=image_url)
                else:
                    embeds.append(embed)
                    embed = discord.Embed(title=f"Pokémon atrapados por {ctx.author.name}", color=0xFFA500)
                    embed.add_field(name=name, value=f"Tipo: {', '.join([translate(t['type']['name']) for t in data['types']])}\n Stats: {avg_stats}", inline=True)
                    embed.set_thumbnail(url=image_url)
        
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
        