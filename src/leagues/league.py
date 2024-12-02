import discord, os, psycopg2
from discord.ext import commands
from dotenv import load_dotenv
from leagues.l_utils import get_league, init_league, n_l
from fights.fights import b_p_track

load_dotenv()
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASS')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')

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