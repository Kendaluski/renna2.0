import requests, discord
from basics.utils import translate
from catches.catches import get_fav
from leagues.l_utils import pk_in_league
from basics.utils import translate

def gen_embed(result, ctx, cursor, l=False,):
	embeds = []
	f = get_fav(ctx.author.id)
	filter = []

	for pk_id, stats, shiny in result:
		if l:
			if pk_in_league(pk_id, ctx.author.id):
				filter.append((pk_id, stats, shiny))
		else:
			filter.append((pk_id, stats, shiny))
	
	for i in range(0, len(filter), 9):
		if l:
			embed = discord.Embed(title=f"Pokémon atrapados por {ctx.author.name} que están en su liga", color=discord.Color.red())
		else:
			embed = discord.Embed(title=f"Pokémon atrapados por {ctx.author.name}", color=discord.Color.red())
		for pk_id, stats, shiny in filter[i:i+9] :
			req = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pk_id}")
			if req.status_code == 200:
				data = req.json()
				name = data['name'].capitalize()
				image_url = set_img(ctx, cursor, filter)
				if shiny:
					name = f"{name} ✨"
				if f == pk_id:
					name = f"{name} ❤"
				embed.add_field(name=name, value=f"Stats: {stats}", inline=True)
				embed.set_thumbnail(url=image_url)
		embeds.append(embed)
	return embeds
			
		
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