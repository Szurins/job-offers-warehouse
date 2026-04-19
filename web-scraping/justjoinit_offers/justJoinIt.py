import json

from bs4 import BeautifulSoup
from selenium import webdriver


def load_justJoinIt_offers():
    driver = webdriver.Chrome()
    status = 200
    count = 0

    json_job_offers = {}
    while status != 500:
        driver.get(
            f"https://justjoin.it/api/candidate-api/offers?from={count * 1500}&itemsCount=1500"
        )
        soup = BeautifulSoup(driver.page_source, "html.parser")
        pres = soup.find_all("pre")

        for pre in pres:
            if "status" in json_job_offers:
                status = json_job_offers["status"]
                if status == 500:
                    break
            json_job_offers.update(json.loads(pre.text))

        count += 1

    with open("justjoinit_offers/json_files/justjoinit_offers.json", "a") as f:
        json.dump(json_job_offers, f)
    driver.quit()
