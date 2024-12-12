import argparse, re, traceback, json
from BackgroundPingu.core import parser, issues

class MockBackgroundPingu:
    def __init__(self):
        # Mock the necessary attributes
        with open("./BackgroundPingu/data/issues.json", "r") as f:
            self.strings = json.load(f)
        with open("./BackgroundPingu/data/mods.json", "r") as f:
            self.mods = json.load(f)

        self.cog_blacklist = []
        self.cog_folder_blacklist = ["__pycache__"]
        self.cogs_path = "./BackgroundPingu/bot/cogs"


class LogCLI:
    def __init__(self):
        self.bot = MockBackgroundPingu()  # Use the mocked bot object

    def get_logs_from_link(self, link, include_content=False):
        link_pattern = r"https:\/\/(?:api\.)?paste\.ee\/.\/\w+|https:\/\/mclo\.gs\/\w+|https?:\/\/[\w\-_\/.]+\.(?:txt|log|tdump)\?ex=[^&]+&is=[^&]+&hm=[^&]+&|https?:\/\/[\w\-_\/.]+\.(?:txt|log|tdump)"
        matches = re.findall(link_pattern, link)
        logs = [(match.split("?ex")[0], parser.Log.from_link(match)) for match in matches]
        logs = [(link, log) for (link, log) in logs if log is not None]
        logs = sorted(logs, key=lambda x: len(x[1]._content), reverse=True)
        if include_content:
            logs.append(("input_text", parser.Log(link)))
        return logs

    def check_log(self, log_link, include_content=False):
        result = {"text": None, "embed": None}
        logs = self.get_logs_from_link(log_link, include_content)
        
        for link, log in logs:
            try:
                results = issues.IssueChecker(
                    self.bot,
                    log,
                    link,
                    None,  # No guild ID
                    None,  # No channel ID
                ).check()
                
                if results.has_values():
                    messages = results.build()
                    result["embed"] = "\n".join(messages)
                    return result
            except Exception as e:
                error = "".join(traceback.format_exception(e))
                result["text"] = f"Error:\n{error}"
                return result
        return result

    def get_settings(self, log_link):
        logs = self.get_logs_from_link(log_link, include_content=False)
        for link, log in logs:
            try:
                reply, success = issues.IssueChecker(
                    self.bot,
                    log,
                    link,
                    None,  # No guild ID
                    None,  # No channel ID
                ).seedqueue_settings()
                if success:
                    return reply
            except Exception as e:
                error = "".join(traceback.format_exception(e))
                return f"Error:\n{error}"
        return None


def main():
    parser = argparse.ArgumentParser(description="Log Analysis Tool")
    parser.add_argument("--link", required=True, help="Link to the log file")
    parser.add_argument(
        "--mode", choices=["check", "settings"], default="check", help="Mode: 'check' for issue checking, 'settings' for recommending SeedQueue settings"
    )

    args = parser.parse_args()
    cli = LogCLI()

    if args.mode == "check":
        result = cli.check_log(args.link, include_content=False)
        if result["embed"]:
            print(result['embed'])
        elif result["text"]:
            print(result["text"])
        else:
            print("No issues found.")

    elif args.mode == "settings":
        settings = cli.get_settings(args.link)
        if settings:
            print(settings)
        else:
            print("No log found.")


if __name__ == "__main__":
    main()
