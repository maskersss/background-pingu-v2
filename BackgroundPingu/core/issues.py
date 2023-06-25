import semver, re
from packaging import version
from BackgroundPingu.bot.main import BackgroundPingu
from BackgroundPingu.core.parser import Log, ModLoader, OperatingSystem

class IssueBuilder:
    def __init__(self, bot: BackgroundPingu) -> None:
        self.bot = bot
        self._messages = {
            "error": [],
            "warning": [],
            "note": []
        }
        self.amount = 0
        self._last_added = None
    
    def _add_to(self, type: str, value: str, add: bool=False):
        self._messages[type].append(value)
        if not add:
            self.amount += 1
            self._last_added = type
        return self

    def error(self, key: str, *args):
        return self._add_to("error", "🔴 " + self.bot.strings.get(f"error.{key}", key).format(*args))
    
    def warning(self, key: str, *args):
        return self._add_to("warning", "🟠 " + self.bot.strings.get(f"warning.{key}", key).format(*args))
    
    def note(self, key: str, *args):
        return self._add_to("note", "🟡 " + self.bot.strings.get(f"note.{key}", key).format(*args))

    def add(self, key: str):
        return self._add_to(self._last_added, "<:reply:1121924702756143234>*" + self.bot.strings.get(f"add.{key}", key) + "*", add=True)

    def has_values(self) -> bool:
        return self.amount > 0

    def build(self) -> list[str]:
        messages = []
        index = 0
        for i in self._messages:
            for j in self._messages[i]:
                add = j + "\n"
                if len(messages) == 0 or index % 9 == 0: messages.append(add)
                else: messages[len(messages) - 1] += add
                index += 1
        return messages

class IssueChecker:
    def __init__(self, bot: BackgroundPingu, log: Log) -> None:
        self.bot = bot
        self.log = log
        self.java_17_mods = [
            "antiresourcereload",
            "serversiderng",
            "setspawnmod",
            "peepopractice"
        ]
    
    def get_mod_metadata(self, mod_filename: str) -> dict:
        mod_filename = mod_filename.lower()
        filenames = [mod_filename.replace(" ", ""), mod_filename.replace("-", ""), mod_filename.replace("+", "")]
        for mod in self.bot.mods:
            original_name = mod["name"].lower()
            mod_names = [original_name.replace(" ", ""), original_name.replace("-", "")]
            if any(mod_name in filename for filename in filenames for mod_name in mod_names):
                return mod
        return None
    
    def get_latest_version(self, metadata: dict) -> bool:
        minecraft_version = semver.Version.parse(self.log.minecraft_version)
        latest_match = None
        for file_data in metadata["files"]:
            for game_version in file_data["game_versions"]:
                all_versions = game_version.split(" ")
                for version in all_versions:
                    try:
                        if minecraft_version.match(version):
                            latest_match = file_data
                            #if version.startswith("=="):
                            #    return latest_match
                            if str(minecraft_version) in version:
                                return latest_match
                        # elif not latest_match is None: return latest_match
                    except ValueError: continue
        return latest_match

    def check(self) -> IssueBuilder:
        builder = IssueBuilder(self.bot)

        has_mcsr_mod = False
        illegal_mods = []
        checked_mods = []
        all_incompatible_mods = {}
        for mod in self.log.mods:
            metadata = self.get_mod_metadata(mod)
            if not metadata is None:
                mod_name = metadata["name"]

                try:
                    for incompatible_mod in metadata["incompatible"]:
                        if all_incompatible_mods[mod_name] is None:
                            all_incompatible_mods[mod_name] = [incompatible_mod]
                        else:
                            all_incompatible_mods[mod_name].append(incompatible_mod)
                except KeyError: pass

                if mod_name in checked_mods: builder.add("duplicate_mod", mod_name.lower())
                else: checked_mods.append(mod_name.lower())

                has_mcsr_mod = True

                latest_version = self.get_latest_version(metadata)
                if not latest_version is None and not (latest_version["name"] == mod or latest_version["version"] in mod):
                    if not "sodiummac" in mod:
                        builder.error("outdated_mod", mod_name, latest_version["page"])
                        continue
                elif latest_version is None: continue
            else: illegal_mods.append(mod)
        if len(illegal_mods) > 0: builder.note("amount_illegal_mods", len(illegal_mods))

        for key, value in all_incompatible_mods.items():
            for incompatible_mod in value:
                if self.log.has_mod(incompatible_mod):
                    builder.error("incompatible_mod", key, incompatible_mod)
        
        if not self.log.mod_loader in [None, ModLoader.FABRIC, ModLoader.VANILLA]:
            if has_mcsr_mod:
                builder.error("incompatible_loader", self.log.mod_loader.value)
                builder.add("fabric_guide")
            builder.note("using_other_loader", self.log.mod_loader.value).add("fabric_guide")

        if len(self.log.mods) > 0 and self.log.mod_loader == ModLoader.VANILLA:
            builder.error("no_loader")
        
        if not self.log.operating_system is None and self.log.operating_system == OperatingSystem.MACOS:
            if self.log.has_mod("sodium-1.16.1-v1.jar") or self.log.has_mod("sodium-1.16.1-v2.jar"):
                builder.error("not_using_mac_sodium")

            if not self.log.launcher is None and self.log.launcher.lower() == "multimc":
                builder.note("use_prism").add("mac_setup_guide")
        
        has_java_error = False
        if not self.log.major_java_version is None and self.log.major_java_version < 17:
            wrong_mods = []
            for mod in self.java_17_mods:
                for installed_mod in self.log.mods:
                    if mod in installed_mod.lower():
                        wrong_mods.append(mod)
            if len(wrong_mods) > 0:
                builder.error(
                    "need_java_17_mods",
                    "mods" if len(wrong_mods) > 1 else
                    "a mod",
                    "`, `".join(wrong_mods),
                    "s" if len(wrong_mods) == 1 else
                    ""
                ).add("java_upgrade_guide")
                has_java_error = True
        
        if not has_java_error and self.log.has_content("require the use of Java 17"):
            builder.error("need_java_17_mc").add("java_upgrade_guide")
            has_java_error = True
        
        if not has_java_error:
            needed_java_version = None
            if self.log.has_content("java.lang.UnsupportedClassVersionError"):
                match = re.compile(r"class file version (\d+\.\d+)").search(self.log._content)
                if not match is None:
                    needed_java_version = round(float(match.group(1))) - 44
            compatibility_match = re.compile(r"The requested compatibility level (JAVA_\d+) could not be set.").search(self.log._content)
            if not compatibility_match is None:
                parsed_version = int(compatibility_match.group(1).split("_")[1])
                if parsed_version > needed_java_version:
                    needed_java_version = parsed_version
            if not needed_java_version is None:
                builder.error("need_new_java", needed_java_version).add("java_upgrade_guide")
                has_java_error = True
        
        if not has_java_error and self.log.has_content("You might want to install a 64bit Java version"):
            builder.error("32_bit_java").add("java_upgrade_guide")
            has_java_error = True
        
        if not has_java_error and self.log.has_content("Incompatible magic value 0 in class file sun/security/provider/SunEntries"):
            builder.error("broken_java").add("java_upgrade_guide")
            has_java_error = True
        
        if not self.log.mod_loader is None and self.log.mod_loader == ModLoader.FABRIC:
            if not self.log.fabric_version is None:
                highest_srigt_ver = None
                for mod in self.log.mods:
                    if "speedrunigt" in mod.lower():
                        match = re.compile(r"-(\d+(?:\.\d+)?)\+").search(mod)
                        if not match is None:
                            ver = version.parse(match.group(1))
                            if highest_srigt_ver is None or ver > highest_srigt_ver:
                                highest_srigt_ver = ver
                if highest_srigt_ver < version.parse("13.3") and self.log.fabric_version > version.parse("0.14.14"):
                    builder.error("incompatible_srigt")
                    if not self.log.minecraft_version == "1.16.1":
                        builder.add("incompatible_srigt_alternative")
                
                if self.log.fabric_version < version.parse("0.12.2"):
                    builder.error("really_old_fabric").add("fabric_guide")
                elif self.log.fabric_version < version.parse("0.14.0"):
                    builder.warning("relatively_old_fabric").add("fabric_guide")
                elif self.log.fabric_version < version.parse("0.14.14"):
                    builder.note("old_fabric").add("fabric_guide")
                elif self.log.fabric_version.__str__() in ["0.14.15", "0.14.16"]:
                    builder.error("broken_fabric").add("fabric_guide")
        
        if not self.log.max_allocated is None:
            has_shenandoah = self.log.has_java_argument("shenandoah")
            min_limit_1 = 1200 if has_shenandoah else 1900
            min_limit_2 = 850 if has_shenandoah else 1200
            if self.log.max_allocated < min_limit_1 and (self.log.has_content("OutOfMemoryError") or self.log.has_content("Process crashed with exitcode -805306369")):
                builder.error("too_little_ram_crash").add("allocate_ram_guide")
            elif self.log.max_allocated < min_limit_2:
                builder.warning("too_little_ram").add("allocate_ram_guide")
            elif self.log.max_allocated < min_limit_1:
                builder.note("too_little_ram").add("allocate_ram_guide")
            elif self.log.max_allocated > 10000:
                builder.error("too_much_ram").add("allocate_ram_guide")
            elif self.log.max_allocated > 4800:
                builder.warning("too_much_ram").add("allocate_ram_guide")
            elif self.log.max_allocated > 3500:
                builder.note("too_much_ram").add("allocate_ram_guide")
        elif self.log.has_content("OutOfMemoryError"):
            builder.error("too_little_ram_crash").add("allocate_ram_guide")
        
        if not self.log.minecraft_folder is None:
            if "OneDrive" in self.log.minecraft_folder:
                builder.note("onedrive")
            if "C:/Program Files" in self.log.minecraft_folder:
                builder.note("program_files")
        
        if self.log.has_content("A fatal error has been detected by the Java Runtime Environment") or self.log.has_content("EXCEPTION_ACCESS_VIOLATION"):
            builder.error("eav_crash")
            for i in range(4): builder.add(f"eav_crash_{i + 1}")
            if self.log.has_mod("speedrunigt"): builder.add("eav_crash_srigt")
            builder.add("eav_crash_disclaimer")
        
        if self.log.has_mod("phosphor"):
            builder.note("starlight_better")
            metadata = self.get_mod_metadata("starlight")
            if not metadata is None:
                latest_version = self.get_latest_version(metadata)
                if not latest_version is None:
                    builder.add("mod_download", metadata["name"], latest_version["page"])
        
        if self.log.has_content("Failed to download the assets index"):
            builder.error("assets_index_fail")
        
        if self.log.has_content("Invalid id 4096 - maximum id range exceeded"):
            builder.error("exceeded_id_limit")
        
        if self.log.has_content("NSWindow drag regions should only be invalidated on the Main Thread"):
            builder.error("mac_too_new_java")
        
        if self.log.has_content("Pixel format not accelerated"):
            builder.error("gl_pixel_format")
        
        if self.log.has_content("Shaders Mod detected"):
            builder.error("shaders_mod_plus_of")
        
        system_libs = [lib for lib in ["GLFW", "OpenAL"] if self.log.has_content("Using system " + lib)]
        system_arg = None
        if len(system_libs) == 2: system_arg = f"{system_libs[0]} and {system_libs[1]} installations"
        elif len(system_libs) == 1: system_arg = f"{system_libs[0]} installation"
        if not system_arg is None:
            if self.log.has_content("Failed to locate library:"): builder.error("builtin_lib_crash", system_arg)
            else: builder.note("builtin_lib_recommendation", system_arg)
        
        if self.log.has_content("me.jellysquid.mods.sodium.client"):
            builder.error("sodium_config_crash")
        
        if self.log.has_mod("serversiderng"):
            builder.note("using_ssrng")
        
        required_mod_match = re.findall(r"requires (.*?) of (\w+),", self.log._content)
        for required_mod in required_mod_match:
            mod_name = required_mod[1]
            if mod_name.lower() == "fabric":
                builder.error("requires_fabric_api")
                continue
            builder.error("requires_mod", mod_name)
        
        if self.log.has_mod("fabric-api"):
            builder.warning("using_fabric_api")
        
        if self.log.has_content("Couldn't extract native jar"):
            builder.error("locked_libs")
        
        if not re.compile(r"java\.io\.IOException: Directory \'(.+?)\' could not be created").search(self.log._content) is None:
            builder.warning("try_admin_launch")
        
        if self.log.has_content("WGL_ARB_create_context_profile is unavaible"):
            builder.error("intel_hd2000").add("intell_hd2000_info")
        
        if self.log.has_content("-1073741819 (0xffffffffc0000005)") or self.log.has_content("The instruction at 0x%p referenced memory at 0x%p. The memory could not be %s."):
            builder.error("exitcode_1073741819")
            for i in range(4):
                builder.add(f"exitcode_1073741819_{i + 1}")
        
        if self.log.has_content("Process crashed with exitcode -805306369") or self.log.has_content("java.lang.ArithmeticException") or (self.log.has_content("########## GL ERROR ##########") and self.log.has_content("@ Render")):
            builder.warning("exitcode_805306369")
        
        if self.log.has_mod("autoreset") or self.log.has_content("the mods atum and autoreset"):
            atum_link = "https://modrinth.com/mod/atum/versions"
            metadata = self.get_mod_metadata("atum")
            if not metadata is None:
                latest_version = self.get_latest_version(metadata)
                if not latest_version is None:
                    atum_link = latest_version["page"]
            builder.error("autoreset_user", atum_link)

        if self.log.has_content("Failed to find Minecraft main class"):
            builder.error("online_launch_required")
        
        if not self.log.launcher is None and self.log.launcher.lower() == "prism":
            pattern = r"This instance is not compatible with Java version (\d+)\.\nPlease switch to one of the following Java versions for this instance:\nJava version (\d+)"
            match = re.search(pattern, self.log._content)
            if not match is None:
                switch_java = False
                if self.log.mod_loader == ModLoader.FORGE: switch_java = True
                elif not self.log.minecraft_version is None:
                    short_version = self.log.minecraft_version[:4]
                    if short_version in [f"1.{18 + i}" for i in range(6)]: switch_java = True
                if switch_java:
                    current_version = int(match.group(1))
                    compatible_version = int(match.group(2))
                    builder.error(
                        "incorrect_java_prism",
                        current_version,
                        compatible_version,
                        compatible_version,
                        " (download the .msi file)" if self.log.operating_system == OperatingSystem.WINDOWS else
                        " (download the .pkg file)" if self.log.operating_system == OperatingSystem.MACOS else
                        "",
                        compatible_version
                    )
                else:
                    builder.error("java_comp_check")
        
        if not self.log.launcher is None and self.log.launcher.lower() == "multimc":
            if self.log.has_content("java.lang.ClassNotFoundException: org.apache.logging.log4j.spi.AbstractLogger"):
                builder.error("no_abstract_logger")
        
        if not self.log.mod_loader is None and self.log.mod_loader == ModLoader.FORGE:
            if self.log.has_content("ClassLoaders$AppClassLoader cannot be cast to class java.net.URLClassLoader"):
                builder.error("forge_too_new_java")
            if self.log.has_content("Unable to detect the forge installer!"):
                builder.error("random_forge_crash_1")
            if self.log.has_content("java.lang.NoClassDefFoundError: cpw/mods/modlauncher/Launcher"):
                builder.error("random_forge_crash_2")
        
        ranked_matches = re.findall(r"The Fabric Mod \"(.*?)\" is not whitelisted!", self.log._content)
        if len(ranked_matches) > 0:
            builder.error("ranked_illegal_mod", ranked_matches[0])

        return builder
