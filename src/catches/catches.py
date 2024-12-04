import psycopg2, requests, discord, os, random
from discord.ext import commands
from dotenv import load_dotenv
from basics.utils import translate
from datetime import datetime
from leagues.league import get_league

load_dotenv()
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASS')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')

def get_fav(id):
    try:
        conn = psycopg2.connect(
            database=db_name,
            user=db_user,
            password=db_pass,
            host=db_host,
            port=db_port
        )
        cursor = conn.cursor()
        cursor.execute("SELECT fav FROM pusers WHERE user_id = %s", (id,))
        result = cursor.fetchone()
        if result is None:
            return None
        else:
            return result[0]
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
        return None
    finally:
        if conn:
            cursor.close()
            conn.close()

@commands.command(name="fav", help="Este comando marca un pokémon como favorito")
async def fav(ctx, id):
    try:
        conn = psycopg2.connect(
            database=db_name,
            user=db_user,
            password=db_pass,
            host=db_host,
            port=db_port
        )

        cursor = conn.cursor()
        cursor.execute("SELECT pk_id FROM pcatches WHERE user_id = %s AND pk_id = %s", (ctx.author.id, id,))
        result = cursor.fetchone()
        if result is None:
            await ctx.send("No tienes ese pokémon")
        else:
            cursor.execute("UPDATE pusers SET fav = %s WHERE user_id = %s", (id, ctx.author.id,))
            conn.commit()
            await ctx.send("Pokémon marcado como favorito")

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
        await ctx.send("Ha ocurrido un error, inténtalo de nuevo más tarde")
    finally:
        if conn:
            cursor.close()
            conn.close()
@fav.error
async def fav_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Debes ingresar el id del pokémon que quieres marcar como favorito")
    if isinstance(error, commands.BadArgument):
        await ctx.send("Debes ingresar el id del pokémon que quieres marcar como favorito")
    else:
        await ctx.send("Ha ocurrido un error al intentar marcar el pokémon como favorito")
fav.category = "Atrapar Pokémon"

class CatchButton(discord.ui.Button):
    def __init__(self, pkid, shiny, uid, stats):
        super().__init__(style=discord.ButtonStyle.primary, label="¡Lo quiero (5 al día)!")
        self.pkid = pkid
        self.shiny = shiny
        self.uid = uid
        self.stats = stats
    
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
                daily_catch_count = 5
            if daily_catch_count > 0:
                daily_catch_count -= 1
                cursor.execute("UPDATE pusers SET daily_catch_count = %s, last_catched = %s WHERE user_id = %s", (daily_catch_count, last_catched, user_id,))
                conn.commit()
                cursor.execute("INSERT INTO pcatches (user_id, pk_id, shiny, stats) VALUES (%s, %s, %s, %s)", (user_id, self.pkid, self.shiny, self.stats))
                conn.commit()
                await interaction.response.send_message("¡Has atrapado un pokémon!", ephemeral=True)
                self.disabled = True
                await interaction.message.edit(view=self.view)
                if daily_catch_count == 0:
                    cursor.execute("UPDATE pusers SET daily_streak = COALESCE(daily_streak,0) + 1 WHERE user_id = %s", (user_id,))
                    conn.commit()
            else:
                await interaction.response.send_message("Ya has atrapado cinco pokémon hoy", ephemeral=True)
        except (Exception, psycopg2.Error) as error:
            print("Error while connecting to PostgreSQL", error)
            await interaction.followup.send_message("An error occurred while catching the Pokémon.", ephemeral=True)
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
            cursor.execute("INSERT INTO pusers (user_id, wins, daily_streak, count, last_used, last_league) VALUES (%s, 0, 0, 10, %s, %s)", (ctx.author.id,today,today,))
            daily_streak = 0
            count = 10
        else:
            cursor.execute("SELECT count, last_used, daily_streak FROM pusers WHERE user_id = %s", (ctx.author.id,))
            result = cursor.fetchone()
            count, last_used, daily_streak = result
            if last_used is None:
                last_used = today
            last_used_date = last_used
            if last_used_date < today:
                count = 10
            if count == 0:
                await ctx.send("Has alcanzado el límite de pokémon salvajes diarios, vuelve mañana")
                return
            cursor.execute("UPDATE pusers SET count = %s, last_used = %s WHERE user_id = %s", (count - 1, today, ctx.author.id,))
        conn.commit()
        res = requests.get('https://pokeapi.co/api/v2/pokemon?limit=1118')
        if res.status_code == 200:
            data = res.json()
            pokemon = random.choice(data['results'])
            response = requests.get(pokemon['url'])
            if response.status_code == 200:
                data = response.json()
                types = [translate(t['type']['name']) for t in data['types']]
                stats = sum([stat['base_stat'] for stat in data['stats']])

                bchance = 1 / 512
                ap = bchance * (daily_streak * 2)
                if random.random() < ap:
                    image_url = data['sprites']['other']['showdown']['front_shiny']
                    if image_url is None:
                        image_url = data['sprites']['front_shiny']
                    shiny = True
                    embed = discord.Embed(title="¡Un pokémon salvaje apareció!", description=f"Es un {translate(data['name'])} **SHINY** de tipo {', '.join(types)}", color=0xFFA500)
                    cursor.execute("UPDATE pusers SET daily_streak = 0 WHERE user_id = %s", (ctx.author.id,))
                    conn.commit()
                else:
                    image_url = data['sprites']['other']['showdown']['front_default']
                    if image_url is None:
                        image_url = data['sprites']['front_default']
                    shiny = False
                    embed = discord.Embed(title="¡Un pokémon salvaje apareció!", description=f"Es un {translate(data['name'])} de tipo {', '.join(types)}", color=0xFFA500)

                embed.set_image(url=image_url)

                view = discord.ui.View()
                view.add_item(CatchButton(data['id'], shiny, ctx.author.id, stats))
                await ctx.send(embed=embed, view=view)
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
        await ctx.send("Ha ocurrido un error, inténtalo de nuevo más tarde")
    
    finally:
        if conn:
            cursor.close()
            conn.close()
pkc.category = "Atrapar Pokémon"

@commands.command(name="rolls", help="Este comando muestra tus tiradas de pokémon diarias restantes, así como la cantidad de pokémon que puedes capturar hoy y tu racha de capturas diarias")
async def rolls(ctx):
    try:
        conn = psycopg2.connect(
            database=db_name,
            user=db_user,
            password=db_pass,
            host=db_host,
            port=db_port
        )
        cursor = conn.cursor()
        cursor.execute("SELECT count, daily_catch_count, daily_streak FROM pusers WHERE user_id = %s", (ctx.author.id,))
        result = cursor.fetchone()
        if result is None:
            await ctx.send("No tienes tiradas de pokémon disponibles")
        else:
            count, daily_catch_count, daily_streak = result
            await ctx.send(f"Tienes {count} tiradas de pokémon diarias restantes, puedes atrapar {daily_catch_count} pokémon hoy y tu racha de capturas diarias es de {daily_streak}")
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
        await ctx.send("Ha ocurrido un error, inténtalo de nuevo más tarde")
    finally:
        if conn:
            cursor.close()
            conn.close()
rolls.category = "Atrapar Pokémon"