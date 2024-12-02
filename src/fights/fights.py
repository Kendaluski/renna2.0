from discord.ext import commands
import discord, os, shared, psycopg2
from dotenv import load_dotenv
from datetime import datetime, timedelta
from leagues.daily_reset import daily_reset
from leagues.l_utils import same_league, both_have_pk, pk_in_league

load_dotenv()
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASS')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
ALT_ID = int(os.getenv('ALT_ID'))

b_p_track = {}
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


@commands.command(name='rcd', help="Resets the cooldown for a user")
@commands.has_permissions(administrator=True)
async def rcd(ctx, user: discord.User):
    if user.id in cd_track:
        cd_track.pop(user.id)
        await ctx.send(f"Cooldown for {user.mention} has been reset.")
    else:
        await ctx.send(f"{user.mention} does not have an active cooldown.")
