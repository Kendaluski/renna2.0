import psycopg2
from discord.ext import commands
import requests
import discord
import os
import random
from dotenv import load_dotenv
from utils import translate
import shared

load_dotenv()
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASS')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')

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
			await interaction.response.send_message("Has aceptado la pelea, elige tu pokémon con +cp <id>", ephemeral=True)
			shared.fight_data[self.did] = {
				"cid": self.cid,
				"cpkid": self.pkid
			}

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

		await interaction.response.send_message("Has rechazado la pelea", ephemeral=True)
		if self.did in shared.fight_data:
			shared.fight_data.pop(self.did)
		


@commands.command(name='fight', help="Este comando simula un combate pokémon contra otro jugador")
async def fight(ctx, pk1: int, enemy: discord.User):
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

		view = discord.ui.View()
		view.add_item(AcceptButton(pk1, ctx.author.id, enemy.id))
		view.add_item(DeclineButton(ctx.author.id, enemy.id, pk1))

		await ctx.send(f"{enemy.mention}, {ctx.author.mention} te ha desafiado a un combate pokémon", view=view)
	except (Exception, psycopg2.Error) as error:
		print("Error while connecting to PostgreSQL", error)
		await ctx.send("An error occurred while fighting.")
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
		await ctx.send(f"¡El combate entre {ctx.author.mention} y {enemy.mention} ha comenzado!")
		cpk = shared.fight_data[ctx.author.id]['cpkid']
		dpk = pk2
		res = requests.get(f'https://pokeapi.co/api/v2/pokemon/{cpk}')
		res2 = requests.get(f'https://pokeapi.co/api/v2/pokemon/{dpk}')
		if res.status_code == 200 and res2.status_code == 200:
			data1 = res.json()
			data2 = res2.json()
			avg1 = sum([stat['base_stat'] for stat in data1['stats']])
			avg2 = sum([stat['base_stat'] for stat in data2['stats']])
			if avg1 > avg2:
				winner = await shared.bot.fetch_user(challenger_id)
				if winner is None:
					await ctx.send("No se ha encontrado al retador")
					return
			else:
				winner = ctx.author
			await ctx.send(f"¡{winner.mention} ha ganado el combate! Puede capturar un pokémon más hoy y se resetean sus tiradas")
			cursor.execute("UPDATE pusers set wins = COALESCE(wins, 0) + 1, count = 0, daily_catch_count = 0 WHERE user_id = %s", (winner.id,))
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