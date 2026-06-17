import requests
import os

DW_TOKEN = os.environ["DW_TOKEN"]

r = requests.get(
    "https://api.datawrapper.de/v3/me",
    headers={"Authorization": f"Bearer {DW_TOKEN}"}
)
print(r.status_code)
print(r.json())
