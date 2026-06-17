import requests
import pandas as pd
import os

ARCGIS = (
    "https://services9.arcgis.com/weJ1QsnbMYJlCHdG"
    "/ArcGIS/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"
)

# Prima chiamata: solo 5 record senza filtri
p = {
    "where": "1=1",
    "outFields": "*",
    "resultRecordCount": 5,
    "f": "json"
}

print("Chiamo API...")
r = requests.get(ARCGIS, params=p)
print("Status:", r.status_code)
data = r.json()
print("Risposta:", data)
