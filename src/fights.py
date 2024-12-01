from discord.ext import commands
import requests, discord, os, random, shared, asyncio, psycopg2
from dotenv import load_dotenv
from utils import translate, get_color
from datetime import datetime, timedelta
from league import same_league, get_league, both_have_pk, pk_in_league, n_l, init_league
from daily_reset import daily_reset

load_dotenv()
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASS')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
ALT_ID = int(os.getenv('ALT_ID'))

cd_track = {}

class AcceptButton(discord.ui.Button):
    def __init__(self, pkid, cid, did):
        super().__init__(style=discord.ButtonStyle.success, label="Aceptar")
        self.pkid = pkid
        self.cid = cid
        self.did = did
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.did and interaction.user.id != self.cid:
            await interaction.response.send_message("Tú no formas parte de esa pelea", ephemeral=True)
            return
        if interaction.user.id == self.cid:
            await interaction.response.send_message("No puedes pelear contra ti mismo", ephemeral=True)
            return
        else:
            await interaction.response.send_message(f"{interaction.user.name} aceptado la pelea, elige tu pokémon con +cp <id>")
            shared.fight_data[self.did] = {
                "cid": self.cid,
                "cpkid": self.pkid
            }
            self.disabled = True
            self.view.children[1].disabled = True
            await interaction.message.edit(view=self.view)

class DeclineButton(discord.ui.Button):
    def __init__(self, cid, did, pkid):
        super().__init__(style=discord.ButtonStyle.danger, label="Rechazar (te cagas)")
        self.cid = cid
        self.did = did
        self.pkid = pkid
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.did:
            await interaction.response.send_message("Tú no formas parte de esa pelea", ephemeral=True)
            return

        self.disabled = True
        self.view.children[0].disabled = True
        await interaction.message.edit(view=self.view)
        await interaction.message.delete()
        await interaction.channel.send(f"{interaction.user.name} ha rechazado la pelea (se caga <:SAJ:1259836031704895538>)")
        if self.did in shared.fight_data:
            shared.fight_data.pop(self.did)
        if self.cid in cd_track:
            cd_track.pop(self.cid)
        


@commands.command(name='fight', help="Este comando simula un combate pokémon contra otro jugador")
async def fight(ctx, pk1: int, enemy: discord.User):
    uid = ctx.author.id
    now = datetime.utcnow()
    cd_p = timedelta(hours=1)
    if uid in cd_track:
        cd_end = cd_track[uid]
        if now < cd_end:
            r = cd_end - now
            h, rem = divmod(r.seconds, 3600)
            m, s = divmod(rem, 60)
            await ctx.send(f"Debes esperar {m} minutos y {s} segundos para poder pelear de nuevo")
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
        cursor.execute("SELECT pk_id, shiny FROM pcatches WHERE user_id = %s AND pk_id = %s", (ctx.author.id, pk1,))
        result = cursor.fetchone()
        if result is None:
            await ctx.send("No tienes ese pokémon")
            return
        await daily_reset()
        if same_league(ctx.author.id, enemy.id):
            await ctx.send("No puedes pelear contra alguien de otra liga")
            return
        if not both_have_pk(ctx.author.id, enemy.id):
            await ctx.send("Ambos debéis tener al menos un pokémon que pueda pelear en vuestra liga")
            return
        if not pk_in_league(pk1, ctx.author.id):
            await ctx.send("Tu pokémon seleccionado no puede pelear en tu liga")
            return
        view = discord.ui.View()
        view.add_item(AcceptButton(pk1, ctx.author.id, enemy.id))
        view.add_item(DeclineButton(ctx.author.id, enemy.id, pk1))

        await ctx.send(f"{enemy.name}, {ctx.author.name} te ha desafiado a un combate pokémon", view=view)
        cd_track[uid] = now + cd_p
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
        await ctx.send("Ha ocurrido un error al procesar la pelea")
    finally:
        if conn:
            cursor.close()
            conn.close()
@fight.error
async def fight_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Debes ingresar el id de tu pokémon y mencionar a tu oponente!")
    if isinstance(error, commands.BadArgument):
        await ctx.send("Debes ingresar el id de tu pokémon (puedes verlo en pkinfo o pkl) y mencionar a quién quieras retar!")
    else:
        await ctx.send("Ha ocurrido un error al intentar pelear")

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
        s1 = result[1]
        cursor.execute("SELECT pk_id, shiny FROM pcatches WHERE user_id = %s AND pk_id = %s", (challenger_id, pkid1,))
        result = cursor.fetchone()
        s2 = result[1]
        cpk = shared.fight_data[ctx.author.id]['cpkid']
        dpk = pk2
        res = requests.get(f'https://pokeapi.co/api/v2/pokemon/{cpk}')
        res2 = requests.get(f'https://pokeapi.co/api/v2/pokemon/{dpk}')
        if res.status_code == 200 and res2.status_code == 200:
            data1 = res.json()
            data2 = res2.json()
            avg1 = sum([stat['base_stat'] for stat in data1['stats']])
            avg2 = sum([stat['base_stat'] for stat in data2['stats']])
            c1 = avg1 / len(data1['stats'])
            c1 = round(c1, 1)
            c2 = avg2 / len(data2['stats'])
            c2 = round(c2, 1)
            co1 = get_color(c1)
            co2 = get_color(c2)
            embed1 = discord.Embed(title=f"{data1['name']} Retador", description=f"Stats: {avg1}", color=co1)
            img1 = data1['sprites']['front_shiny'] if s2 else data1['sprites']['front_default']
            embed1.set_image(url=img1)
            embed2 = discord.Embed(title=f"{data2['name']} Defensor", description=f"Stats: {avg2}", color=co2)
            img2 = data2['sprites']['front_shiny'] if s1 else data2['sprites']['front_default']
            embed2.set_image(url=img2)
            
            if avg1 > avg2:
                winner = await shared.bot.fetch_user(challenger_id)
                if winner is None:
                    await ctx.send("No se ha encontrado al retador")
                    return
            else:
                winner = ctx.author
            await ctx.send("**¡La pelea ha comenzado!**", embeds=[embed1, embed2])
            await asyncio.sleep(1)
            await ctx.send(f"¡{winner.name} ha ganado el combate! Puede capturar un pokémon más hoy y se resetean sus tiradas")
            cursor.execute("UPDATE pusers set wins = COALESCE(wins, 0) + 1, count = 0, daily_catch_count = 1 WHERE user_id = %s", (winner.id,))
            conn.commit()
            l = n_l(winner.id)
            cursor.execute("UPDATE pusers set league = %s WHERE user_id = %s", (l, challenger_id))
            conn.commit()
            l = n_l(ctx.author.id)
            cursor.execute("UPDATE pusers set league = %s WHERE user_id = %s", (l, ctx.author.id))
            conn.commit()

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

@commands.command(name='wins', help="Este comando muestra todas las victorias de todos los usuarios (si se añade all al comando) o de uno mismo si no se pone nada")
async def wins(ctx, user: str = None):
    try:
        conn = psycopg2.connect(
            database=db_name,
            user=db_user,
            password=db_pass,
            host=db_host,
            port=db_port
        )
        cursor = conn.cursor()
        if user is None:
            cursor.execute("SELECT user_id, wins FROM pusers WHERE user_id = %s", (ctx.author.id,))
            result = cursor.fetchone()
            if result is None:
                await ctx.send("No has ganado ni una vez")
            else:
                await ctx.send(f"Has ganado {result[1]} veces")
        elif user == "all":
            cursor.execute("SELECT user_id, wins FROM pusers ORDER BY wins DESC")
            result = cursor.fetchall()
            embed = discord.Embed(title="Victorias de todos los usuarios", description="", color=0xFFA500)
            for row in result:
                user = await shared.bot.fetch_user(row[0])
                if user is None or user.id == ALT_ID:
                    continue
                embed.add_field(name=user.name, value=row[1], inline=True)
            await ctx.send(embed=embed)
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
        await ctx.send("An error occurred while fetching wins.")
    finally:
        if conn:
            cursor.close()
            conn.close()

@commands.command(name="getl", help="Este comando te muestra el máximo de stat que tu pokémon puede tener a la hora de pelear")
async def getl(ctx):
    try:
        conn = psycopg2.connect(
            database=db_name,
            user=db_user,
            password=db_pass,
            host=db_host,
            port=db_port
        )
        cursor = conn.cursor()
        cursor.execute("SELECT league FROM pusers WHERE user_id = %s", (ctx.author.id,))
        league = cursor.fetchone()[0]
        if league == 0 or league == None:
            league = init_league(ctx.author.id)
            cursor.execute("UPDATE pusers set league = %s WHERE user_id = %s", (league, ctx.author.id))
            conn.commit()
        if league == 100:
            await ctx.send(f"Tu rango de de stats es de 0 a 100")
        elif league == 300:
            await ctx.send(f"Tu rango de de stats es de 101 a 300")
        elif league == 500:
            await ctx.send(f"Tu rango de de stats es de 301 a 500")
        elif league == 600:
            await ctx.send(f"Tu rango de de stats es de 501 a 600")
        elif league == 800:
            await ctx.send("Tu rango de de stats es de 601 a 800")
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
        await ctx.send("Se ha producido un error al intentar obtener la liga")
    finally:
        if conn:
            cursor.close()
            conn.close()

b_p_track = {}

@commands.command(name='rcd', help="Resets the cooldown for a user")
@commands.has_permissions(administrator=True)
async def rcd(ctx, user: discord.User):
    if user.id in cd_track:
        cd_track.pop(user.id)
        await ctx.send(f"Cooldown for {user.mention} has been reset.")
    else:
        await ctx.send(f"{user.mention} does not have an active cooldown.")

class ConfirmButton(discord.ui.Button):
    def __init__(self, user_id):
        super().__init__(style=discord.ButtonStyle.success, label="Confirmar")
        self.user_id = user_id
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("No puedes confirmar esta acción.", ephemeral=True)
            return
        if interaction.user.id in b_p_track:
            await interaction.response.send_message("Ya has confirmado esta acción.", ephemeral=True)
            return
        b_p_track[interaction.user.id] = True
        try:
            conn = psycopg2.connect(
                database=db_name,
                user=db_user,
                password=db_pass,
                host=db_host,
                port=db_port
            )
            cursor = conn.cursor()
            l = get_league(self.user_id)
            if l == 100:
                await interaction.response.send_message("No puedes bajar más de liga", ephemeral=True)
                return
            l = n_l(self.user_id)
            cursor.execute("UPDATE pusers set league = %s WHERE user_id = %s", (l, self.user_id))
            conn.commit()
            await interaction.response.send_message("Tu liga ha bajado de nivel", ephemeral=True)
            await interaction.message.delete()
            if interaction.user.id in b_p_track:
                b_p_track.pop(interaction.user.id)
        except (Exception, psycopg2.Error) as error:
            print("Error while connecting to PostgreSQL", error)
            await interaction.response.send_message("Se ha producido un error al intentar bajar de liga", ephemeral=True)
        finally:
            if conn:
                cursor.close()
                conn.close()

class CancelButton(discord.ui.Button):
    def __init__(self, user_id):
        super().__init__(style=discord.ButtonStyle.danger, label="Cancelar")
        self.user_id = user_id
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("No puedes cancelar esta acción.", ephemeral=True)
            return
        if interaction.user.id in b_p_track:
            await interaction.response.send_message("Ya has cancelado esta acción.", ephemeral=True)
            return
        b_p_track[interaction.user.id] = True
        await interaction.response.send_message("Has cancelado la acción.", ephemeral=True)
        await interaction.message.delete()
        if interaction.user.id in b_p_track:
            b_p_track.pop(interaction.user.id)

@commands.command(name='dl', help="Este comando te baja un nivel la liga en la que estás")
async def dl(ctx):
    l = get_league(ctx.author.id)
    if l == 100:
        await ctx.send("Estás en la liga más baja, no puedes bajar más")
    view = discord.ui.View()
    view.add_item(ConfirmButton(ctx.author.id))
    view.add_item(CancelButton(ctx.author.id))
    await ctx.send("¿Estás seguro de que quieres bajar de liga? Esta acción solo se resetea a las 00", view=view)