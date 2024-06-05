import asyncio
import datetime
import os
import re
import time
from typing import Union, List, Optional

import requests
from rich.console import Console
from rich.prompt import IntPrompt
from rich.table import Table
from rich.text import Text
from selenium import webdriver

from icloud import HideMyEmail

MAX_CONCURRENT_TASKS = 10
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1247538256162197627/lAgMP_1xpxG0AhfI_n9xFbHYwjE8XyDQlqdt_UCmoz1K3Mi1dLrbxsQ_eUUDNNmBlmoH"


class RichHideMyEmail(HideMyEmail):
    _cookie_file = "cookie.txt"

    def __init__(self):
        super().__init__()
        self.console = Console()
        self.table = Table()

        if os.path.exists(self._cookie_file):
            # load in a cookie string from file
            with open(self._cookie_file, "r") as f:
                self.cookies = [line for line in f if not line.startswith("//")][0]
        else:
            self.console.log(
                '[bold yellow][WARN][/] No "cookie.txt" file found! Generation might not work due to unauthorized access.'
            )

    async def _generate_one(self) -> Union[str, None]:
        # First, generate an email
        gen_res = await self.generate_email()

        if not gen_res:
            return
        elif "success" not in gen_res or not gen_res["success"]:
            error = gen_res["error"] if "error" in gen_res else {}
            err_msg = "Unknown"
            if type(error) == int and "reason" in gen_res:
                err_msg = gen_res["reason"]
            elif type(error) == dict and "errorMessage" in error:
                err_msg = error["errorMessage"]
            self.console.log(
                f"[bold red][ERR][/] - Failed to generate email. Reason: {err_msg}"
            )
            return

        email = gen_res["result"]["hme"]
        self.console.log(f'[50%] "{email}" - Successfully generated')

        # Then, reserve it
        reserve_res = await self.reserve_email(email)

        if not reserve_res:
            return
        elif "success" not in reserve_res or not reserve_res["success"]:
            error = reserve_res["error"] if "error" in reserve_res else {}
            err_msg = "Unknown"
            if type(error) == int and "reason" in reserve_res:
                err_msg = reserve_res["reason"]
            elif type(error) == dict and "errorMessage" in error:
                err_msg = error["errorMessage"]
            self.console.log(
                f'[bold red][ERR][/] "{email}" - Failed to reserve email. Reason: {err_msg}'
            )
            return

        self.console.log(f'[100%] "{email}" - Successfully reserved')
        return email

    async def _generate(self, num: int):
        tasks = []
        for _ in range(num):
            task = asyncio.ensure_future(self._generate_one())
            tasks.append(task)

        return filter(lambda e: e is not None, await asyncio.gather(*tasks))

    async def generate(self, count: Optional[int]) -> List[str]:
        try:
            emails = []
            self.console.rule()
            if count is None:
                s = IntPrompt.ask(
                    Text.assemble(("How many iCloud emails you want to generate?")),
                    console=self.console,
                )

                count = int(s)
            self.console.log(f"Generating {count} email(s)...")
            self.console.rule()

            with self.console.status(f"[bold green]Generating iCloud email(s)..."):
                while count > 0:
                    batch = await self._generate(
                        count if count < MAX_CONCURRENT_TASKS else MAX_CONCURRENT_TASKS
                    )
                    count -= MAX_CONCURRENT_TASKS
                    emails += batch

            if len(emails) > 0:
                with open("emails.txt", "a+") as f:
                    f.write(os.linesep.join(emails) + os.linesep)

                self.console.rule()
                self.console.log(
                    f':star: Emails have been saved into the "emails.txt" file'
                )

                self.console.log(
                    f"[bold green]All done![/] Successfully generated [bold green]{len(emails)}[/] email(s)"
                )

            return emails
        except KeyboardInterrupt:
            return []

    async def list(self, active: bool, search: str) -> None:
        gen_res = await self.list_email()
        if not gen_res:
            return

        if "success" not in gen_res or not gen_res["success"]:
            error = gen_res["error"] if "error" in gen_res else {}
            err_msg = "Unknown"
            if type(error) == int and "reason" in gen_res:
                err_msg = gen_res["reason"]
            elif type(error) == dict and "errorMessage" in error:
                err_msg = error["errorMessage"]
            self.console.log(
                f"[bold red][ERR][/] - Failed to generate email. Reason: {err_msg}"
            )
            return

        self.table.add_column("Label")
        self.table.add_column("Hide my email")
        self.table.add_column("Created Date Time")
        self.table.add_column("IsActive")

        for row in gen_res["result"]["hmeEmails"]:
            if row["isActive"] == active:
                if search is not None and re.search(search, row["label"]):
                    self.table.add_row(
                        row["label"],
                        row["hme"],
                        str(
                            datetime.datetime.fromtimestamp(
                                row["createTimestamp"] / 1000
                            )
                        ),
                        str(row["isActive"]),
                    )
                else:
                    self.table.add_row(
                        row["label"],
                        row["hme"],
                        str(
                            datetime.datetime.fromtimestamp(
                                row["createTimestamp"] / 1000
                            )
                        ),
                        str(row["isActive"]),
                    )

        self.console.print(self.table)

    def send_discord_message(self, new_emails_count: int) -> None:
        with open("emails.txt", "r") as f:
            total_emails_count = len([line for line in f if line.strip()])

        message = (
            f"Successfully generated {new_emails_count} new email(s). "
            f"Total number of generated emails: {total_emails_count}."
        )
        
        payload = {"content": message}
        requests.post(DISCORD_WEBHOOK_URL, json=payload)


async def generate(count: Optional[int]) -> None:
    # Define the URL
    url = "https://www.icloud.com/settings/"

    # Set up the Selenium WebDriver (using Chrome in this example)
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=options)

    try:
        # Open the URL
        driver.get(url)

        # Wait for user to press Enter in the console after completing necessary actions
        input("Press Enter after completing the manual steps...")

        while True:
            # Refresh the page to get new cookies
            driver.refresh()
            time.sleep(5)  # Give some time for the page to refresh

            # Get the cookies
            cookies = driver.get_cookies()
            
            # Format the cookies as semicolon-separated name=value pairs
            cookie_string = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
            
            # Save the formatted cookies string to cookie.txt
            with open("cookie.txt", "w") as f:
                f.write(cookie_string)

            async with RichHideMyEmail() as hme:
                new_emails = await hme.generate(5)
                hme.send_discord_message(len(new_emails))
            
            await asyncio.sleep(31 * 60)  # wait for 31 minutes before next iteration

    except KeyboardInterrupt:
        # Handle manual interruption gracefully
        pass


async def list(active: bool, search: str) -> None:
    async with RichHideMyEmail() as hme:
        await hme.list(active, search)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(generate(None))
    except KeyboardInterrupt:
        pass