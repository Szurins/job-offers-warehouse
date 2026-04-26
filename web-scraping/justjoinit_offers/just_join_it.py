import json

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def clean_offer(offer):
    return {
        "title": offer.get("title"),
        "workplaceType": offer.get("workplaceType"),
        "experienceLevel": offer.get("experienceLevel"),
        "category": offer.get("category", {}).get("key"),
        "city": offer.get("city"),
        "street": offer.get("street"),
        "companyName": offer.get("companyName"),
        "companyLogoThumbUrl": offer.get("companyLogoThumbUrl"),
        "publishedAt": offer.get("publishedAt"),
        "employmentTypes": [
            {
                "currency": e.get("currency"),
                "type": e.get("type"),
                "unit": e.get("unit"),
                "from": e.get("from"),
                "to": e.get("to"),
            }
            for e in offer.get("employmentTypes", [])
            if e.get("currency") == "PLN"
        ],
        "niceToHaveSkills": [s.get("name") for s in offer.get("niceToHaveSkills", [])],
        "languages": [
            {"code": l.get("code"), "level": l.get("level")}
            for l in offer.get("languages", [])
        ],
    }


def load_justjoinit_offers():
    chrome_options = Options()
    chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(options=chrome_options)

    status = 200
    count = 0

    all_offers = []

    while status != 500:
        url = f"https://justjoin.it/api/candidate-api/offers?from={count * 1500}&itemsCount=1500"
        driver.get(url)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        pre = soup.find("pre")

        if not pre:
            break

        try:
            messy_json = json.loads(pre.text)
        except Exception as e:
            print("Błąd parsowania JSON:", e)
            break

        status = messy_json.get("status", 200)
        if status == 500:
            break

        offers = messy_json.get("data", [])

        if not offers:
            break

        cleaned = [clean_offer(o) for o in offers]
        all_offers.extend(cleaned)

        print(f"Pobrano batch {count}, ofert: {len(cleaned)}")

        count += 1

    driver.quit()

    with open(
        "justjoinit_offers/json_files/justjoinit_offers.json", "w", encoding="utf-8"
    ) as f:
        json.dump(all_offers, f, ensure_ascii=False, indent=2)

    print(f"Zapisano {len(all_offers)} ofert.")
