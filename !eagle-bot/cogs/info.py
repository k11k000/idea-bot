import disnake
from disnake.ext import commands
import methods


class InfoCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(description="Информация о боте.")
    async def info(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        embed = methods.embed("Информация", "https://github.com/k11k000/eagle-bot")
        await inter.edit_original_response(embed=embed)


def setup(bot: commands.Bot):
    methods.startprint(__name__)
    bot.add_cog(InfoCommand(bot))