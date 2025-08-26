import requests
from bs4 import BeautifulSoup
import pandas as pd

# URL to scrape
url = "https://www.hribi.net/gorovje/julijske_alpe/1"

# Get the HTML content
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")

# Find the mountain list box
box = soup.find("div", id="gorovjaseznam")

# Find all mountain links in the table
rows = box.find_all("tr")

data = []

print(rows)

for row in rows:
    cols = row.find_all("td")
    if cols:
        name_tag = cols[0].find("a")
        if name_tag:
            name = name_tag.text.strip()
            link = "https://www.hribi.net" + name_tag['href']
        else:
            name = link = ""

        height = cols[1].text.strip() if len(cols) > 1 else ""
        area = cols[2].text.strip() if len(cols) > 2 else ""

        data.append({
            "Name": name,
            "Height": height,
            "Mountain Group": area,
            "Link": link
        })

# # Save to CSV
df = pd.DataFrame(data)
# Remove the second row (index 1)
df = df.drop(df.index[0])

df.to_csv("julijske_alpe.csv", index=False, encoding="utf-8")


print("Scraping completed! Data saved to julijske_alpe.csv")
