import semver, json, re
from packaging import version
from math import sqrt
from typing import Any, Dict, Optional
from ..data_loader import load_issues_json
from ..parser import Log


# Simple presentation presets. Can override by passing `style=` at init.
DEFAULT_STYLES: Dict[str, Dict[str, Any]] = {
    "web": {
        "prefix": {
            "top_info": "‼️ ",
            "error":    "🔴 ",
            "warning":  "🟠 ",
            "note":     "🟡 ",
            "info":     "🟢 ",
            "add":      " ↳ ",
        },
        "bold_open": "**",
        "bold_close": "**",
        "experimental_prefix": "[⚠️ experimental] ",
        "chunk_size": 9, # how many lines per page in build()
    },
    "discord": {
        "prefix": {
            "top_info": "‼️ ",
            "error":    "<:dangerkekw:1123554236626636880> ",
            "warning":  "<:warningkekw:1123563914454634546> ",
            "note":     "<:kekw:1123554521738657842> ",
            "info":     "<:infokekw:1123567743355060344> ",
            "add":      "<:reply:1122083632727724083>*",
        },
        "bold_open": "**",
        "bold_close": "**",
        "experimental_prefix": "**[warning: experimental]** ",
        "chunk_size": 9,
    },
}

class IssueBuilder:
    def __init__(
        self,
        log: Log,
        mode: str = "web",
        style: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.log = log
        self.mode = mode
        self._messages: Dict[str, list[str]] = {
            "top_info": [],
            "error": [],
            "warning": [],
            "note": [],
            "info": [],
        }
        self.amount = 0
        self._last_added: Optional[str] = None
        self.footer = ""

        # Strings source
        self._strings: Dict[str, Any] = load_issues_json()

        # Style
        base = DEFAULT_STYLES["web" if mode not in DEFAULT_STYLES else mode]
        self.style = {**base, **(style or {})}
        # Ensure all required prefixes exist
        self.prefix = {**base["prefix"], **(self.style.get("prefix", {}))}

    # --------------- utilities ---------------

    def _lookup(self, typ: str, key: str, fallback: Optional[str] = None) -> str:
        s = self._strings
        if isinstance(s, dict):
            raw_key = f"{typ}.{key}"
            if raw_key in s:
                return str(s[raw_key])
            
            mode_key = f"{typ}.{key}.{self.mode}"
            if mode_key in s:
                return str(s[mode_key])
        return fallback if fallback is not None else key

    def _bold(self, text: str, want: bool) -> str:
        if not want:
            return text
        return f"{self.style['bold_open']}{text.replace('**', '')}{self.style['bold_close']}"

    def _experimental_wrap(self, text: str, experimental: bool) -> str:
        if not experimental:
            return text
        return f"{self.style['experimental_prefix']}{text}"

    def _add_to(self, typ: str, value: str, add: bool = False):
        self._messages[typ].append(value)
        if not add:
            self.amount += 1
            self._last_added = typ
        return self

    # --------------- public API ---------------

    def top_info(self, key: str, *args):
        text = self._lookup("top_info", key, key).format(*args)
        text = self._bold(text, True)
        return self._add_to("top_info", f"{self.prefix['top_info']}{text}")

    def error(self, key: Optional[str], *args, experimental: bool = False, bold: bool = False):
        if key is None:
            return
        text = self._lookup("error", key, key).format(*args)
        text = self._experimental_wrap(self._bold(text, bold), experimental)
        return self._add_to("error", f"{self.prefix['error']}{text}")

    def warning(self, key: Optional[str], *args, experimental: bool = False, bold: bool = False):
        if key is None:
            return
        text = self._lookup("warning", key, key).format(*args)
        text = self._experimental_wrap(self._bold(text, bold), experimental)
        return self._add_to("warning", f"{self.prefix['warning']}{text}")

    def note(self, key: Optional[str], *args, experimental: bool = False, bold: bool = False):
        if key is None:
            return
        text = self._lookup("note", key, key).format(*args)
        text = self._experimental_wrap(self._bold(text, bold), experimental)
        return self._add_to("note", f"{self.prefix['note']}{text}")

    def info(self, key: Optional[str], *args, experimental: bool = False, bold: bool = False):
        if key is None:
            return
        text = self._lookup("info", key, key).format(*args)
        text = self._experimental_wrap(self._bold(text, bold), experimental)
        return self._add_to("info", f"{self.prefix['info']}{text}")

    def add(self, key: Optional[str], *args, experimental: bool = False, bold: bool = False):
        """
        Appends a continuation line under the last added type.
        Mirrors your old behaviour. If no previous type, it does nothing.
        """
        if key is None or self._last_added is None:
            return
        text = self._lookup("add", key, key).format(*args)
        text = self._experimental_wrap(self._bold(text, bold), experimental)

        # for discord preset we opened with "*"; close it to preserve italics.
        if self.prefix.get("add", "").endswith("*"):
            return self._add_to(self._last_added, f"{self.prefix['add']}{text}*", add=True)
        else:
            return self._add_to(self._last_added, f"{self.prefix['add']}{text}", add=True)

    def has(self, typ: str, key: str) -> bool:
        wanted = self._lookup(typ, key, key)
        wanted = wanted.replace("*", "")
        # convert '{}' wildcards to '.*'
        pattern = re.escape(wanted).replace(r"\{\}", r".*")

        for s in self._messages.get(typ, []):
            # remove prefix ("emoji " or similar)
            _, _, tail = s.partition(" ")
            # strip simple formatting
            tail = tail.replace("*", "")
            tail = tail.replace("<b>", "").replace("</b>", "")
            if re.match(pattern, tail):
                return True
        return False

    def has_values(self) -> bool:
        return self.amount > 0

    def set_footer(self, s: str):
        self.footer = s
        return self

    def build(self, chunk_size: Optional[int] = None) -> list[str]:
        size = chunk_size or int(self.style.get("chunk_size", 9))
        messages: list[str] = []
        index = 0

        # preserve ordering of categories
        for typ in ["top_info", "error", "warning", "note", "info"]:
            items = self._messages.get(typ, [])
            for j_idx, entry in enumerate(items):
                if "Re-Upload Log" in entry and self.has("top_info", "uploaded_log"):
                    continue

                add = entry + "\n"
                # extra blank line after top_info block
                if typ == "top_info" and j_idx == len(items) - 1:
                    add += "\n"

                if not messages or (index % size == 0):
                    messages.append(add)
                else:
                    messages[-1] += add
                index += 1

        return messages
