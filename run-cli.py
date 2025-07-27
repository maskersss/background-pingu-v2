import argparse, json, random, re, traceback
from loghelper.issues.builder import IssueBuilder
from loghelper.issues.checker import IssueChecker
from loghelper import parser
from loghelper.config import *

class LogCLI:
    def get_logs_from_link(self, link, include_content=False):
        link_pattern = LINK_PATTERN
        matches = re.findall(link_pattern, link)
        if len(matches) > 3: matches = random.sample(matches, 3)

        logs = [(match.split("?ex")[0], parser.Log.from_link(match)) for match in matches]
        logs = [(link, log) for (link, log) in logs if log is not None]
        logs = sorted(logs, key=lambda x: len(x[1]._content), reverse=True)
        if include_content:
            logs.append(("message", parser.Log(link)))
        return logs

    def check_log(self, log_link, include_content=False):
        result = {"text": None, "embed": None}
        logs = self.get_logs_from_link(log_link, include_content)
        
        for link, log in logs:
            try:
                results = IssueChecker(
                    log,
                    link,
                    None,  # No guild ID
                    None,  # No channel ID
                    "web",
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
                reply, success = IssueChecker(
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
