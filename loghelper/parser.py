import re, requests, enum
from packaging import version
from cached_property import cached_property
from .config import *

class OperatingSystem(enum.IntEnum):
    WINDOWS = enum.auto()
    LINUX = enum.auto()
    MACOS = enum.auto()

class LogType(enum.Enum):
    FULL_LOG = "full log"
    THREAD_DUMP = "thread dump"
    CRASH_REPORT = "crash-report"
    HS_ERR_PID_LOG = "hs_err_pid log"
    LATEST_LOG = "latest.log"
    LAUNCHER_LOG = "launcher log"

class Launcher(enum.Enum):
    OFFICIAL_LAUNCHER = "Official Launcher"
    MULTIMC = "MultiMC"
    PRISM = "Prism"
    MODRINTH = "Modrinth App"
    ATLAUNCHER = "ATLauncher"
    TL = "TL"

class ModLoader(enum.Enum):
    FABRIC = "Fabric"
    QUILT = "Quilt"
    FORGE = "Forge"
    VANILLA = "Vanilla"

class Log:
    def __init__(self, content: str) -> None:
        self.leaked_pc_username = False
        pattern = r"(/|\\|//|\\\\)(Users|home)(/|\\|//|\\\\)([^/\\]+)(/|\\|//|\\\\)"
        for match in re.findall(pattern, content):
            if match and match[3].lower() not in ["user", "admin", "********"]:
                self.leaked_pc_username = True
                break
        match = None
        content = re.sub(pattern, r"\1\2\3********\5", content)

        pattern = r"\"USERNAME=([^/\\]+)\"" # from mmc/prism logs
        for match in re.findall(pattern, content):
            if match and match[3].lower() not in ["user", "admin", "********"]:
                self.leaked_pc_username = True
                break
        match = None
        content = re.sub(pattern, r"\"USERNAME=********\"", content)

        # just replacing pc_username with "" is a bad idea
        # for instance, if it's "Alex", it could also replace it in the mod "Alex Caves", which would leak it
        
        self.lines = content.count("\n") + 1
        if self.lines > MAX_STARTING_LOG_LINES + MAX_ENDING_LOG_LINES:
            lines = content.splitlines()
            content = (
                "\n".join(lines[:MAX_STARTING_LOG_LINES])
                + "\n" * 10
                + "--- Log truncated: Middle portion omitted ---"
                + "\n" * 10
                + "\n".join(lines[-MAX_ENDING_LOG_LINES:])
            )

        pattern = r"Session ID is token:.{50,}?\n"
        if re.search(pattern, content) is not None:
            replacement = "Session ID is (redacted))\n"
            content = re.sub(pattern, replacement, content)
            self.leaked_session_id = True
        else: self.leaked_session_id = False

        self._content = content
        self._lower_content = self._content.lower()
    
    @staticmethod
    def from_link(link: str):
        paste_ee_match = re.search(r"https://(?:api\.)?(?:pastee\.dev|paste\.ee)/(?:p/|d/)([a-zA-Z0-9]+)", link)
        mclogs_match = re.search(r"https://mclo\.gs/(\w+)", link)
        if paste_ee_match: link = f"https://pastee.dev/d/{paste_ee_match.group(1)}/0"
        elif mclogs_match: link = f"https://api.mclo.gs/1/raw/{mclogs_match.group(1)}"
        elif not ".txt" in link and not ".log" in link and not ".tdump" in link and not ".json" in link: return None
        try:
            res = requests.get(link, timeout=5)
        except requests.exceptions.Timeout:
            return Log("__PINGU__DOWNLOAD_ERROR__timeout__")
        if res.status_code == 200:
            return Log(res.text.replace("\r", ""))
        elif res.status_code != 404:
            return Log(f"__PINGU__DOWNLOAD_ERROR__{res.status_code}__")
        return None

    @cached_property
    def mods(self) -> list[str]:
        pattern = re.compile(r"\[✔️\]\s+([^\[\]]+\.jar)")
        mods = pattern.findall(self._content)
        if len(mods) > 0: return mods

        pattern = re.compile(r"\[✔\]\s+([^\[\]\n]+)")
        mods = [mod.rstrip("\n").replace(" ", "+") + ".jar" for mod in pattern.findall(self._content)]
        if len(mods) > 0: return mods

        pattern = re.compile(r"\[✔️\]\s+([^\[\]\n]+)")
        mods = [mod + ".jar" for mod in pattern.findall(self._content)]
        return mods

    
    @cached_property
    def fabric_mods(self) -> list[str]:
        if self.type == LogType.THREAD_DUMP: return []

        excluded_prefixes = [
            "java ",
            "fabricloader ",
            "minecraft ",
        ]
        excluded_patterns = [
            r" via ",
            r"<0x.*>",
        ]

        pattern = re.compile(r"\t- ([^\n]+)", re.DOTALL)

        fabric_mods = []
        for mod in pattern.findall(self._content):
            mod = mod.replace("_", "-")
            if (not any(mod.startswith(prefix) for prefix in excluded_prefixes)
                and not any(re.search(pattern, mod) for pattern in excluded_patterns)
            ):
                fabric_mods.append(mod)
        
        return fabric_mods
    
    @cached_property
    def whatever_mods(self) -> list[str]:
        return self.mods if len(self.mods) > 0 else self.fabric_mods

    @cached_property
    def java_version(self) -> str:
        version_match = re.compile(r"\nJava is version (\S+),").search(self._content) # mmc/prism logs
        if not version_match is None:
            return version_match.group(1)
        
        version_match = re.compile(r"\n\tJava Version: (\S+),").search(self._content) # crash reports
        if not version_match is None:
            return version_match.group(1)
        
        return None
    
    @cached_property
    def major_java_version(self) -> int:
        if not self.java_version is None:
            parts = self.java_version.split(".")
            try:
                if not parts[0] == "1": return int(parts[0])
                if len(parts) > 1: return int(parts[1])
            except ValueError: pass
        
        match = re.search(r"\s*- java (\d+)", self._content)
        if not match is None:
            return int(match.group(1))

        return None
    
    @cached_property
    def minecraft_folder(self) -> str:
        # mmc/prism logs
        match = re.compile(r"Minecraft folder is:\n(.*)\n").search(self._content)
        if not match is None: return match.group(1).strip()

        # seedqueue logging
        if not self.java_arguments is None:
            match = re.compile(r"-Djava.library.path=(.*)$").search(self.java_arguments)
            if not match is None:
                return match.group(1).strip().replace("/natives", "/.minecraft")

        return None
    
    @cached_property
    def operating_system(self) -> OperatingSystem:
        if not self.minecraft_folder is None:
            if self.minecraft_folder.startswith("/"):
                if len(self.minecraft_folder) > 1 and self.minecraft_folder[1].isupper():
                    return OperatingSystem.MACOS
                return OperatingSystem.LINUX
            return OperatingSystem.WINDOWS
        
        if self.has_content("Operating System: Windows"): return OperatingSystem.WINDOWS
        if self.has_content("Operating System: Mac OS"): return OperatingSystem.MACOS
        if self.has_content("Operating System: Linux"): return OperatingSystem.LINUX

        if any(self.has_content(windows) for windows in [
            "-natives-windows.jar",
            "/AppData/",
        ]): return OperatingSystem.WINDOWS

        if any(self.has_content(macos) for macos in [
            "/Applications/",
            "/Library/Application Support/",
        ]): return OperatingSystem.MACOS

        if any(self.has_content(linux) for linux in [
            "/.local/share/",
            "/.var/app/",
        ]): return OperatingSystem.LINUX

        return None

    @cached_property
    def is_intel_mac(self) -> bool:
        if not self.operating_system in [OperatingSystem.MACOS, None]: return False

        if any(self.has_content(intel) for intel in [
            ": Intel",
        ]): return True

        return False

    @cached_property
    def is_arm_mac(self) -> bool:
        if not self.operating_system in [OperatingSystem.MACOS, None]: return False

        if any(self.has_content(arm) for arm in [
            "Mac OS X (aarch64)",
        ]): return True

        return False
    
    @cached_property
    def minecraft_version(self) -> str:
        if self.type == LogType.LAUNCHER_LOG: return None

        for pattern in [
            r"/com/mojang/minecraft/(\S+?)/",
            r"Loading Minecraft (\S+) with Fabric Loader",
            r"Minecraft Version ID: (\S+)",
            r"Minecraft Version: (\S+)",
            r"\n\t- minecraft (\S+)\n",
            r"/net/minecraftforge/forge/(\S+?)-",
            r"--version, (\S+),",
            r"minecraft server version (\S+)\n",
        ]:
            match = re.compile(pattern).search(self._content)
            if not match is None:
                return match.group(1)
        
        return None
    
    @cached_property
    def parsed_mc_version(self) -> version.Version:
        if self.minecraft_version is None: return None
        
        try:
            return version.parse(self.minecraft_version)
        except version.InvalidVersion: return None
    
    @cached_property
    def loader_mc_version(self) -> str:
        for pattern in [
            r"libraries/net/fabricmc/intermediary/(\S+)/intermediary-",
            r"--fml.mcVersion (\S+)",
        ]:
            match = re.compile(pattern).search(self._content)
            if not match is None:
                return match.group(1)
        
        return None
    
    @cached_property
    def short_version(self) -> str:
        if not self.minecraft_version is None:
            return self.minecraft_version[:4]
        return None
    
    @cached_property
    def fabric_version(self) -> version.Version:
        for pattern in [
            r"Loading Minecraft \S+ with Fabric Loader (\S+)",
            r"libraries/net/fabricmc/fabric-loader/\S+/fabric-loader-(\S+).jar",
        ]:
            match = re.compile(pattern).search(self._content)
            try:
                if not match is None: return version.parse(match.group(1))
            except version.InvalidVersion: pass

        return None
    
    @cached_property
    def launcher(self) -> Launcher:
        for multimc_name in [
            "multimc",
            "ultimmc",
        ]:
            if self.has_pattern(rf"^{multimc_name}"):
                return Launcher.MULTIMC
            if any(self.has_content(multimc) for multimc in [
                f"org.{multimc_name}",
                f"/{multimc_name}",
                f"\\{multimc_name}",
            ]):
                return Launcher.MULTIMC
        
        for prism_name in [
            "prism",
            "polymc",
            "pollymc",
        ]:
            if self.has_pattern(rf"^{prism_name}"):
                return Launcher.PRISM
            if any(self.has_content(prism) for prism in [
                f"org.{prism_name}",
                f"/{prism_name}",
                f"\\{prism_name}",
            ]):
                return Launcher.PRISM
        
        if any(self.has_content(modrinth) for modrinth in [
            r"com.modrinth.theseus",
            r"ModrinthApp",
            r"{MINECRAFT_USERNAME}",
        ]):
            return Launcher.MODRINTH
        
        if self.has_content(".tlauncher"):
            return Launcher.TL
        
        if (self.has_content("\\AppData\\Roaming\\.minecraft")
            or self.has_content("/AppData/Roaming/.minecraft")
            or self.has_pattern(r"-Xmx(\d+)G")
        ):
            return Launcher.OFFICIAL_LAUNCHER
    
        if any(self.has_content(atlauncher) for atlauncher in [
            "Made By Bob*",
            "/ATLauncher/",
        ]):
            return Launcher.ATLAUNCHER
        
        if self.exitcode and self.has_content("Please note that usually neither the exit code"):
            return Launcher.MULTIMC
        
        if self.max_allocated == 1024:
            return Launcher.MULTIMC

        return None

    @cached_property
    def type(self) -> LogType:
        if any([self.has_pattern(rf"^{launcher}") for launcher in [
            "multimc",
            "ultimmc",
            "prism",
            "polymc",
            "pollymc",
        ]]):
            return LogType.FULL_LOG

        if any(self.has_content(thread_dump) for thread_dump in [
            "-- Thread Dump --",
            "\nFull thread dump"
        ]):
            return LogType.THREAD_DUMP

        if self._content.startswith("---- Minecraft Crash Report ----"):
            return LogType.CRASH_REPORT
        
        if self.has_content("---------------  T H R E A D  ---------------"):
            return LogType.HS_ERR_PID_LOG

        if self.has_content(" D | "):
            return LogType.LAUNCHER_LOG

        if self._content.startswith("["):
            return LogType.LATEST_LOG

        return None

    @cached_property
    def is_multimc_or_fork(self) -> bool:
        return self.launcher in [Launcher.MULTIMC, Launcher.PRISM]

    @cached_property
    def is_prism(self) -> bool:
        return self.launcher == Launcher.PRISM

    @cached_property
    def edit_instance(self) -> str:
        return "" if self.is_prism else " Instance"
    
    @cached_property
    def mod_loader(self) -> ModLoader:
        if self.type == LogType.LAUNCHER_LOG: return None
        
        match = re.compile(r"Main Class:\n(.*)\n").search(self._content)
        if not match is None:
            line = match.group(1)
            for loader in ModLoader:
                if loader.value.lower() in line.lower():
                    return loader
            if "net.minecraft.launchwrapper.Launch" in line:
                return ModLoader.FORGE
            if "net.minecraft.client.main.Main" in line:
                return ModLoader.VANILLA
        
        if self.has_pattern(r"Loading Minecraft \S+ with Fabric Loader"):
            return ModLoader.FABRIC
        
        match = re.search(r"Client brand changed to '(\S+)'", self._content)
        if not match is None:
            for loader in ModLoader:
                if loader.value.lower() in match.group(1).lower():
                    return loader
        
        if self.has_content("client brand is untouched"):
            return ModLoader.VANILLA

        if any(self.has_content(content) for content in [
            "\nhttps://maven.minecraftforge.net",
            "\nhttps://maven.neoforged.net",
            "net.minecraftforge.",
            "--fml.forgeVersion, ",
        ]):
            return ModLoader.FORGE
        
        return None
    
    @cached_property
    def java_arguments(self) -> str:
        # multimc/prism logs
        match = re.compile(r"Java Arguments:\n(.*?)\n", re.DOTALL).search(self._content)
        if not match is None:
            return match.group(1)
        
        # crash reports
        match = re.compile(r"JVM Flags: \S+ total; ([^\n]*)", re.DOTALL).search(self._content)
        if not match is None:
            return match.group(1)
        
        # seedqueue logging
        match = re.compile(r"JVM Arguments: ([^\n]*)", re.DOTALL).search(self._content)
        if not match is None:
            return match.group(1)
        
        return None

    @cached_property
    def max_allocated(self) -> int:
        if not self.java_arguments is None:
            match = re.compile(r"-Xmx(\d+)m").search(self.java_arguments)
            try:
                if not match is None: return int(match.group(1))
            except ValueError: pass
            
            match = re.compile(r"-Xmx(\d+)M").search(self.java_arguments)
            try:
                if not match is None: return int(match.group(1))
            except ValueError: pass
            
            match = re.compile(r"-Xmx(\d+)G").search(self.java_arguments)
            try:
                if not match is None: return int(match.group(1))*1024
            except ValueError: pass
        return None
    
    @cached_property
    def recommended_min_allocated(self) -> tuple[int, int, int]:
        min_limit_0, min_limit_1, min_limit_2 = 0, 0, 0

        if self.is_newer_than("1.18"):
            min_limit_0 += 5000
            min_limit_1 += 3000
            min_limit_2 += 1300
        elif self.is_newer_than("1.14"):
            min_limit_0 += 2800
            min_limit_1 += 1800
            min_limit_2 += 1200
        elif self.is_newer_than("1.1"):
            min_limit_0 += 2000
            min_limit_1 += 1500
            min_limit_2 += 800
        else:
            min_limit_0 += 5000
            min_limit_1 += 1500
            min_limit_2 += 1000
        
        mod_cnt = len(self.whatever_mods)
        if self.mod_loader == ModLoader.FORGE:
            min_limit_0 += min(mod_cnt * 100, 5000)
            min_limit_1 += min(mod_cnt * 100, 1000)
            min_limit_2 += min(mod_cnt * 50, 200)
        
        if self.is_ssg_log:
            min_limit_0 *= 0.7
            min_limit_1 *= 0.7
            min_limit_2 *= 0.7
        
        if self.has_java_argument("shenandoah"):
            min_limit_0 *= 0.7
            min_limit_1 *= 0.7
            min_limit_2 *= 0.7
        
        if self.has_java_argument("zgc"):
            min_limit_0 *= 1.7
            min_limit_1 *= 1.3
            min_limit_2 *= 1.3
        
        if self.is_ranked_log:
            min_limit_0 += 1500
            min_limit_1 += 700
            min_limit_2 += 300
        
        return (min_limit_0, min_limit_1, min_limit_2)
    
    @cached_property
    def recommended_max_allocated(self) -> tuple[int, int, int]:
        max_limit_0, max_limit_1, max_limit_2 = 0, 0, 0

        if self.is_newer_than("1.18"):
            max_limit_0 += 15000
            max_limit_1 += 8000
            max_limit_2 += 6000
        elif self.is_newer_than("1.14"):
            max_limit_0 += 10000
            max_limit_1 += 4500
            max_limit_2 += 3100
        elif self.is_newer_than("1.1"):
            max_limit_0 += 8000
            max_limit_1 += 3200
            max_limit_2 += 2200
        else:
            max_limit_0 += 12000
            max_limit_1 += 7000
            max_limit_2 += 5500
        
        mod_cnt = len(self.whatever_mods)
        if self.mod_loader == ModLoader.FORGE:
            max_limit_0 += min(mod_cnt * 400, 4000)
            max_limit_1 += max(min(mod_cnt * 200, 1500), 9000)
            max_limit_2 += max(min(mod_cnt * 100, 800), 8000)
        
        if self.is_ssg_log:
            max_limit_0 *= 0.8
            max_limit_1 *= 0.8
            max_limit_2 *= 0.8
        
        if self.has_java_argument("shenandoah"):
            max_limit_0 *= 0.7
            max_limit_1 *= 0.7
            max_limit_2 *= 0.7
        
        if self.has_java_argument("zgc"):
            max_limit_0 *= 1.3
            max_limit_1 *= 1.3
            max_limit_2 *= 1.3
        
        if self.is_ranked_log:
            max_limit_0 += 10000
            max_limit_1 += 7000
            max_limit_2 += 4000
        
        if self.is_seedqueue_log:
            max_limit_0, max_limit_1 = None, None
        
        return (max_limit_0, max_limit_1, max_limit_2)

    @cached_property
    def seedqueue_ram(self) -> tuple[int, int]:
        min_ram, max_ram = 170, 250

        if self.has_java_argument("shenandoah"):
            min_ram *= 0.8
            max_ram *= 0.8
        
        if self.has_java_argument("zgc"):
            min_ram *= 1.2
            max_ram *= 1.2

        return (min_ram, max_ram)

    @cached_property
    def processors(self) -> int:
        pattern = re.compile(r"Available Processors: ([0-9]+)\n")
        match = pattern.search(self._content)
        if not match is None:
            return int(match.group(1))
        return None

    @cached_property
    def pc_ram(self) -> int:
        pattern = re.compile(r"Total Physical Memory \(MB\): ([0-9]+)\n")
        match = pattern.search(self._content)
        if not match is None:
            return int(match.group(1))
        return None

    @cached_property
    def ram_guide(self) -> tuple[str, str, str, str]:
        if self.is_seedqueue_log:
            sq_min, sq_max = self.seedqueue_ram
            sq_min = int(round(sq_min, -1))
            sq_max = int(round(sq_max, -1))
            seedqueue = f" + `{sq_min}-{sq_max}` MB per `Max Queued Seed`"
        else:
            seedqueue = ""
        
        min_recomm = self.recommended_min_allocated[1]
        max_recomm = self.recommended_max_allocated[2]

        if min_recomm is None or max_recomm is None:
            if min_recomm is None: min_recomm = "?"
            else: min_recomm = str(int(round(min_recomm, -2)))
            if max_recomm is None: max_recomm = "?"
            else: max_recomm = str(int(round(max_recomm, -2)))
        else:
            diff = max_recomm - min_recomm
            min_recomm = str(int(round(min_recomm + diff / 7, -2)))
            max_recomm = str(int(round(max_recomm - diff / 7, -2)))

        if self.is_multimc_or_fork:
            return (
                "allocate_ram_guide_mmc",
                min_recomm,
                max_recomm,
                seedqueue,
                "Prism" if self.is_prism else "MultiMC",
            )
        else:
            return ("allocate_ram_guide", min_recomm, max_recomm, seedqueue)

    @cached_property
    def setup_guide(self) -> str:
        if self.operating_system == OperatingSystem.MACOS: return "mac_setup_guide"
        return "k4_setup_guide"

    @cached_property
    def fabric_guide(self) -> str:
        if self.launcher in [Launcher.OFFICIAL_LAUNCHER, Launcher.MODRINTH]: return None
        if self.is_newer_than("1.0") and not self.is_newer_than("1.14"): return "legacy_fabric_guide"
        if self.is_prism: return "fabric_guide_prism"
        return "fabric_guide_mmc"

    @cached_property
    def java_update_guide(self) -> str:
        if self.launcher == Launcher.OFFICIAL_LAUNCHER:
            return self.setup_guide
        
        if self.is_prism:
            return "java_update_guide_prism"

        if self.operating_system == OperatingSystem.LINUX:
            return "java_update_guide_linux"

        if self.launcher in [Launcher.MODRINTH, Launcher.ATLAUNCHER]:
            return None

        return "java_update_guide"
    
    @cached_property
    def libraries(self) -> str:
        pattern = r"\nLibraries:\n(.*?)\nNative libraries:\n"
        match = re.search(pattern, self._content, re.DOTALL)
        if not match is None:
            return match.group(1)
        
        return None
    
    @cached_property
    def stacktrace(self) -> str:
        log = self._content
        ignored_patterns = [
            r"(?s)---- Minecraft Crash Report ----.*?This is just a prompt for computer specs to be printed",
            r"(?s)WARNING: coremods are present:.*?Contact their authors BEFORE contacting forge"
        ]
        for pattern in ignored_patterns:
            log = re.sub(pattern, "", log)
        
        crash_patterns = [
            r"---- Minecraft Crash Report ----.*A detailed walkthrough of the error",
            r"-- Crash --.*-- Mods --",
            r"Failed to start Minecraft:.*",
            r"Unable to launch\n.*",
            r"Exception caught from launcher\n.*",
            r"Reported exception thrown!\n.*",
            r"Minecraft has crashed!.*",
            r"A mod crashed on startup!\n.*",
            r"Unreported exception thrown!\n.*",
            r"Encountered an unexpected exception\n.*",
            r"Unhandled game exception\n.*",
            r"Failed to create window: \n.*",
        ]
        for crash_pattern in crash_patterns:
            match = re.search(crash_pattern, log, re.DOTALL)
            if not match is None:
                return match.group().lower().replace("fast_reset", "fastreset").replace("knot//", "")
        
        return None
    
    @cached_property
    def exitcode(self) -> int:
        pattern = r"Process (crashed|exited) with (exit)? ?code (-?\d+)"
        match = re.search(pattern, self._content, re.DOTALL)
        if not match is None:
            try: return int(match.group(3))
            except ValueError: pass
        
        for exit_code in [-1073741819, -1073740791, -805306369, -1073740771]:
            if self.has_content(f"{exit_code}"): return exit_code

        return None

    @cached_property
    def is_ssg_log(self) -> bool:
        for ssg_mod in [
            "setspawn",
            "chunkcacher"
        ]:
            if self.has_mod(ssg_mod): return True
        
        return False

    @cached_property
    def is_ranked_log(self) -> bool:
        for ranked_mod in [
            "mcsrranked"
        ]:
            if self.has_mod(ranked_mod): return True
        
        if self.has_content("com.mcsrranked"): return True
        
        return False

    @cached_property
    def is_seedqueue_log(self) -> bool:
        if self.has_mod("seedqueue"): return True
        
        return False
    
    @cached_property
    def is_log(self) -> bool:
        if self.type == LogType.LAUNCHER_LOG: return True
        if self.minecraft_version is None: return False
        return True

    @cached_property
    def modcheck_v1_warning(self) -> str:
        if any(self.has_mod(old_mod) for old_mod in [
            "fast-reset-1",
        ]):
            return "modcheck_v1_warning"
        
        return None
    
    @cached_property
    def recommended_mods(self) -> list[str]:
        mods = []

        if self.operating_system == OperatingSystem.MACOS:
            mods.append("retino")

        if not self.is_newer_than("1.15"): return mods
        
        mods.append("sodium")
        if not self.is_newer_than("1.20"): mods.append("starlight")
        if not self.is_ranked_log: mods.append("speedrunapi")
        mods.append("lithium")

        if self.launcher != Launcher.OFFICIAL_LAUNCHER and not self.is_newer_than("1.17"):
            mods.append("voyager")
        
        if self.is_newer_than("1.17") and not self.is_ssg_log:
            mods.append("planifolia")

        if self.is_ssg_log:
            mods += [
                "seedqueue",
                "setspawn",
                "chunkcacher",
                "speedrunigt",
                "antiresourcereload",
            ]
        elif not self.has_mod("mcsrranked") and not self.has_mod("peepopractice"):
            mods += [
                "antigone",
                "speedrunigt",
                "lazystronghold",
                "antiresourcereload",
                "fast-reset",
                "atum",
                "state-output",
            ]
            if not self.has_mod("pogloot"):
                mods.append("worldpreview")
            if all(not self.has_mod(seedqueue_incompatible) for seedqueue_incompatible in [
                "fsg",
                "beachfilter",
                "pogloot",
            ]):
                mods.append("seedqueue")
            if not self.minecraft_version == "1.16.1":
                mods.append("sleepbackground")
        
        return mods

    def get_java_arg(self, arg: str) -> str:
        if self.java_arguments is None: return arg
        for java_arg in self.java_arguments.split(" "):
            if arg.lower() in java_arg.lower(): return java_arg.strip().strip('[],')
        return arg
    
    def is_newer_than(self, compared_version: str) -> bool:
        if self.parsed_mc_version is None: return False
        return self.parsed_mc_version >= version.parse(compared_version)
    
    def has_content(self, content: str) -> bool:
        return content.lower() in self._lower_content
    
    def has_content_in_stacktrace(self, content: str) -> bool:
        if self.stacktrace is None: return False
        return content.lower().replace("_","") in self.stacktrace.lower().replace("_","")

    def has_pattern(self, pattern: str) -> bool:
        return bool(re.compile(pattern, re.IGNORECASE).search(self._lower_content))
    
    def has_mod(self, mod_name: str) -> bool:
        mod_name = mod_name.lower().replace(" ", "").replace("-", "").replace("+", "")
        for mod in self.whatever_mods:
            if mod_name in mod.lower().replace(" ", "").replace("-", "").replace("+", ""):
                return True
        return False
    
    def has_normal_mod(self, mod_name: str) -> bool:
        for mod in self.mods:
            if mod_name.lower() in mod.lower():
                return True
        return False
    
    def has_java_argument(self, argument: str) -> bool:
        if self.java_arguments is None: return False
        return argument.lower() in self.java_arguments.lower()
    
    def has_library(self, content: str) -> bool:
        if self.libraries is None: return False
        return content.lower() in self.libraries.lower()
    
    def upload(self) -> tuple[bool, str]:
        api_url = "https://api.mclo.gs/1/log"
        payload = {
            "content": self._content
        }
        response = requests.post(api_url, data=payload)
        if response.status_code == 200:
            match = re.search(r"/(Users|home)/([^/]+)/", self._content)
            return (
                match and match.group(2).lower() not in ["user", "admin", "********"],
                response.json().get("url")
            )
    
    def __str__(self) -> str:
        return f"""
mods={self.mods}
fabric_mods={self.fabric_mods}
java_version={self.java_version}
major_java_version={self.major_java_version}
minecraft_folder={self.minecraft_folder}
operating_system={self.operating_system}
is_intel_mac={self.is_intel_mac}
is_arm_mac={self.is_arm_mac}
minecraft_version={self.minecraft_version}
parsed_mc_version={self.parsed_mc_version}
loader_mc_version={self.loader_mc_version}
short_version={self.short_version}
fabric_version={self.fabric_version}
launcher={self.launcher}
type={self.type}
is_multimc_or_fork={self.is_multimc_or_fork}
is_prism={self.is_prism}
edit_instance={self.edit_instance}
mod_loader={self.mod_loader}
java_arguments={self.java_arguments}
max_allocated={self.max_allocated}
recommended_min_allocated={self.recommended_min_allocated}
recommended_max_allocated={self.recommended_max_allocated}
seedqueue_ram={self.seedqueue_ram}
ram_guide={self.ram_guide}
setup_guide={self.setup_guide}
fabric_guide={self.fabric_guide}
java_update_guide={self.java_update_guide}
stacktrace={self.stacktrace}
exitcode={self.exitcode}
is_ssg_log={self.is_ssg_log}
is_ranked_log={self.is_ranked_log}
is_seedqueue_log={self.is_seedqueue_log}
is_log={self.is_log}
recommended_mods={self.recommended_mods}
""".strip()
