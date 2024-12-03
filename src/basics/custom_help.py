from discord.ext import commands
import discord

class CustomHelpCmd(commands.HelpCommand):
	def __init__(self):
		super().__init__()

	async def send_bot_help(self, mapping):
		embed = discord.Embed(title="Comands de Renna", description="Aquí tienes una lista de todos mis comandos", color=discord.Colour.magenta())
		for cog, commands in mapping.items():
			cml = [command.name for command in commands]
			if cml:
				cog_name = getattr(cog, "qualified_name", "Sin categoría")
				embed.add_field(name=cog_name, value="\n".join(cml), inline=False)
		channel = self.get_destination()
		await channel.send(embed=embed)
	async def send_cog_help(self, cog):
		embed = discord.Embed(title=f"{cog.qualified_name} Commands", description=cog.description, color=0x00FF00)
		for command in cog.get_commands():
			embed.add_field(name=command.name, value=command.help or "No description", inline=False)
		channel = self.get_destination()
		await channel.send(embed=embed)

	async def send_group_help(self, group):
		embed = discord.Embed(title=f"{group.qualified_name} Commands", description=group.help or "No description", color=0x00FF00)
		for command in group.commands:
			embed.add_field(name=command.name, value=command.help or "No description", inline=False)
		channel = self.get_destination()
		await channel.send(embed=embed)

	async def send_command_help(self, command):
		embed = discord.Embed(title=command.qualified_name, description=command.help or "No description", color=0x00FF00)
		embed.add_field(name="Usage", value=self.get_command_signature(command), inline=False)
		channel = self.get_destination()
		await channel.send(embed=embed)