import psycopg2, discord, os, requests
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASS')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')

class ConfirmButton(discord.ui.Button):
    def __init__(self, user_id, id, all):
        super().__init__(style=discord.ButtonStyle.success, label="Confirmar")
        self.user_id = user_id
        self.id = id
        self.all = all
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("No puedes confirmar esta acción.", ephemeral=True)
            return
        try:
            conn = psycopg2.connect(
                dbname=db_name, 
                user=db_user, 
                password=db_pass, 
                host=db_host, 
                port=db_port
            )
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(pk_id), COUNT(CASE WHEN shiny = TRUE THEN 1 END) FROM pcatches WHERE user_id = {interaction.user.id} AND pk_id = {self.id}")
            result = cursor.fetchall()
            p_count, s_count = result[0]
            if s_count >= 2 and self.all == False:
                s_count -= 1
            if s_count == 1 and self.all == False:
                s_count = 0
            cursor.execute(f"SELECT stats FROM pcatches WHERE user_id = {interaction.user.id} AND pk_id = {self.id}")
            stats = cursor.fetchall()
            total_to_add = 0
            if not all:
                important_stats = stats[1:]
            else:
                important_stats = stats
            for stat in important_stats:
                if stat[0] < 500:
                    total_to_add += 0.5
                elif stat[0] >= 500 and stat[0] < 700:
                    total_to_add += 1
                elif stat[0] >= 700:
                    total_to_add += 3
            total_to_add += 2 * s_count
            total_to_add = int(total_to_add)
            cursor.execute(f"UPDATE pusers SET daily_catch_count = COALESCE(daily_catch_count, 0) + {total_to_add} WHERE user_id = {interaction.user.id}")
            conn.commit()
            delete = "WITH cte AS ( SELECT id FROM pcatches WHERE user_id = %s AND pk_id = %s LIMIT %s) DELETE FROM pcatches WHERE id IN (SELECT id FROM cte);"
            if not self.all:
                cursor.execute(delete, (interaction.user.id, self.id, p_count - 1))
            else:
                cursor.execute(delete, (interaction.user.id, self.id, p_count))
            conn.commit()
            if s_count > 0 and not self.all:
                cursor.execute(f"UPDATE pcatches SET shiny = True WHERE user_id = {interaction.user.id} AND pk_id = {self.id}")
                conn.commit()
            req = requests.get(f"https://pokeapi.co/api/v2/pokemon/{self.id}")
            if req.status_code == 200:
                data = req.json()
                name = data['name']
                name = name.capitalize()
            if not self.all:
                msg = f"Has vendido " + str(p_count - 1) + " " + name + " , a cambio has ganado " + str(total_to_add) + " capturas diarias "
            else:
                msg = f"Has vendido todos tus " + name + ", a cambio has ganado " + str(total_to_add) + " capturas diarias "
            await interaction.response.send_message(msg)
            await interaction.message.delete()
        except (Exception, psycopg2.Error) as error:
            print("Error while connecting to PostgreSQL", error)
            await interaction.channel.send("No se pudo conectar a la base de datos")
            return
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
        await interaction.response.send_message("Has cancelado la acción.", ephemeral=True)
        await interaction.message.delete()


@commands.command(name="sell", help="Este comando vende todos los pokémon, el ID especificado, del usuario menos 1, a no ser que se le añada el argumento <all> después del ID. A cambio, el usuario recibe más capturas diarias, dependiendo de la cantidad de pokémon vendidos, sus estadísticas así como si es shiny o no.\n Si vendes un pokémon que tiene menos de 500 de stats, recibirás 0.5 capturas diarias por cada uno, si tiene entre 500 y 700, recibirás 1 captura diaria por cada uno y si tiene más de 700, recibirás 3 capturas diarias por cada uno. Además, si es shiny recibirás 2 capturas más por cada shiny")
async def sell(ctx, id: int, *args):
    if id < 1:
        await ctx.send("El id del pokémon debe ser mayor a 0")
        return
    if args:
        if args[0] != "all":
            await ctx.send("El comando solo acepta el ID del pokémon que quieres vender y la palabra 'all' para vender todos los pokémon de ese ID")
            return
        all = True
    else:
        all = False
    try:
        conn = psycopg2.connect(
            dbname=db_name, 
            user=db_user, 
            password=db_pass, 
            host=db_host, 
            port=db_port
        )
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(pk_id), COUNT(shiny) FROM pcatches WHERE user_id = {ctx.author.id} AND pk_id = {id}")
        result = cursor.fetchall()
        if result[0][0] == 0:
            await ctx.send("No tienes ese pokémon")
            return
        if result[0][0] == 1 and not all:
            await ctx.send("No puedes vender tu último pokémon")
            return
    except (Exception, psycopg2.Error) as error:
            print("Error while connecting to PostgreSQL", error)
            await ctx.send("No se pudo conectar a la base de datos")
            return
    finally:
        if conn:
            cursor.close()
            conn.close()
    view = discord.ui.View()
    view.add_item(ConfirmButton(ctx.author.id, id, all))
    view.add_item(CancelButton(ctx.author.id))
    if not all:
        await ctx.send("¿Estás seguro de que quieres vender todas las copias de ese pokémon? Recuerda que te quedarás con 1 siempre que no lo especifiques", view=view)
    else:
        await ctx.send("¿Estás seguro de que quieres vender todos los pokémon de ese ID?", view=view)
    

@sell.error
async def sell_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Debes ingresar el id del pokémon que quieres vender!")
    if isinstance(error, commands.BadArgument):
        await ctx.send("Debes ingresar el id del pokémon que quieres vender!")
sell.category = "Ventas"
