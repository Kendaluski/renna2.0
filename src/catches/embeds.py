import requests, discord
from basics.utils import translate
from catches.catches import get_fav

def all_embeds(embeds, pk_id, shiny, ctx, img, embed):
	req = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pk_id}")
	if req.status_code == 200:
		data = req.json()
		avg_stats = sum(stat['base_stat'] for stat in data['stats'])
		if img:
			image_url = img
		else:
			image_url = data['sprites']['other']['showdown']['front_shiny'] if shiny else data['sprites']['other']['showdown']['front_default']
			if image_url is None:
				image_url = data['sprites']['front_shiny'] if shiny else data['sprites']['front_default']
		if shiny:
			name = f"{data['name']} **SHINY**"
		else:
			name = data['name']
		id = data['id']
		
		if len(embed.fields) < 25:
			embed.add_field(name=name, value=f"ID: {id} \nTipo: {', '.join([translate(t['type']['name']) for t in data['types']])}\n Stats: {avg_stats}", inline=True)
			embed.set_thumbnail(url=image_url)
		else:
			embeds.append(embed)
			embed = discord.Embed(title=f"Pokémon atrapados por {ctx.author.name} que están en su liga", color=0x00FF00)
			embed.add_field(name=name, value=f"Tipo: {', '.join([translate(t['type']['name']) for t in data['types']])}\n Stats: {avg_stats}", inline=True)
			embed.set_thumbnail(url=image_url)
	return embeds

def one_embed(shiny, pk_id, ctx):
	embed = None
	req = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pk_id}")
	if req.status_code == 200:
		data = req.json()
		image_url = data['sprites']['other']['showdown']['front_shiny'] if shiny else data['sprites']['other']['showdown']['front_default']
		if image_url is None:
			image_url = data['sprites']['front_shiny'] if shiny else data['sprites']['front_default']
		avg_stats = sum(data['stats'][i]['base_stat'] for i in range(6))
		name = data['name']
		id = data['id']
		types = [translate(t['type']['name']) for t in data['types']]
		if shiny:
			embed = discord.Embed(title=f"Info del [{id}]{name} **SHINY** de {ctx.author.name}", color=0x00FF00)
		else:
			embed = discord.Embed(title=f"Info del [{id}]{name} de {ctx.author.name}", color=0x00FF00)
		embed.add_field(name="Tipo", value=", ".join(types), inline=False)
		embed.add_field(name="Stats", value=avg_stats, inline=False)
		embed.set_thumbnail(url=image_url)
	return embed

def set_img(ctx, cursor, result):
	f = get_fav(ctx.author.id)
	image_url = None
	if f:
		cursor.execute("SELECT shiny FROM pcatches WHERE user_id = %s AND pk_id = %s", (ctx.author.id, f,))
		shiny = cursor.fetchone()[0]
		req = requests.get(f"https://pokeapi.co/api/v2/pokemon/{f}")
		if req.status_code == 200:
			data = req.json()
			image_url = data['sprites']['other']['showdown']['front_shiny'] if shiny else data['sprites']['other']['showdown']['front_default']
			if image_url is None:
				image_url = data['sprites']['front_shiny'] if shiny else data['sprites']['front_default']
		
		if not image_url and result:
			pk_id, shiny, stats = result[-1]
			req = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pk_id}")
			if req.status_code == 200:
				data = req.json()
				image_url = data['sprites']['other']['showdown']['front_shiny'] if shiny else data['sprites']['other']['showdown']['front_default']
				if image_url is None:
					image_url = data['sprites']['front_shiny'] if shiny else data['sprites']['front_default']
	return image_url