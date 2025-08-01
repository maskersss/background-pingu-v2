import discord, re, traceback, random
from discord import commands
from discord.ext.commands import Cog
from datetime import datetime
from BackgroundPingu.bot.main import BackgroundPingu
from loghelper.issues.builder import IssueBuilder
from loghelper.issues.checker import IssueChecker
from loghelper import parser
from loghelper.config import *
from BackgroundPingu.bot.ui import views

class Core(Cog):
    def __init__(self, bot: BackgroundPingu) -> None:
        super().__init__()
        self.bot = bot
    
    async def get_logs_from_message(self, msg: discord.Message, include_content=False):
        link_pattern = LINK_PATTERN
        matches = re.findall(link_pattern, msg.content)
        if len(msg.attachments) > 0:
            for attachment in msg.attachments:
                matches.append(attachment.url)
        if len(matches) > 3: matches = random.sample(matches, 3)

        logs = [(match.split("?ex")[0], parser.Log.from_link(match)) for match in matches]
        logs = [(link, log) for (link, log) in logs if not log is None]
        logs = sorted(logs, key=lambda x: len(x[1]._content), reverse=True) # check the longest logs first
        if include_content: logs.append(("message", parser.Log(msg.content))) # check the message itself (last)

        return logs
    
    async def check_log(self, msg: discord.Message, include_content=False):
        if (not include_content
            and not msg.author.id in [
                473868086773153793,    # zeppelin
                1110166332059697222,   # pingu
                834848683697635328,    # test
            ]
            and msg.channel.id in [
                727673359860760627,    # javacord #public-help
                1074385256070791269,   # rankedcord #tech-help
                1262901524619595887,   # seedqueuecord #questions
                1062467804877561878,   # jinglecord #help-and-support
                933914673437368380,    # fsgcord #help
                1033763530798800908,   # srigtcord #support
                1071138999604891729,   # for testing
            ]
        ):
            include_content = True

        found_result = False
        result = {
            "text": None,
            "embed": None,
            "view": None
        }
        logs = await self.get_logs_from_message(msg, include_content)
        
        for link, log in logs:
            try:
                results = IssueChecker(
                    log,
                    link,
                    msg.guild.id if not msg.guild is None else None,
                    msg.channel.id if not msg.channel is None else None,
                    "discord",
                ).check()
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
    
    async def get_settings(self, msg: discord.Message) -> tuple[str, bool]:
        found_result = False
        result = None
        
        logs = await self.get_logs_from_message(msg, include_content=False)

        for link, log in logs:
            try:
                reply, success = IssueChecker(
                    log,
                    link,
                    msg.guild.id if not msg.guild is None else None,
                    msg.channel.id if not msg.channel is None else None,
                    "discord",
                ).seedqueue_settings()
                if success:
                    result = reply
                    found_result = True
            except Exception as e:
                error = "".join(traceback.format_exception(e))
                result = f"```\n{error}\n```\n<@695658634436411404> :bug:"
                found_result = True
            if found_result: break
        
        return (result, found_result)

    async def build_embed(self, results: IssueBuilder, messages: list[str], msg: discord.Message):
        embed = discord.Embed(
            title=f"{results.amount} Issue{'s' if results.amount > 1 else ''} Found:",
            description=messages[0],
            color=0xFFFFFF,
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
    
    @commands.message_command(name="Recommend Settings")
    async def recommend_settings_cmd(self, ctx: discord.ApplicationContext, msg: discord.Message):
        reply, found_result = await self.get_settings(msg)
        if found_result:
            return await ctx.response.send_message(content=reply)
        return await ctx.response.send_message(":x: **No log found in this message.**", ephemeral=True)

def setup(bot: BackgroundPingu):
    bot.add_cog(Core(bot))
