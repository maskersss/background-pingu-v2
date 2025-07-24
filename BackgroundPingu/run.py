from BackgroundPingu.bot import main
from BackgroundPingu import secrets
from BackgroundPingu.data import issues_sorter, mods_getter
from discord.errors import HTTPException
from time import sleep

def run_bot():
    try:
        main.BackgroundPingu().run(secrets.Discord.TOKEN)
    except HTTPException as e:
        if e.status == 429:  # 429 is the status code for rate limiting
            print("We are being rate-limited. Sleeping for 10 minutes...")
            sleep(600)
        else:
            print(f"An HTTP error occurred:")
            raise e

if __name__ == "__main__":
    mods_getter.get_mods()
    issues_sorter.sort()
    run_bot()
