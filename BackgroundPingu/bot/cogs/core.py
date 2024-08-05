import discord, re, traceback, random
from discord import commands
from discord.ext.commands import Cog
from datetime import datetime
from BackgroundPingu.bot.main import BackgroundPingu
from BackgroundPingu.core import parser, issues
from BackgroundPingu.bot.ui import views

class Core(Cog):
    def __init__(self, bot: BackgroundPingu) -> None:
        super().__init__()
        self.bot = bot
    
    async def check_log(self, msg: discord.Message, include_content=False):
        found_result = False
        result = {
            "text": None,
            "embed": None,
            "view": None
        }
        link_pattern = r"https:\/\/(?:api\.)?paste\.ee\/.\/\w+|https:\/\/mclo\.gs\/\w+|https?:\/\/[\w\-_\/.]+\.(?:txt|log|tdump)\?ex=[^&]+&is=[^&]+&hm=[^&]+&|https?:\/\/[\w\-_\/.]+\.(?:txt|log|tdump)"
        matches = re.findall(link_pattern, msg.content)
        if len(msg.attachments) > 0:
            for attachment in msg.attachments:
                matches.append(attachment.url)
        if len(matches) > 3: matches = random.sample(matches, 3)

        logs = [(match.split("?ex")[0], parser.Log.from_link(match)) for match in matches]
        logs = [(link, log) for (link, log) in logs if not log is None]
        logs = sorted(logs, key=lambda x: len(x[1]._content), reverse=True) # check the longest logs first
        if include_content: logs.append(("message", parser.Log(msg.content))) # check the message itself (last)
        
        for link, log in logs:
            try:
                results = issues.IssueChecker(self.bot, log, link, msg.guild.id if not msg.guild is None else None).check()
                if results.has_values():
                    messages = results.build()
                    result["embed"] = await self.build_embed(results, messages, msg)
                    result["view"] = views.Paginator(messages, results, msg)
                    found_result = True
            except Exception as e:
                error = "".join(traceback.format_exception(e))
                result["text"] = f"```\n{error}\n```\n<@695658634436411404> :bug:"
                found_result = True
            if found_result: break
        return result

    async def build_embed(self, results: issues.IssueBuilder, messages: list[str], msg: discord.Message):
        embed = discord.Embed(
            title=f"{results.amount} Issue{'s' if results.amount > 1 else ''} Found:",
            description=messages[0],
            color=self.bot.color,
            timestamp=datetime.now()
        )
        embed.set_author(name=msg.author.name, icon_url=msg.author.avatar.url if msg.author.avatar is not None else "")
        embed.set_footer(text=f"Page 1/{len(messages)}" + (f" • {results.footer}" if len(results.footer) > 0 else ""))
        return embed
    
    def should_reply(self, result: dict):
        return not result["text"] is None or (not result["embed"] is None and not result["view"] is None)

    @Cog.listener()
    async def on_message(self, msg: discord.Message):
        result = await self.check_log(msg)
        if self.should_reply(result):
            try:
                await msg.reply(content=result["text"], embed=result["embed"], view=result["view"])
            except discord.errors.Forbidden: pass
    
    @commands.message_command(name="Check Log")
    async def check_log_cmd(self, ctx: discord.ApplicationContext, msg: discord.Message):
        result = await self.check_log(msg, include_content=True)
        if self.should_reply(result):
            return await ctx.response.send_message(content=result["text"], embed=result["embed"], view=result["view"])
        return await ctx.response.send_message(":x: **No log or no issues found in this message.**", ephemeral=True)

def setup(bot: BackgroundPingu):
    bot.add_cog(Core(bot))
