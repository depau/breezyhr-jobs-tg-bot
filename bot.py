import asyncio
import json
import os

import requests
from bs4 import BeautifulSoup
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton

# Environment variables
url = os.environ["URL"].rstrip("/")
persistence_file_path = os.environ.get("PERSISTENCE_PATH", "persist.json")
telegram_bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
telegram_chat_id = os.environ["TELEGRAM_CHAT_ID"]


def clean_polyglot_label(text):
    return text.replace("%LABEL_POSITION_TYPE_", "").replace("%", "").replace("s", "")


async def main():
    response = requests.get(url)
    if response.status_code != 200:
        print("Failed to fetch the webpage")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    job_listings = soup.select("ul.positions li.position")

    try:
        with open(persistence_file_path, "r") as file:
            persisted_listings = json.load(file)
    except FileNotFoundError:
        persisted_listings = {}

    current_listings = {}
    bot = Bot(token=telegram_bot_token)

    for listing in job_listings:
        title = listing.find("h2").text.strip()
        location = clean_polyglot_label(
            listing.find("li", class_="location").text.strip()
        )
        type_ = clean_polyglot_label(listing.find("li", class_="type").text.strip())
        department = listing.find("li", class_="department").text.strip()
        salary_range = listing.find("li", class_="salary-range").text.strip()
        listing_url = listing.find("a")["href"].lstrip("/")
        full_url = (
            f"{url}/{listing_url}"
            if not listing_url.startswith("http")
            else listing_url
        )

        current_listings[listing_url] = {
            "title": title,
            "location": location,
            "type": type_,
            "department": department,
            "salary_range": salary_range,
            "url": full_url,
        }

        if listing_url not in persisted_listings:
            message = (
                f"<b>New job listing found:</b> {title}\n"
                f"<b>Location:</b> {location}\n"
                f"<b>Type:</b> {type_}\n"
                f"<b>Department:</b> {department}\n"
                f"<b>Salary Range:</b> {salary_range}\n"
            )
            keyboard = [[InlineKeyboardButton(text="Apply", url=full_url)]]
            await bot.send_message(
                chat_id=telegram_chat_id,
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML",
            )

    with open(persistence_file_path, "w") as file:
        json.dump(current_listings, file, indent=2)


if __name__ == "__main__":
    while True:
        asyncio.run(main())
        asyncio.sleep(os.environ.get("POLL_INTERVAL", 3600))
