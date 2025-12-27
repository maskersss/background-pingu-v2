import discord, json, re, requests, traceback
from discord import commands
from discord.ext.commands import Cog
from BackgroundPingu.bot.main import BackgroundPingu
from loghelper.issues.builder import IssueBuilder
from loghelper.issues.checker import IssueChecker
from loghelper import parser
from loghelper.config import *

class Tips(Cog):
    def __init__(self, bot: BackgroundPingu) -> None:
        super().__init__()
        self.bot = bot
    
    @commands.slash_command(name="recommend_settings", description="Gives recommended settings for SeedQueue based on a log.")
    async def recommend_settings(
        self,
        ctx: discord.ApplicationContext,
        log: discord.Option(str, required=False),
    ):
        if log is None:
            text = "Please get a link to the log and provide it as a command parameter for this command[:](https://cdn.discordapp.com/attachments/531598137790562305/575381000398569493/unknown.png)"
            return await ctx.respond(text)

        link_pattern = LINK_PATTERN
        match = re.search(link_pattern, log)
        if match is None:
            text = "No pastee.dev or mclo.gs link found. Please get a link to the log and provide it as a command parameter for this command[:](https://cdn.discordapp.com/attachments/531598137790562305/575381000398569493/unknown.png)"
            if ctx.channel_id == 1271835972912545904: text += "\n_If you're still confused, you should ask in a help channel._"
            return await ctx.respond(text)

        link = match.group(0)     
        (link, log) = (link.split("?ex")[0], parser.Log.from_link(link))
        if log is None:
            text = "The link you provided is not valid. Please get a link to the log and provide it as a command parameter for this command[:](https://cdn.discordapp.com/attachments/531598137790562305/575381000398569493/unknown.png)"
            if ctx.channel_id == 1271835972912545904: text += "\n_If you're still confused, you should ask in a help channel._"
            return await ctx.respond(text)

        text, success = IssueChecker(
            log,
            link,
            ctx.guild_id,
            ctx.channel_id,
            ctx.author.id,
            "discord",
        ).seedqueue_settings()
        
        if not success:
            text = "The link you provided is not a valid log. Please get a link to the log and provide it as a command parameter by uploading it from your launcher[:](https://cdn.discordapp.com/attachments/531598137790562305/575381000398569493/unknown.png)"
            if ctx.channel_id == 1271835972912545904: text += "\n_If you're still confused, you should ask in a help channel._"
        
        return await ctx.respond(text)
    
    @commands.slash_command(name="fabric", description="A guide on how to install Fabric.")
    async def fabric(
        self,
        ctx: discord.ApplicationContext,
        launcher: discord.Option(str, choices=["MultiMC / Prism", "MCSR Launcher", "Official Launcher", "All"], required=False, default="All"),
    ):
        text = "For your mods to work, you need to install Fabric Loader."
        if launcher in ["MultiMC / Prism", "All"]: text += "\n- For MultiMC and Prism Launcher, see the image how to do that[.](https://i.imgur.com/ZR6UJCA.png)"
        if launcher in ["MCSR Launcher", "All"]: text += "\n- For MCSR Launcher, you can install Fabric by right clicking your instance and doing `Edit Instance > Version > Change Version`."
        if launcher in ["Official Launcher", "All"]: text += """\n- For official Minecraft Launcher, follow the instructions [**here**](<https://wiki.fabricmc.net/player:tutorials:install_mcl:windows>), up to step 3. Do **NOT** install Fabric API."""
        return await ctx.respond(text)

    @commands.slash_command(name="fastloot", description="Gives links to fastloot guides.")
    async def fastloot(self, ctx: discord.ApplicationContext):
        text = """### Guides on different types of fastlooting:

* RSG Fastlooting: <https://www.youtube.com/watch?v=ebd3q3HNnQA>
* SSG Fastlooting: <https://www.youtube.com/watch?v=uZC_XE1t5yQ>"""
        return await ctx.respond(text)
    
    @commands.slash_command(name="log", description="Shows how to send a log.")
    async def log(
        self,
        ctx: discord.ApplicationContext,
        launcher: discord.Option(str, choices=["MultiMC", "Prism", "Modrinth App", "Other"], required=False, default="MultiMC"),
    ):
        if launcher == "MultiMC": link = "https://i.imgur.com/MfrJwcM.png"
        elif launcher == "Prism": link = "https://i.imgur.com/wNlSlcn.png"
        elif launcher == "Modrinth App": link = "https://media.discordapp.net/attachments/727673359860760627/1446445444732420179/image.png"
        else: link = "https://media.discordapp.net/attachments/433058639956410383/1061333462826614844/image.png"
        text = f"Please send a log by following this image[:]({link})"
        return await ctx.respond(text)

    @commands.slash_command(name="mmclog", description="Shows how to send a log on MultiMC/Prism Launcher.")
    async def mmclog(self, ctx: discord.ApplicationContext):
        return await self.log(ctx, "MultiMC")

    @commands.slash_command(name="borderless", description="Explains how to run Minecraft as a borderless window.")
    async def borderless(self, ctx: discord.ApplicationContext):
        text = """If you use [Jingle](<https://github.com/DuncanRuns/Jingle/releases>) (recommended), simply click "Go Borderless".
Otherwise, [application to run Minecraft as a borderless window](<https://github.com/Mr-Technician/BorderlessMinecraft/releases>)
ℹ️ Make sure to disable fullscreen in Options ⟶ Book & Quill ⟶ StandardSettings."""
        return await ctx.respond(text)

    @commands.slash_command(name="mcsr", description="Explains that MCSR != Ranked.")
    async def mcsr(self, ctx: discord.ApplicationContext):
        text = """"MCSR" is short for "minecraft speedrunning", and is usually used to refer to the minecraft speedrunning community.
If you're referring to the mod that allows people to speedrun 1v1, that's "MCSR Ranked" or "Ranked" for short <:Okayge:796454436427005984>"""
        return await ctx.respond(text)

    @commands.slash_command(name="onedrive", description="Explains that OneDrive is bad.")
    async def onedrive(self, ctx: discord.ApplicationContext):
        text = """OneDrive can mess with your game files to save space, and this can lead to issues. If your launcher folder is located in OneDrive, you should move it out to a different folder, for example to "C:/MultiMC/".
If you want to unlink OneDrive, follow [this link](<https://support.microsoft.com/en-au/office/turn-off-disable-or-uninstall-onedrive-f32a17ce-3336-40fe-9c38-6efb09f944b0>)."""
        return await ctx.respond(text)

    @commands.slash_command(name="rankedfaq", description="Sends a link to the MCSR Ranked Tech Support FAQ document.")
    async def rankedfaq(self, ctx: discord.ApplicationContext):
        text = """You can find MCSR Ranked Tech Support FAQ document here: <https://wiki.mcsrranked.com/install/faq>"""
        return await ctx.respond(text)

    @commands.slash_command(name="regions", description="Gives an infographic about structure regions.")
    async def regions(self, ctx: discord.ApplicationContext):
        text = """https://cdn.discordapp.com/attachments/83066801105145856/1033984974614962286/1.16.1_Regions.png"""
        return await ctx.respond(text)

    @commands.slash_command(name="ahk", description="Gives a guide to rebind keys using AutoHotkey.")
    async def ahk(self, ctx: discord.ApplicationContext):
        text = """To rebind keys, you can download AutoHotkey (<https://www.autohotkey.com/>, **make sure to get version 1.1**) and create a file with your desired key bindings. For instance, if you want to swap the keys "F3" and "r", you can create a file and name it *something*.ahk with the following content:
```ahk
#IfWinActive Minecraft
*F3::r
*r::F3```Launch the file, and the input of keys "F3" and "r" will be swapped (which means pressing "r" will open the debug menu).
You can customize the key bindings as desired, see this for help: <https://www.autohotkey.com/docs/v1/KeyList.htm> 

**Rebind Rules**
You may remap keys using external programs, but:
• Each game input may have only one key, and each key may cause only one game input
• F3 shortcuts (such as F3+C, Shift+F3, etc.) can't be bound to a single button
• Inputs must be buttons - no scrolling the scroll-wheel or similar
• Rebinding "Attack/Destroy" or "Use Item/Place Block" to a keyboard button in order to abuse as an autoclicker is not allowed"""
        return await ctx.respond(text)

    @commands.slash_command(name="rebind", description="Gives a guide to rebind keys using AutoHotkey.")
    async def rebind(self, ctx: discord.ApplicationContext):
        return await self.ahk(ctx)

    @commands.slash_command(name="new", description="Provides a comprehensive guide to start learning speedrunning.")
    async def new(self, ctx: discord.ApplicationContext):
        text = """The most popular category/version to run is 1.16.1 Any% Random Seed Glitchless, so we're assuming you're planning to run this category.

[Follow this video for a tutorial to set up Minecraft for speedrunning.](<https://youtu.be/RSLv7FfQZKY>) It goes through everything from setting up Prism Launcher to installing mods and practice maps, so it's highly recommended to watch this first.

The most important things to learn when starting out are bastion routes and one-cycling. Watch [these videos for introductory bastion routes](<https://www.youtube.com/playlist?list=PL7Q35RXRsOR-udeKzwlYGJd0ZrvGJ0fwu>) and [this video for one-cycling.](<https://youtu.be/JaVyuTyDxxs>)

In general, it's a good idea to watch top runs and top runners' streams to get a feel of how a speedrun goes. Here's a [more comprehensive playlist](<https://www.youtube.com/playlist?list=PLwJbTWLH-1dakBZaROfNJZ-m59OQg_hFp>) and a [full comprehensive guide](<https://metafy.gg/guides/view/ultimate-minecraft-speedrun-guide-cIzfjeTmwOm>), but since they cover a lot of strategies it may seem overwhelming at first, so take it easy."""
        return await ctx.respond(text)

    @commands.slash_command(name="tutorials", description="Links Couriway's Metafy guide and Osh's tutorials YouTube playlist.")
    async def tutorials(self, ctx: discord.ApplicationContext):
        text = """Couriway's Metafy guide: <https://metafy.gg/guides/view/ultimate-minecraft-speedrun-guide-cIzfjeTmwOm>
-# (it is free, you just need to create an account)

Osh's tutorials playlist: <https://www.youtube.com/playlist?list=PLwJbTWLH-1dakBZaROfNJZ-m59OQg_hFp>"""
        return await ctx.respond(text)

    @commands.slash_command(name="jarfix", description="Explains how to fix jar files not opening.")
    async def jarfix(self, ctx: discord.ApplicationContext):
        text = "If you're having issues with .jar programs on Windows, download and run this Java installer: https://aka.ms/download-jdk/microsoft-jdk-21-windows-x64.msi ."
        return await ctx.respond(text)

    @commands.slash_command(name="folderinafolder", description="Explains the correct practice map folder structure.")
    async def folderinafolder(self, ctx: discord.ApplicationContext):
        text = "https://cdn.discordapp.com/attachments/433058639956410383/1195805874120314941/image.png"
        return await ctx.respond(text)

    @commands.slash_command(name="java", description="Gives a guide to update Java.")
    async def java(
        self,
        ctx: discord.ApplicationContext,
        launcher: discord.Option(str, choices=["MCSR Launcher", "Prism", "MultiMC", "Official Launcher", "All"], required=False, default="All"),
        os: discord.Option(str, choices=["Windows", "Linux", "macOS"], required=False, default="Windows"),
    ):
        text = ""

        if launcher == "Official Launcher":
            text += f"We do not recommend using the official Minecraft launcher since it is [tedious](<https://bit.ly/updatejavamc>) to switch Java versions. Type `/setup` to set up Prism for speedrunning.\n"
        elif launcher == "MCSR Launcher":
            text += "On MCSR Launcher, use this guide to update your Java version[:](https://gist.github.com/user-attachments/assets/60d308c6-5782-469a-a532-a2c57993881b) <https://gist.github.com/maskersss/ee30ca16d33e7b8bb51e246ff62c83d6>.\n"
        elif launcher == "Prism":
            text += "On Prism, use this guide to update your Java version[:](https://gist.github.com/user-attachments/assets/2cb8c15b-caf1-40ef-8e8e-3f8b736df254) <https://gist.github.com/maskersss/0993754fb91686f78f8c000280699fa4>.\n"
        else:
            if launcher == "All":
                text += "* If you're using MCSR Launcher: use [**this guide**](<https://gist.github.com/maskersss/ee30ca16d33e7b8bb51e246ff62c83d6>) to update your Java version.\n"
                text += "* If you're using Prism: use [**this guide**](<https://gist.github.com/maskersss/0993754fb91686f78f8c000280699fa4>) to update your Java version.\n"
            if os == "Linux":
                text += f"* If you're using MultiMC:\n  * You can install the latest version of Java [**here**](<https://www.google.com/search?q=%7Binsert+your+distro+name+here%7D+how+to+install+java+21>).\n"
            else:
                if os == "Windows":
                    text += "* If you're using MultiMC:\n  * On Windows, install the latest version of Java by downloading **and running** the Microsoft Java installer: <https://aka.ms/download-jdk/microsoft-jdk-21-windows-x64.msi>.\n"
                    text += "    * When prompted, it is recommended you install Java **for all users**.\n"
                else: # macos
                    query_string = "?os=mac&package=jdk&version=21&mode=filter"
                    text += f"* If you're using MultiMC:\n  * On macOS, you can install the latest version of Java [**here**](<https://adoptium.net/temurin/releases/{query_string}>)."
                    text += " Download and run the `.pkg` file.\n"

            text += "  * After installing Java, follow the steps in the image below[:](https://cdn.discordapp.com/attachments/433058639956410383/1172533931485175879/image.png)\n"
            text += "    * If the Java you installed doesn't show up, click `Refresh` on the bottom left in the `Auto-detect` menu.\n"
            if launcher == "All": text += f"* We do not recommend using the official Minecraft launcher since it is [tedious](<https://bit.ly/updatejavamc>) to switch Java versions. Type `/setup` to set up Prism for speedrunning.\n"
        
        return await ctx.respond(text.strip())

    @commands.slash_command(name="ninjabrainbot", description="Gives a guide to using Ninjabrain Bot.")
    async def ninjabrainbot(self, ctx: discord.ApplicationContext):
        text = """Download: <https://github.com/Ninjabrain1/Ninjabrain-Bot/releases/latest>
Tutorial: https://youtu.be/Gp6EnDs24NI"""
        return await ctx.respond(text)

    @commands.slash_command(name="nbbdebug", description="Gives a guide to debugging Ninjabrain Bot.")
    async def nbbdebug(self, ctx: discord.ApplicationContext):
        text = """To troubleshoot issues with Ninjabrain Bot, please send the following information:
- Screenshots of these Ninjabrain Bot tabs in options: `Basic`, `Advanced`, Optional features ➔ `Angle adjustment` & `Boat measurement`
- These files in your instance folder: `.minecraft/config/mcsr/standardsettings.json` and `.minecraft/options.txt`
Also, make sure that the resolution for Jingle ➔ Scripts ➔ Resizing ➔ Customize ➔ "Eye measuring size" is set to `384x16384` , and make sure you're switching to 30 FOV.
-# You don't need to retype this command, it just sends this text."""
        return await ctx.respond(text)

    @commands.slash_command(name="nbbfaq", description="Links a Ninjabrain Bot FAQ document.")
    async def nbbfaq(self, ctx: discord.ApplicationContext):
        text = """https://docs.google.com/document/d/1aYxL747PI6Lr0rgPSFmO-wvL6P7-YPLpNJewCJU86n0"""
        return await ctx.respond(text)

    @commands.slash_command(name="mpkdebug", description="Gives a guide to debugging MiniPracticeKit not working.")
    async def mpkdebug(self, ctx: discord.ApplicationContext):
        text = """To troubleshoot MiniPracticeKit not working, please verify the following:
- A 20-100 KB file named **exactly** "hotbar" or "hotbar.nbt", __not__ "hotbar (1).nbt" or similar, exists in your .minecraft folder.
- You are pressing your **Hotbar slot 1** hotkey while holding your **Load hotbar** hotkey, and both of these aren't conflicting with other hotkeys."""
        return await ctx.respond(text)

    @commands.slash_command(name="prism", description="Gives a link to download Prism Launcher.")
    async def prism(
        self,
        ctx: discord.ApplicationContext,
        nightly: discord.Option(bool, choices=[True, False], required=False, default=False),
    ):
        text = "Prism Launcher is a more updated fork of MultiMC. "
        if not nightly:
            text += """You can download it here: https://prismlauncher.org/"""
        else:
            text += """You can download the latest development builds of it here: https://nightly.link/PrismLauncher/PrismLauncher/workflows/trigger_builds/develop.

> :warning: Warning :warning:
> Development builds have been less tested and are therefore more likely to have bugs! For this reason, it's recommended to use Portable builds – for Windows, that would be the second lowest option on the above page."""
        return await ctx.respond(text)

    @commands.slash_command(name="setup", description="Gives a link to a tutorial to setup Minecraft Speedrunning.")
    async def setup(
        self,
        ctx: discord.ApplicationContext,
        os: discord.Option(str, choices=["Windows", "Linux", "macOS"], required=False, default="Windows"),
    ):
        if os == "macOS": text = """To set up speedrunning on Mac, follow [the macOS setup guide](<https://www.youtube.com/watch?v=GomIeW5xdBM>) to install everything and for some additional tips, and then follow [the 2025 setup guide](<https://www.youtube.com/watch?v=RSLv7FfQZKY&t=193s>) to download and configure mods.

To run several instances, use **SeedQueue** (`/seedqueue`).
[SlackowWall](<https://github.com/Slackow/SlackowWall/releases/latest>): used for resizing Minecraft.
Boateye guide: <https://youtu.be/Mj42HbnPUZ4>

Mac speedrunning discord: <https://discord.gg/sczfsdE39W>"""
        elif os == "Linux": text = """Guide to setup Minecraft for speedrunning on Linux: <https://its-saanvi.github.io/linux-mcsr>

resetti (for window resizing on X11, and multi-instancing on versions without SeedQueue): <https://github.com/tesselslate/resetti>
waywall (for window resizing on Wayland + many useful features): <https://tesselslate.github.io/waywall>

MCSR Linux Discord server: https://discord.gg/CVxuagAXMt"""
        else: text = """1.16.1/1.15.2 setup video tutorial, including SeedQueue: https://youtu.be/RSLv7FfQZKY
For other categories/versions, follow [this video](<https://youtu.be/VL8Syekw4Q0>), substituting any mention of 1.16.1 & RSG for your chosen category/version."""
        
        return await ctx.respond(text)
    
    @commands.slash_command(name="dmvc", description="Explains why using DMs/VCs for support is bad.")
    async def dmvc(self, ctx: discord.ApplicationContext):
        server_id = ctx.guild_id
        channel = "a support channel"
        for sid, cid, _ in SERVER_SUPPORT_BOT_CHANNEL_IDS:
            if sid == server_id and not cid is None:
                channel = f"<#{cid}> "
                break
        text = f"""If you have a problem, type your problem in {channel}. Please do not ask to VC or DM, using voice chats or direct messages are a bad way to solve your problem, since:

1) You are making the other person to commit to helping you.
2) The person might not know how to solve your issue.
3) Other people can't correct them if they are wrong.
4) They require the person's schedule and availability to line up with yours."""
        return await ctx.respond(text)
    
    @commands.slash_command(name="linux", description="Gives a link to a Linux tutorial for MCSR.")
    async def linux(self, ctx: discord.ApplicationContext):
        return await self.setup(ctx, os="Linux")

    @commands.slash_command(name="sodium", description="Explains that the Sodium settings GUI is no longer a thing.")
    async def sodium(self, ctx: discord.ApplicationContext):
        text = """"Video settings" uses **vanilla UI** if you access it from the options menu. You can access all Sodium settings from Options > Book and Quill > Sodium. __You can't get the Sodium UI anymore. This is intended.__"""
        return await ctx.respond(text)

    @commands.slash_command(name="mac", description="Gives links to tutorials for Minecraft Speedrunning on a Mac.")
    async def mac(self, ctx: discord.ApplicationContext):
        return await self.setup(ctx, os="macOS")

    @commands.slash_command(name="1_16_1", description="Explains why using 1.16.1 is standard for Minecraft speedrunning.")
    async def one_sixteen_one(self, ctx: discord.ApplicationContext):
        text = "1.16.1 gives 4x more pearls and 3x more string from piglin barters on average compared to later versions. This, as well as not having piglin brutes, means that using 1.16.1 is standard and recommended for Minecraft speedrunning. You can play later versions if you wish (the category is 1.16+) but it will put you at a severe disadvantage. This only applies for RSG Any%, not SSG (which uses different versions) or other category extensions."
        return await ctx.respond(text)

    @commands.slash_command(name="mapless", description="Gives links to mapless tutorials.")
    async def mapless(self, ctx: discord.ApplicationContext):
        text = """meebie's tutorial: https://youtu.be/o0LDg3fe2iI
older tutorials: https://discord.com/channels/83066801105145856/433058639956410383/1310491974381600788"""
        return await ctx.respond(text)

    @commands.slash_command(name="discords", description="Gives a link to the MCSR discords spreadsheet.")
    async def discords(self, ctx: discord.ApplicationContext):
        text = "https://docs.google.com/spreadsheets/d/1Gry6LCYV3VPYNekp1LE0KfuGPnAboa3zXvj545mshJU/edit#gid=0"
        return await ctx.respond(text)

    @commands.slash_command(name="divine", description="Gives an infographic for nether fossil divine.")
    async def divine(self, ctx: discord.ApplicationContext):
        text = "https://cdn.discordapp.com/attachments/433058639956410383/897752137507946496/Screenshot_25.png"
        return await ctx.respond(text)

    @commands.slash_command(name="preemptivebug", description="Explains the preemptive bug.")
    async def preemptivebug(self, ctx: discord.ApplicationContext):
        text = "The pie chart may occasionally bug and give spikes significantly higher than expected. Assuming you're on Windows and your Minecraft is using an NVIDIA GPU, you can fix this by turning off \"Threaded optimization\" in the NVIDIA Control Panel, which you can access by right-clicking your Desktop[:](https://cdn.discordapp.com/attachments/433058639956410383/1166992505296920628/image.png)"
        return await ctx.respond(text)

    @commands.slash_command(name="julti", description="Gives a link to a Julti tutorial.")
    async def julti(self, ctx: discord.ApplicationContext):
        text = """**Julti is no longer recommended for 1.16.1 & 1.15.2, you should use [SeedQueue](<https://www.youtube.com/watch?v=RSLv7FfQZKY>) and [Jingle](<https://github.com/DuncanRuns/Jingle>) instead.**
Julti tutorial: <https://youtu.be/_8gQkgZcTKo>
Julti discord: <https://discord.gg/cXf86mXAWR>"""
        return await ctx.respond(text)

    @commands.slash_command(name="jingle", description="Gives a link to Jingle's GitHub page.")
    async def jingle(self, ctx: discord.ApplicationContext):
        text = """Speedrunning utility application by DuncanRuns
Download: <https://github.com/DuncanRuns/Jingle/releases>
Support discord: <https://discord.gg/cXf86mXAWR>"""
        return await ctx.respond(text)

    @commands.slash_command(name="worldbopper", description="Gives links to programs for auto-deleting worlds.")
    async def worldbopper(self, ctx: discord.ApplicationContext):
        text = """To delete worlds, you can use the **Clear Worlds** button in [**Jingle**](<https://github.com/DuncanRuns/Jingle>).
If you want worlds to be deleted automatically, you can use the [**Jingle WorldBopper plugin**](<https://github.com/marin774/Jingle-WorldBopper-Plugin>)."""
        return await ctx.respond(text)
    
    @commands.slash_command(name="seedqueue", description="Explains what SeedQueue is.")
    async def seedqueue(self, ctx: discord.ApplicationContext):
        text = """SeedQueue is a mod that is meant to replace multi-instancing. Instead of having multiple Minecrafts generating worlds open at the same time, it does it all in just one Minecraft instance. This greatly improves performance, especially for lower end hardware, and is also aimed to make speedrunning more accessible.
Download: <https://github.com/contariaa/seedqueue/releases>
Explanation: <https://www.youtube.com/watch?v=fGu2MYZxh_c>
Tutorial: <https://www.youtube.com/watch?v=RSLv7FfQZKY>
Wiki: <https://github.com/contariaa/seedqueue/wiki>
Discord server: <https://discord.gg/9P6PJkHCdU>"""
        return await ctx.respond(text)
    
    @commands.slash_command(name="coaching", description="Provides information on coaching / learning speedrunning.")
    async def coaching(self, ctx: discord.ApplicationContext):
        text = """Coaching in MCSR isn’t something most people have access to. 
Long-term coaching usually only happens between friends, content creators who stream it, or paid services.

**If you’re looking for help starting out, type `!!new` in <#433058639956410383> for setup information and resources.**

If you want an idea of what coaching looks like, here are some playlists of coaching VODs you can learn from:

Couriway - Midoffs S1 <https://www.youtube.com/watch?v=1h-Uqhc_DtQ&list=PLiNXLWzA7YLYKZ_KYdn3N52we4B3bn4vK>
Nerdi - Speedrun Bootcamp <https://www.youtube.com/watch?v=pDLufpy11GY&list=PLiNHtofX3klVmUMUxRbi2R8jcVSW9OE9_>"""
        return await ctx.respond(text)

    @commands.slash_command(name="sq", description="Explains what SeedQueue is.")
    async def sq(self, ctx: discord.ApplicationContext):
        return await self.seedqueue(ctx)

    @commands.slash_command(name="wall", description="Redirects to `/seedqueue`.")
    async def wall(self, ctx: discord.ApplicationContext):
        return await self.seedqueue(ctx)
    
    @commands.slash_command(name="zgc", description="Gives an explanation of Z Garbage Collector.")
    async def zgc(
        self,
        ctx: discord.ApplicationContext,
        launcher: discord.Option(str, choices=["MultiMC / Prism", "Official Launcher"], required=False, default="MultiMC / Prism"),
    ):
        text = """Z Garbage Collector (ZGC) is a garbage collector that improves performance and reduces lag spikes, though it uses more memory. It's currently **recommended** over the default GC if you use SeedQueue.
To use ZGC, set Minecraft to use Java 17+ if you haven't already done so (do `/java`), then"""
        if launcher == "MultiMC / Prism":
            text += "\n- If you're on MultiMC or Prism: Go to `Settings > Java` and set your JVM arguments to `-XX:+UseZGC`."
        else:
            text += "\n- If you're on the official Minecraft launcher: Go to Installations > \"...\" for the installation you're using > Edit > More options and in the JVM arguments text field, find and replace `-XX:+UseG1GC` with `-XX:+UseZGC`."
        
        return await ctx.respond(text)
    
    @commands.slash_command(name="graalvm", description="Gives a link to the GraalVM guide.")
    async def graalvm(self, ctx: discord.ApplicationContext):
        text = """GraalVM is a Java compiler that performs worse than other compilers at the start of sessions, but speeds up as the session goes on.
[Download (Windows)](https://download.oracle.com/graalvm/21/latest/graalvm-jdk-21_windows-x64_bin.zip)
[Guide](<https://gist.github.com/maskersss/5847d594fc6ce4feb66fbd2d3fda281d#graalvm>)"""
        return await ctx.respond(text)

    @commands.slash_command(name="modcheck", description="Gives a link to ModCheck.")
    async def modcheck(self, ctx: discord.ApplicationContext):
        text = "Application that helps install the allowed mods: <https://github.com/tildejustin/modcheck/releases/latest>"
        return await ctx.respond(text)

    @commands.slash_command(name="1_16mods", description="Gives an explanation of 1.16 mods.")
    async def one_sixteen_mods(self, ctx: discord.ApplicationContext):
        text = """Download the mods by using [**ModCheck**](<https://github.com/tildejustin/modcheck/releases/latest>) or from <https://mods.tildejustin.dev/>.
All other mods are banned[.](https://i.imgur.com/8k1LyKZ.png)"""
        return await ctx.respond(text)

    @commands.slash_command(name="areessgee", description="Gives a link to AreEssGee.")
    async def areessgee(self, ctx: discord.ApplicationContext):
        text = """AreEssGee is a configurable artificial seed generator mod. <https://github.com/faluhub/AreEssGee>
Join <https://discord.gg/s9m8gf6pju> if you have any questions about / issues with this mod. 
You can submit to the [AreEssGee leaderboard](<https://docs.google.com/spreadsheets/d/1n5Z3qsWbQX_uImx-HvzGacRpa6FjT5USRBnDKcsQbQ0/edit#gid=0>) in that server.
⚠️ *AreEssGee requires Java 17+. Type `/java` if you need help with updating your Java version.*"""
        return await ctx.respond(text)

    @commands.slash_command(name="peepopractice", description="Gives a link to PeepoPractice.")
    async def peepopractice(self, ctx: discord.ApplicationContext):
        text = """PeepoPractice is a versatile Fabric 1.16.1 mod to practice splits of Minecraft speedruns. It includes mapless, bastion, fortress, postblind, stronghold, end, AA splits and more.
Don't forget to check the FAQ in the readme! 
<https://github.com/faluhub/peepoPractice>
:warning: *PeepoPractice is incompatible with FastReset and requires Java 17+. Do `/java` if you need help with updating your Java version.*"""
        return await ctx.respond(text)

    @commands.slash_command(name="allowedmods", description="Gives a link to allowed mods.")
    async def allowedmods(self, ctx: discord.ApplicationContext):
        text = """If you use Optifine (allowed only before 1.15), please read section A.8 of the [detailed rules](<https://www.minecraftspeedrunning.com/public-resources/rules>).
All allowed mods can be downloaded from <https://mods.tildejustin.dev/> or by using [**ModCheck**](<https://github.com/tildejustin/modcheck/releases/latest>).
All other mods, including Fabric API, are banned[.](https://i.imgur.com/ulBwh7C.png)"""
        return await ctx.respond(text)

    @commands.slash_command(name="piedirectory", description="Gives the useful pie directories.")
    async def piedirectory(
        self,
        ctx: discord.ApplicationContext,
        directory: discord.Option(str, choices=["Mapless / Preemptive", "Village / Fortress", "All"], required="False", default="All"),
    ):
        text = "Common piechart directories:"
        if directory in ["Mapless / Preemptive", "All"]:
            text += "\n- Mapless / Preemptive: ```root.gameRenderer.level.entities```"
        if directory in ["Village / Fortress", "All"]:
            text += "\n- Village / Fortress: ```root.tick.level.entities.blockEntities```"""
        
        text += "\nIf you're using the StandardSettings mod, you can paste it into the `Pie Directory` option in `Options > Book and Quill > StandardSettings` to reset your pie chart to the given directory on reset."

        return await ctx.respond(text)

    @commands.slash_command(name="perch", description="Gives the command to force the dragon to perch.")
    async def perch(self, ctx: discord.ApplicationContext):
        text = """1.13+:```/data merge entity @e[type=ender_dragon,limit=1] {DragonPhase:2}```1.11-1.12:```/entitydata @e[type=ender_dragon] {DragonPhase:2}```1.9-1.10:```/entitydata @e[type=EnderDragon] {DragonPhase:3}```"""
        return await ctx.respond(text)

    @commands.slash_command(name="standardsettings", description="Explains what StandardSettings is.")
    async def standardsettings(self, ctx: discord.ApplicationContext):
        text = """If your settings reset whenever you create a world, you are probably using StandardSettings.
If you want to change which settings reset and what do they reset to, go to Options > Book and Quill > StandardSettings and configure them.
If you don't want your settings to reset, set "Use StandardSettings" there to "OFF"."""
        return await ctx.respond(text)

    # remove the spaces          (here) when uncommenting, also for `/modpack`
    '''@commands.slash_command(name = "modpack_list", description="Gives a list of MCSR modpacks.")
    async def modpack_list(self, ctx: discord.ApplicationContext):
        text = """### Modpacks for [PrismLauncher](<https://prismlauncher.org/>) / [MultiMC](<https://multimc.org/>) / [ATLauncher](<https://atlauncher.com/>)
Do `/modpack` for a tutorial on how to import them.
If the game crashes when it starts up, do `/java`.
If you're wondering why your settings keep resetting, do `/standardsettings`.
- **Full RSG 1.16.1 Pack (Includes all RSG mods, __RECOMMENDED__) (Requires Java 17+ (`/java`))**
  - Download: **[Windows](https://mods.tildejustin.dev/modpacks/v4/MCSR-1.16.1-Windows-RSG.mrpack) | [macOS](https://mods.tildejustin.dev/modpacks/v4/MCSR-1.16.1-OSX-RSG.mrpack) | [Linux](https://mods.tildejustin.dev/modpacks/v4/MCSR-1.16.1-Linux-RSG.mrpack)**
- **Full SSG 1.16.5 Pack (Includes all SSG mods, __RECOMMENDED__) (Requires Java 17+ (`/java`))**
  - Download: **[Windows](https://mods.tildejustin.dev/modpacks/v4/MCSR-1.16.5-Windows-SSG.mrpack) | [macOS](https://mods.tildejustin.dev/modpacks/v4/MCSR-1.16.5-OSX-SSG.mrpack) | [Linux](https://mods.tildejustin.dev/modpacks/v4/MCSR-1.16.5-Linux-SSG.mrpack)**
- **Normal Ranked Pack (Includes basic mods for MCSR Ranked, __RECOMMENDED__)**
  - Download: **[Windows](https://mods.tildejustin.dev/modpacks/v4/MCSRRanked-Windows-1.16.1.mrpack) | [macOS](https://mods.tildejustin.dev/modpacks/v4/MCSRRanked-OSX-1.16.1.mrpack) | [Linux](https://mods.tildejustin.dev/modpacks/v4/MCSRRanked-Linux-1.16.1.mrpack)**
- **Full Ranked Pack (Requires __Java 17+__ (`/java`))**
  - Download: **[Windows](https://mods.tildejustin.dev/modpacks/v4/MCSRRanked-Windows-1.16.1-Pro.mrpack) | [macOS](https://mods.tildejustin.dev/modpacks/v4/MCSRRanked-OSX-1.16.1-Pro.mrpack) | [Linux](https://mods.tildejustin.dev/modpacks/v4/MCSRRanked-Linux-1.16.1-Pro.mrpack)**"""
        return await ctx.respond(text)'''

    @commands.slash_command(name="modpack", description="Links a speedrunning Modrinth modpack.")
    async def modpack(self, ctx: discord.ApplicationContext):
        text = """Contains all mods that are verifiable on speedrun.com for modern versions of Minecraft.
To import it into MultiMC/Prism, go to Add Instance > Modrinth, search for "SpeedrunPack", select it and press OK.
https://modrinth.com/modpack/speedrun"""
        return await ctx.respond(text)

    @commands.slash_command(name="practicemaps", description="Gives a list of practice maps.")
    async def practicemaps(self, ctx: discord.ApplicationContext):
        text = """*Consider getting [MapCheck](<https://github.com/cylorun/Map-Check/releases/latest>) to download multiple maps at once.*
[MCSR Practice Map](<https://github.com/Dibedy/The-MCSR-Practice-Map/releases/latest>)
[Bastions](<https://github.com/LlamaPag/bastion/releases/latest>)
[Blaze](<https://github.com/Mescht/Blaze-Practice/releases/latest>)
[Buried treasure](<https://github.com/Mescht/BTPractice/releases/latest>)
[Crafting](<https://github.com/Semperzz/Crafting-Practice-v2/releases/latest>) / [Search crafting](<https://github.com/7rowl/Search-Crafting-Practice/releases/latest>)
[One cycle & End practice](<https://github.com/ryguy2k4/ryguy2k4endpractice/releases/latest>)
[Overworld](<https://github.com/7rowl/OWPractice/releases/latest>)
[Portals](<https://github.com/Semperzz/Portal-Practice/releases/latest>)
[Zero cycle](<https://github.com/Mescht/Zero-Practice/releases/latest>) / [Mongeycoaster variant](<https://drive.google.com/drive/folders/1Z9RSDIwlg5E6U5JdrdZPRvqM8AyqZDP->)
Practice mods:
[PeepoPractice, for practicing splits](<https://github.com/faluhub/peepoPractice>) (‼️ needs java 17+ and is incompatible with fastreset)"""
        return await ctx.respond(text)

    @commands.slash_command(name="mapcheck", description="Gives a link to MapCheck.")
    async def mapcheck(self, ctx: discord.ApplicationContext):
        text = "Application that helps downloading minecraft speedrun practice maps: <https://github.com/cylorun/Map-Check/releases/latest>"
        return await ctx.respond(text)

    @commands.slash_command(name="boateye", description="Gives a link to boat measurement setup guide.")
    async def boateye(self, ctx: discord.ApplicationContext):
        text = """Guide to set up boat eye: https://youtu.be/l1Z2t9e6Qko"""
        return await ctx.respond(text)

    @commands.slash_command(name="entity_culling", description="Explains how to turn off Entity Culling to fix e-1.")
    async def entity_culling(self, ctx: discord.ApplicationContext):
        text = "If your entity counter on F3 is `-1` or there isn't a `blockEntities` slice on the piechart in `root.gameRenderer.level.entities`, turn off `Entity Culling` in `Video Settings`."
        return await ctx.respond(text)

    @commands.slash_command(name="multidraw", description="Explains how to turn off Chunk Multidraw.")
    async def multidraw(self, ctx: discord.ApplicationContext):
        text = "If you're experiencing graphics related issues, such as water being invisible or blocks being inside you, try turning off `Chunk Multidraw` in `Options > Book and Quill > Sodium`."
        return await ctx.respond(text)

    @commands.slash_command(name="igpu", description="Gives a guide to get Minecraft to use the high-performance GPU.")
    async def igpu(self, ctx: discord.ApplicationContext):
        text = "If you are experiencing bad performance or graphics-related issues, it's possible that Minecraft is using your integrated GPU. To ensure that Minecraft uses your high-performance GPU, please follow this guide: <https://docs.google.com/document/d/1aPF1lyBAfPWyeHIH80F8JJw8rvvy6lRm0WJ2xxSrRh8/edit#heading=h.4oyoeerdwbr2>"
        return await ctx.respond(text)

    @commands.slash_command(name="desync", description="Gives a guide to ender eye desync for Minecraft speedruns.")
    async def desync(self, ctx: discord.ApplicationContext):
        text = "https://www.youtube.com/watch?v=uBqAeZMlEFQ"
        return await ctx.respond(text)

    @commands.slash_command(name="eyezoom", description="Gives a link to a tutorial for Eye Zoom Macro.")
    async def eyezoom(self, ctx: discord.ApplicationContext):
        text = """Link to Jingle (Download the .jar file): ⁠<https://github.com/DuncanRuns/Jingle/releases>
Open Jingle and add a hotkey for **Eye Measuring** under the **Hotkeys** tab.

**Eye Line-up:**
The right edge of the crosshair should line up with the left edge of the eye's middle pixel, as shown in the image below[:](https://cdn.discordapp.com/attachments/433058639956410383/1325558188044587038/image.png)"""
        return await ctx.respond(text)

    @commands.slash_command(name="ram", description="Gives a guide to change the amount of allocated RAM.")
    async def ram(
        self,
        ctx: discord.ApplicationContext,
        launcher: discord.Option(str, choices=["MultiMC / Prism", "Official Launcher"], required=False, default="MultiMC / Prism"),
    ):
        if launcher == "MultiMC / Prism": text = "https://i.imgur.com/UgdLz7W.png"
        else: text = "https://media.discordapp.net/attachments/433058639956410383/996360988179828746/unknown.png"
        return await ctx.respond(text)

    @commands.slash_command(name="rawaccel", description="Links the RawAccel guide.")
    async def rawaccel(self, ctx: discord.ApplicationContext):
        text = """## RawAccel
If you do not have software for your mouse, or you are limited to certain DPI options, then you can use alternative software like RawAccel to change your desktop sensitivity.

[RawAccel Guide (Timestamped)](<https://youtu.be/l1Z2t9e6Qko&t=217>)"""
        return await ctx.respond(text)

    @commands.slash_command(name="rules", description="Links the speedrun.com rules document.")
    async def rules(self, ctx: discord.ApplicationContext):
        text = "<https://rules.minecraftspeedrunning.com/latest>"
        return await ctx.respond(text)

    @commands.slash_command(name="packs", description="Links the speedrun.com resource packs rules.")
    async def packs(self, ctx: discord.ApplicationContext):
        text = "Read section A.4 for resource pack rules: <https://rules.minecraftspeedrunning.com/latest>"
        return await ctx.respond(text)

    @commands.slash_command(name="thinmag", description="Links a guide to set up the E-Counter with the ThinBT macro.")
    async def thinmag(self, ctx: discord.ApplicationContext):
        text = "https://www.youtube.com/watch?v=ZXPM1f00wmY"
        return await ctx.respond(text)

    @commands.slash_command(name="thinbt", description="Gives a guide to set up the ThinBT macro.")
    async def thinbt(self, ctx: discord.ApplicationContext):
        text = """### With Jingle 
* Download [Jingle](https://github.com/DuncanRuns/Jingle/releases). Choose the latest **.jar** file.
* Set a hotkey in **Hotkeys > Add > Resizing - Thin BT (Script)**
* You can change your resolution in **Scripts > Resizing - Customize > Enter your thin bt size**
### With Julti or Autohotkey (not recommended)
- See this message: https://discord.com/channels/83066801105145856/433058639956410383/1364609888126242816 

How to use thin resolution effectively: <https://www.youtube.com/watch?v=OwKqLv2MJrg>"""
        return await ctx.respond(text)

    @commands.slash_command(name="fnlock", description="Explains that you need to turn off FnLock.")
    async def fnlock(self, ctx: discord.ApplicationContext):
        text = """If you need to press Fn-F3 to use F3, and/or some F3 hotkeys (such as F3-B) don't work, toggle Fn-lock on your pc <https://www.thewindowsclub.com/how-to-lock-and-unlock-function-fn-key-in-windows>. If you're on a Lenovo, the setting is in Lenovo Vantage > Device > Input & Accessories > Select F1-F12 function.

If you don't have an F3 key at all, which means you need to press Fn-3 to use F3, type `/rebind` for a tutorial on how to rebind a key to F3."""
        return await ctx.respond(text)

    @commands.slash_command(name="bastions", description="Gives links to bastion routes.")
    async def bastions(self, ctx: discord.ApplicationContext):
        text = """Old general guides:
- [k4yfour's introductory bastion routes](<https://www.youtube.com/playlist?list=PL7Q35RXRsOR-udeKzwlYGJd0ZrvGJ0fwu>)
- [Buzzaboo's guide on finding and routing bastions](<https://www.youtube.com/watch?v=vy1VOQXwnUU>)
More updated guides:
- [Modern bridge routes](<https://docs.google.com/spreadsheets/d/1TYV8RBFb4sV2VRQRZGKPjN-hTPS6bx9UllXKChZyIa0/edit?pli=1&gid=0#gid=0>)
- [Stables triple to gap](<https://www.youtube.com/watch?v=T6VBpOCevs8>)"""
        return await ctx.respond(text)
    
    @commands.slash_command(name="fortress", description="Gives links to guides for finding and routing fortresses.")
    async def fortress(self, ctx: discord.ApplicationContext):
        text = """Basic fortress guide: <https://youtu.be/pmx9LyUvLTk> (find fortress with pieray, blaze bed/tnt, spawnerless and more)
More tips: <https://youtu.be/9LpyDBPC3u4>
Dynamic rd spawnerless (advanced technique): <https://youtu.be/qfwyFWTY3ds>
Fortress binoculars (find fortress if a treasure spawner exists): https://discord.com/channels/83066801105145856/861092932832198687/1247271210409136168"""
        return await ctx.respond(text)
    
    @commands.slash_command(name="fsg", description="Gives a link to the FSG mod and discord server.")
    async def fsg(self, ctx: discord.ApplicationContext):
        text = """FSG Mod: <https://modrinth.com/mod/fsg-mod>
This mod requires Atum, which should be obtained from <https://mods.tildejustin.dev/>.

Join the FSG discord for the latest resources : https://discord.gg/cADcJe8ND8"""
        return await ctx.respond(text)
    
    @commands.slash_command(name="crafting", description="Gives links to search crafting resources.")
    async def crafting(self, ctx: discord.ApplicationContext):
        text = """[Overview of Language Crafting for Minecraft Speedruns](https://docs.google.com/document/d/1jSeciLoEgSwWWCdNk0dKignzxJskxJ5_zeCQmcdGmTg) *(contains: Vietnamese, Ukrainian, Korean, Bosnian, English)*
[Search crafting languages comparison](<https://docs.google.com/spreadsheets/d/1NM5U84PjTBA6oMDSyFgveVVWcP7i0aCIFqvQCNUotYE/edit#gid=1472263979>)
[Remapping keys explanation](<https://docs.google.com/document/d/1V2Uk4wDZknr6U9KbYJEc0JRYO7OWmhtmNIK0swTzXxs>)

More search crafting languages:
[Norwegian](<https://docs.google.com/document/u/0/d/1p3i64xH4C63d3QO7U6VXXe0JZIj-zHtrv1ZC_BKaCwk>), [Franggian](<https://docs.google.com/document/d/1_GvCg7kQP9Ls6yFX_b3eF4UqlPgSxbPjeQsWMr2QQGA>), [French Canadian](<https://docs.google.com/document/d/e/2PACX-1vRZ6v_jah6lNFUeT3ZOKlDhtooF8HZfJNS0KpeNXwHlFayjYcx_GTOIPSijOhm6BSLxPvCrZfRNq5qt/pub>), [Danish](<https://docs.google.com/spreadsheets/u/0/d/1btQ3Tx8gCvdUD_x71lEm0j7ZUE72GocsE0urh1xdIKU/htmlview#gid=0>), [Maltese](<https://docs.google.com/document/d/1Hm2BE0soChqjv499DElXYM_r30-m5nfr-TIaCWc3vTk>), [Pirate Speak](<https://docs.google.com/document/d/1PTwAu86MCue7KJah6QWNhSdE4pL7r-4cuuO6OdUhbS8>), [Vietnamese V2](<https://docs.google.com/document/d/1AKqzwW1km12fvKfx3niuORhD8RRncRU71pUBZA-apRA>)"""
        return await ctx.respond(text)

    @commands.slash_command(name="endfight", description="Gives a link to the end fight tutorial.")
    async def endfight(self, ctx: discord.ApplicationContext):
        text = "https://youtu.be/JrCZ6E0LKko"
        return await ctx.respond(text)

    @commands.slash_command(name="eyelineup", description="Gives a guide to lining up the crosshair on the ender eye for measuring.")
    async def eyelineup(self, ctx: discord.ApplicationContext):
        text = """The right edge of the crosshair should line up with the left edge of the eye's middle pixel, as shown in the image below[:](https://cdn.discordapp.com/attachments/433058639956410383/1122565681515352154/image.png)"""
        return await ctx.respond(text)

    @commands.slash_command(name="eyewiggle", description="Links a page explaining eye wiggle.")
    async def eyewiggle(self, ctx: discord.ApplicationContext):
        text = """https://frontcage.com/t/what-to-do-about-eye-wiggle/14"""
        return await ctx.respond(text)

    @commands.slash_command(name="gamma", description="Gives a guide for increasing brightness past 100%.")
    async def gamma(self, ctx: discord.ApplicationContext):
        text = """It is legal to set gamma to up to 5.0.
If you're using Speedrunning Sodium or Planifolia, you can adjust the brightness level up to 500% in-game via `Options > Video Settings` in the title screen.
Otherwise, open your `options.txt` file in your Minecraft directory and change the value next to `gamma` to `5.0`, or do `!!setup` for a guide on setting up mods."""
        return await ctx.respond(text)

    @commands.slash_command(name="ghostbucket", description="Gives an explanation for ghost buckets.")
    async def ghostbucket(self, ctx: discord.ApplicationContext):
        text = "Ghost buckets occur if your crosshair moves from one block to another as you right click with a bucket. Keep your mouse still while you right click to prevent them from occurring."
        return await ctx.respond(text)

    @commands.slash_command(name="lazychunks", description="Gives an explanation of lazy chunks for pie-ray.")
    async def lazychunks(self, ctx: discord.ApplicationContext):
        text = """Spawners up to 3 chunks outside your render distance remain loaded and will still show up on the pie chart. This is why just dropping your render distance by 1 won't unload the spawner. You have to drop it by at least 4 to unload it.

*Example: If the spawner loads in at 15 chunks, you should decrease your render distance to 11 (press Shift-F3-F four times), then increase it to 14 (press F3-F three times). Reopen the pie chart and the spawner should be gone.*"""
        return await ctx.respond(text)

    @commands.slash_command(name="mpk", description="Gives a link to MiniPracticeKit.")
    async def mpk(self, ctx: discord.ApplicationContext):
        text = """MiniPracticeKit:
<https://github.com/Knawk/mc-MiniPracticeKit>
https://discord.com/channels/83066801105145856/405839885509984256/1146302423095332915

MiniPracticeKit Editor (for customizing setup):
https://qmaxxen.github.io/MiniPracticeKit-Editor/"""
        return await ctx.respond(text)

    @commands.slash_command(name="onecycle", description="Gives a link to a onecycle tutorial.")
    async def onecycle(self, ctx: discord.ApplicationContext):
        text = "https://youtu.be/JaVyuTyDxxs"
        return await ctx.respond(text)

    @commands.slash_command(name="overlay", description="Gives a guide to changing your eye measuring overlay.")
    async def overlay(self, ctx: discord.ApplicationContext):
        text = """# Changing measuring overlay
* Use [this website](https://qmaxxen.github.io/overlay-gen/) to generate your own overlay.
* OBS canvas width/height are usually the same as your monitors width/height
* Download the image

*Do one of the following parts depending on which type of projector you use:*
### For OBS
* Drag the image into your Jingle Mag scene
* Ctrl + F to maximize it, alternatively drag the corners
* Drag it below the Jingle Mag Cover
* Delete the old overlay
* Restart Jingle
### For Jingle (EyeSee plugin)
* Open Jingle ➔ Open Jingle Folder ➔ Delete "eyesee_overlay.png"
* Drag your new overlay into the folder and rename it to "eyesee_overlay.png"
* Restart Jingle"""
        return await ctx.respond(text)

    @commands.slash_command(name="portals", description="Gives a link to the portals spreadsheet.")
    async def portals(self, ctx: discord.ApplicationContext):
        text = """Common magma ravine portals:
<https://www.youtube.com/watch?v=mLuxNQZshy0>

Other portals:
https://docs.google.com/spreadsheets/d/1VU6IZpyhr-3tMXC5GG4ryuqrbmQkvCKE_1nJm2eym4c"""
        return await ctx.respond(text)

    @commands.slash_command(name="portalheight", description="Links the 2nd portal y height distribution graph.")
    async def portalheight(self, ctx: discord.ApplicationContext):
        text = "https://cdn.discordapp.com/attachments/727673359860760627/1110309490324164658/image.png"
        return await ctx.respond(text)

    @commands.slash_command(name="preemptive", description="Gives links to preemptive resources.")
    async def preemptive(self, ctx: discord.ApplicationContext):
        text = """Video tutorial by meebie: https://youtu.be/yF4kcBk3lKo
Original video explanation/tutorial by addlama: <https://youtu.be/2dWq2wXy43M>
Detailed document by Mimi: <https://docs.google.com/document/d/1Xnmki5jOwuiwVnyv1b3VJLpiDWfNixgKW3zQowmpsYo/edit>"""
        return await ctx.respond(text)

    @commands.slash_command(name="zerocycle", description="Gives links to zero cycle resources.")
    async def zerocycle(self, ctx: discord.ApplicationContext):
        text = """[Zero Cycle tutorial](https://youtu.be/PB5UQB13VHc)
[Couriway Metafy Guide End section (requires account)](<https://metafy.gg/guides/view/ultimate-minecraft-speedrun-guide-cIzfjeTmwOm/chapter-6-the-end-I88hY9AXfrU>)
[Zero practice map](<https://github.com/Mescht/Zero-Practice/releases/latest>)

[Zero Cycle music video by Dylqn & Fulham](<https://youtu.be/iuti2oacMNI>)"""
        return await ctx.respond(text)

    @commands.slash_command(name="extraoptions", description="Gives a link to Extra Options mod and an explanation of SRC rules regarding it.")
    async def extraoptions(self, ctx: discord.ApplicationContext):
        text = """⚠️ **__Warning!__** ⚠️ 
This mod is now configurable through Options > Book and Quill > ExtraOptions, __**not**__ through accessibility settings.
This mod is allowed, but may result in your run being **rejected** if it is used to gain an advantage that was otherwise unavailable, such as the examples listed here: https://discord.com/channels/83066801105145856/765767120008773662/1251662769518936064 . If you are unsure something may be deemed as an abuse of unintended behaviour, you may ask by opening a thread in <#728007511386488872> .
Download **(read the above warning)**: 
||<https://mods.tildejustin.dev/>||
This mod allows you to adjust FOV and distortion effects.
<:MCSRRanked:1310948334604783627> If you're playing Ranked, this mod is already bundled in the Ranked mod and is therefore not needed."""
        return await ctx.respond(text)

    @commands.slash_command(name="seedwave", description="Gives the current Seedwave level.")
    async def seedwave(self, ctx: discord.ApplicationContext):
        url = "https://seedwave.vercel.app/api/seedwave"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = json.loads(response.text)
            text = f"{data['seedwave']}"
            if data["isBloodseed"]: text += " 🩸"
        except Exception as e:
            error = "".join(traceback.format_exception(e))
            text = f"```\n{error}\n```\n<@695658634436411404> :bug:"
        return await ctx.respond(text.strip())
    
    @commands.slash_command(name="help", description="Gives a guide to using the bot.")
    async def help(self, ctx: discord.ApplicationContext):
        text = """- **Log Analysis**: Send a message containing a Minecraft log link from pastee.dev or mclo.gs, or upload a log file directly in the chat. The bot will analyze the log and provide feedback automatically.
- **/tags**: Use this command to get a list of all available tags related to MCSR strategies, guides, and more.
- **Need Help?**: If you're still unsure after the bot's response, please ask in the appropriate help channel.

If you have any questions or suggestions regarding the bot, feel free to ping or dm `maskers`.
Source code available on [GitHub](<https://github.com/maskersss/background-pingu-v2>)."""
        return await ctx.respond(text)
    
    @commands.slash_command(name="info", description="Gives a guide to using the bot.")
    async def info(self, ctx: discord.ApplicationContext):
        return await self.help(ctx)

    # @commands.slash_command(name="", description="")
    # async def (self, ctx: discord.ApplicationContext):
    #     text = ""
    #     return await ctx.respond(text)

    @commands.slash_command(name="tags", description="Lists all possible tags.")
    async def tags(self, ctx: discord.ApplicationContext):
        try:
            with open("BackgroundPingu/bot/cogs/tips.py") as file:
                text = file.read()
            tags = re.findall(r"name=\"([^\"]*)\"", text)

            # Separate tags into groups based on first letter
            groups = {}
            for tag in tags:
                if len(tag) == 0: continue
                first_letter = tag[0].upper() if tag[0].isalpha() else "#"
                groups.setdefault(first_letter, []).append(tag)

            # Sort each group
            for group in groups.values():
                group.sort()

            # Format and print the groups
            text = ""
            for letter, group in sorted(groups.items()):
                if letter.isalpha():
                    text += f"[{letter}] {', '.join(group)}\n"
                else:
                    text += f"[#] {', '.join(group)}\n"

            text = f"```{text}```"
            return await ctx.respond(text)
        except Exception as e:
            error = "".join(traceback.format_exception(e))
            text = f"```\n{error}\n```\n<@695658634436411404> :bug:"
            return await ctx.respond(text)

def setup(bot: BackgroundPingu):
    bot.add_cog(Tips(bot))
