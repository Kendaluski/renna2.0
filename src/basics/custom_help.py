from discord.ext import commands
import discord

class CustomHelpCmd(commands.HelpCommand):
    def __init__(self):
        super().__init__()

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title="Comandos de Renna", description="Aquí tienes una lista de todos mis comandos, puedes hacer +help <nombre_del_comando> para ver su información y cómo utilizarlo <:ok:1259851748659695728>", color=discord.Colour.magenta())
        cat = {}
        for command in self.context.bot.commands:
            if not command.hidden:
                category = getattr(command, "category", "Sin categoría")
                if category not in cat:
                    cat[category] = []
                cat[category].append(command.name)
        for k, cmds in cat.items():
            if k != "Sin categoría":
                embed.add_field(name=k, value=", ".join(cmds), inline=False)

        channel = self.get_destination()
        if isinstance(channel, discord.TextChannel):
            await channel.send(embed=embed)
        else:
            print("No valid destination channel found")

    async def send_command_help(self, command):
        embed = discord.Embed(title=command.qualified_name, description=command.help or "No description", color=discord.Colour.magenta())
        embed.add_field(name="Uso: ", value=self.get_command_signature(command), inline=False)
        channel = self.get_destination()
        if isinstance(channel, discord.TextChannel):
            await channel.send(embed=embed)
        else:
            print("No valid destination channel found")