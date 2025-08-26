import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import csv
from urllib.parse import urljoin

# Load CSV from previous step
df = pd.read_csv("julijske_alpe.csv")

header = [
    "mountain_id",
    "route_name",
    "route_time",
    "route_difficulty",
    "start_point",
    "ferata",
    "height_diff",
    "gear_summer",
    "gear_winter"
]

# 2) Create (or overwrite) the CSV with that header
with open("poti.csv", "w", newline="", encoding="utf-8") as fout:
    writer = csv.writer(fout)
    writer.writerow(header)


headers = {
    "User-Agent": "Mozilla/5.0"
}

id = 0

for idx, row in df.iterrows():
    name = row['Name']
    url = row['Link']
    id += 1

    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")

        main_box = soup.find("div", class_="main2")
        main2_all = main_box.find_all("div", recursive=False)
        
        description = main2_all[2].text.strip() if len(main2_all) > 2 else ""
        description = description.replace("Opis gore:", "").strip()

        routes = []
        table = soup.find("table", id="poti")
        routes_all = table.find_all("tr", class_=["trG0", "trG1"]) if table else []

        
        route_label_map = {
            "Izhodišče":                     "start_point",
            "Ferata":                        "ferata",
            "Višinska razlika":              "height_diff",
            "Priporočena oprema (poletje)":  "gear_summer",
            "Priporočena oprema (zima)":     "gear_winter"
        }

        if table:
            for route in routes_all:
                # reset every field
                route_name = route_time = route_difficulty = ""
                route_info = {v: "" for v in route_label_map.values()}
                print(f"  Scraping route/s {len(routes) + 1} for {name}")

                # 1) name + link
                try:
                    a0 = route.find_all("a")[0]
                    route_name = a0.text.strip()
                    href = a0.get("href", "")
                    link = urljoin("https://www.hribi.net", href)
                except Exception:
                    link = None

                # 2) time & difficulty
                a_tags = route.find_all("a")
                if len(a_tags) > 1:
                    route_time = a_tags[1].text.strip()
                if len(a_tags) > 2:
                    route_difficulty = a_tags[2].text.strip()

                # 3) fetch the route page and parse its gorasiv box
                if link:
                    try:
                        r2 = requests.get(link, headers=headers, timeout=10)
                        s2 = BeautifulSoup(r2.content, "html.parser")
                        box2 = s2.find("div", class_="gorasiv")
                        if box2:
                            for div2 in box2.find_all("div", class_="g2"):
                                txt = div2.get_text(" ", strip=True).replace("\xa0", " ")
                                if ":" not in txt:
                                    continue
                                lab, val = txt.split(":", 1)
                                lab = lab.strip()
                                val = val.strip()
                                if lab in route_label_map:
                                    col = route_label_map[lab]
                                    # special cleanup for height_diff
                                    if lab == "Višinska razlika":
                                        m = re.search(r"\d+", val)
                                        val = m.group() if m else ""
                                    route_info[col] = val
                    except Exception as e:
                        print(f"  ⚠️  Couldn't load route details at {link}: {e}")

                # 4) Append a full row tuple
                routes.append((
                    id,
                    route_name,
                    route_time,
                    route_difficulty,
                    route_info["start_point"],
                    route_info["ferata"],
                    route_info["height_diff"],
                    route_info["gear_summer"],
                    route_info["gear_winter"],
                ))
                
                print(f"  ✔ Successfully scraped route: {route_name}")
                time.sleep(1)  # Respectful scraping

            # write out all at once
            with open("poti.csv", "a", newline="", encoding="utf-8") as fout:
                writer = csv.writer(fout)
                writer.writerows(routes)
        
        # Respectful scraping
        time_out = 2
        print(f"✅ Successfully scraped {name}")
        print(f"Now waiting for {time_out} seconds before next request...")
        time.sleep(time_out)  

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        continue
