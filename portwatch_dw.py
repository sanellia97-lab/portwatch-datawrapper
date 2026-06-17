import requests
import pandas as pd
import time
import os
from datetime import datetime, timedelta

ARCGIS = (
    "https://services9.arcgis.com/weJ1QsnbMYJlCHdG"
    "/ArcGIS/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"
)

def fetch_chokepoints(days=7):
    cutoff = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
    records = []
    offset = 0
    while True:
        p = {
            "where": f"date >= {cutoff}",
            "outFields": "*",
            "resultOffset": offset,
            "resultRecordCount": 2000,
            "orderByFields": "date",
            "f": "json"
        }
        r = requests.get(ARCGIS, params=p).json()
        features = r.get("features", [])
        if not features:
            break
        records.extend(f["attributes"] for f in features)
        offset += 2000
        time.sleep(0.3)
    df = pd.DataFrame(records)
    print("COLONNE:", df.columns.tolist())
    print(df.head(3).to_string())
    return df

print("Scarico dati PortWatch (7 giorni)...")
df = fetch_chokepoints(days=7)
print(f"Totale record: {len(df)}") 
