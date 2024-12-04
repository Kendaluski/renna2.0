import discord

class PagesView(discord.ui.View):
	def __init__(self, embeds):
		super().__init__()
		self.embeds = embeds
		self.current_page = 0

	def set_page(self):
		embed = self.embeds[self.current_page]
		embed.set_footer(text=f"Página {self.current_page + 1}/{len(self.embeds)}")
	
	@discord.ui.button(label="←", style=discord.ButtonStyle.primary)
	async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
		if self.current_page == 0:
			self.current_page = len(self.embeds) - 1
		else:
			self.current_page -= 1
		self.set_page()
		await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
	
	@discord.ui.button(label="→", style=discord.ButtonStyle.primary)
	async def forward(self, interaction: discord.Interaction, button: discord.ui.Button):
		if self.current_page == len(self.embeds) - 1:
			self.current_page = 0
		else:
			self.current_page += 1
		self.set_page()
		await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)