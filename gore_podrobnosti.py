import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

# 1) Load your mountains CSV (must have an 'id', 'Name' and 'Link' columns)
df = pd.read_csv("julijske_alpe.csv", dtype={"id": int})

# 2) Prepare a mapping from Slovenian labels → our column names
label_map = {
    "Država":            "Country",
    "Gorovje":           "Mountain Range",
    "Višina":            "Height(m)",
    "Širina/Dolžina":    "Coordinates",
    "Vrsta":             "Type",
    "Ogledov":           "Views",
    "Priljubljenost":    "Popularity",
    "Število slik":      "Number of Images",
    "Število poti":      "Number of Paths",
    "Število GPS sledi": "Number of GPS Paths",
    "Vpisna knjiga":     "Registration Book",
    "Knjiga vpisov":     "Registration Book"
}

# 3) Container for all rows
details = []

# 4) Headers for polite scraping
headers = {"User-Agent": "Mozilla/5.0"}

id = 0

for _, row in df.iterrows():
    id += 1
    mid  = id
    name = row["Name"]
    url  = row["Link"]
    print(f"Scraping {name} (id={mid}) → {url}")

    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.content, "html.parser")

    # --- Title ---
    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # --- Initialize every info field to empty ---
    info = {col: "" for col in label_map.values()}

    # --- Parse the details (div.gorasiv > div.g2) by label ---
    details_section = soup.find("div", class_="gorasiv")
    if details_section:
        for div in details_section.find_all("div", class_="g2"):
            text = div.get_text(" ", strip=True).replace("\u00a0", " ")
            if ":" not in text:
                continue
            label, val = text.split(":", 1)
            label = label.strip()
            val   = val.strip()

            if label in label_map:
                col = label_map[label]
                # Clean up a few fields:
                if label == "Višina":            # extract just the number
                    m = re.search(r"\d+", val)
                    val = m.group() if m else ""
                elif label == "Ogledov":         # remove thousands separators
                    val = val.replace(".", "").strip()
                info[col] = val

    # --- Description (the 3rd direct child div under main2) ---
    description = ""
    main2 = soup.find("div", class_="main2")
    if main2:
        blocks = main2.find_all("div", recursive=False)
        if len(blocks) > 2:
            description = blocks[2].get_text(" ", strip=True).replace("Opis gore:", "").strip()

    # --- Build this row’s dict ---
    row_data = {
        "id":          mid,
        "Name":        name,
        "URL":         url,
        "Title":       title,
    }
    # merge in all the label‐parsed fields
    row_data.update(info)
    row_data["Description"] = description

    details.append(row_data)

    # be polite
    time.sleep(2)

# 5) Write out to CSV with a fixed column order
df_detail = pd.DataFrame(details)
cols = [
    "id","Name","URL","Title",
    "Country","Mountain Range","Height(m)","Coordinates",
    "Type","Views","Popularity","Number of Images",
    "Number of Paths","Number of GPS Paths","Registration Book", 
    "Description"
]
df_detail = df_detail[cols]
df_detail.to_csv("julijske_alpe_podrobnosti.csv", index=False, encoding="utf-8")

print("✅ Saved julijske_alpe_podrobnosti.csv")
