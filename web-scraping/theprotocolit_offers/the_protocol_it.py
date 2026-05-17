import json
import os
import time

import requests
from bs4 import BeautifulSoup


def clean_offer(offer):
    return {
        "title": offer.get("title"),
        "companyName": offer.get("company"),
        "workplaceType": offer.get("work_mode"),
        "salary": offer.get("salary"),
        "contractType": offer.get("contract_type"),
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

            salary_el = offer.find(attrs={"data-test": "text-earningText"})
            salary = salary_el.text.strip() if salary_el else "Nie podano"

            contract_el = offer.find(attrs={"data-test": "text-contractType"})
            contract_type = contract_el.text.strip() if contract_el else "Brak"

            link = offer.get("href", "")
            if link and not link.startswith("http"):
                link = f"https://theprotocol.it{link}"

            raw_data = {
                "title": title,
                "company": company,
                "work_mode": work_mode,
                "salary": salary,
                "contract_type": contract_type,
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

    output_path = os.path.join(output_dir, "theprotocol_offers.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_offers, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(all_offers)} offers.")
