import json
import os
import re
import time

import requests
from bs4 import BeautifulSoup


def clean_offer(offer):
    salary_raw = offer.get("salary_raw", "")

    if (
        not salary_raw
        or "nie podano" in salary_raw.lower()
        or "szczegóły" in salary_raw.lower()
    ):
        return {
            "title": offer.get("title"),
            "companyName": offer.get("company"),
            "workplaceType": offer.get("work_mode"),
            "employmentTypes": [],
            "link": offer.get("link"),
        }

    currency = "PLN"
    if "eur" in salary_raw.lower() or "€" in salary_raw:
        currency = "EUR"
    elif "usd" in salary_raw.lower() or "$" in salary_raw:
        currency = "USD"

    contract_mapping = {
        "b2b": "B2B",
        "uop": "UoP",
        "uod": "UoD",
        "uz": "UZ",
        "o pracę": "UoP",
        "zlecenie": "UZ",
        "dzieło": "UoD",
    }

    contract_type = "Brak"
    for key, val in contract_mapping.items():
        if key in salary_raw.lower():
            contract_type = val
            break

    unit = "month"
    salary_raw_lower = salary_raw.lower()
    if any(k in salary_raw_lower for k in ["godz", "godzin", " h", "/h"]):
        unit = "hour"
    elif any(k in salary_raw_lower for k in ["dzień", "dzien", " d ", "/d"]):
        unit = "day"

    salary_from = None
    salary_to = None

    numbers = re.findall(r"(\d+(?:\.\d+)?)", salary_raw.replace(",", "."))
    if numbers:
        try:
            if "k" in salary_raw.lower():
                salary_from = int(float(numbers[0]) * 1000)
                if len(numbers) > 1:
                    salary_to = int(float(numbers[1]) * 1000)
            else:
                salary_from = int(float(numbers[0]))
                if len(numbers) > 1:
                    salary_to = int(float(numbers[1]))
        except ValueError:
            pass

    return {
        "title": offer.get("title"),
        "companyName": offer.get("company"),
        "workplaceType": offer.get("work_mode"),
        "employmentTypes": [
            {
                "currency": currency,
                "type": contract_type,
                "unit": unit,
                "from": salary_from,
                "to": salary_to,
            }
        ],
        "link": offer.get("link"),
    }


def scrape_theprotocol():
    page_number = 1
    all_offers = []

    print("Starting offer collection...")

    while True:
        url = f"https://theprotocol.it/praca?sort=date&pageNumber={page_number}"
        print(f"Processing page: {page_number}")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                print(
                    f"Error fetching page {page_number}. Status code: {response.status_code}"
                )
                break
        except Exception as e:
            print(f"Network error occurred: {e}")
            break

        soup = BeautifulSoup(response.text, "html.parser")

        empty_list_element = soup.find(attrs={"data-test": "text-emptyList"})
        if empty_list_element:
            print(f"Reached the end of offers at page {page_number}. Stopping loop.")
            break

        offers_elements = soup.find_all("a", attrs={"data-test": "list-item-offer"})
        if not offers_elements:
            print(f"No offers on page {page_number} (no HTML elements found). End.")
            break

        page_offers = []
        for offer in offers_elements:
            title_el = offer.find(attrs={"data-test": "text-jobTitle"})
            title = title_el.text.strip() if title_el else "Brak"

            company_el = offer.find(attrs={"data-test": "text-employerName"})
            company = company_el.text.strip() if company_el else "Brak"

            work_mode_el = offer.find(attrs={"data-test": "text-workModes"})
            work_mode = work_mode_el.text.strip() if work_mode_el else "Brak"

            salary_container = offer.find(attrs={"data-test": "text-salary"})
            salary_raw = salary_container.text.strip() if salary_container else ""

            link = offer.get("href", "")
            if link and not link.startswith("http"):
                link = f"https://theprotocol.it{link}"

            raw_data = {
                "title": title,
                "company": company,
                "work_mode": work_mode,
                "salary_raw": salary_raw,
                "link": link,
            }
            page_offers.append(raw_data)

        cleaned = [clean_offer(o) for o in page_offers]
        all_offers.extend(cleaned)

        time.sleep(1)
        page_number += 1

    output_dir = "theprotocolit_offers/json_files"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_path = os.path.join(output_dir, "theprotocolit_offers.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_offers, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(all_offers)} offers.")
