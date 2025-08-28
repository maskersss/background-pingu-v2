from discord.ext import tasks
from discord.ext.commands import Cog
from BackgroundPingu.bot.main import BackgroundPingu
from loghelper.data import mods_getter

class ModCheck(Cog):
    def __init__(self, bot: BackgroundPingu) -> None:
        super().__init__()
        self.bot = bot
        self.mod_updater.start()
    
    def cog_unload(self) -> None:
        self.mod_updater.cancel()
        return super().cog_unload()

    @tasks.loop(minutes=15)
    async def mod_updater(self):
        self.bot.mods = mods_getter.get_mods(start=False)

def setup(bot: BackgroundPingu):
    bot.add_cog(ModCheck(bot))
