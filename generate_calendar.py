import requests
from bs4 import BeautifulSoup

url = "https://www.dd-munich.de/event-list"
headers = {"User-Agent": "Mozilla/5.0"}

resp = requests.get(url, headers=headers)
soup = BeautifulSoup(resp.text, "html.parser")

scripts = soup.find_all("script")

for s in scripts:
    if "events" in s.text.lower() or "wix" in s.text.lower():
        print("---- SCRIPT FOUND ----")
        print(s.text[:2000])
        print("----------------------")
