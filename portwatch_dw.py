import requests
import pandas as pd
import time
import os
from datetime import datetime, timedelta

DW_TOKEN = os.environ["DW_TOKEN"]
DW_BASE = "https://api.datawrapper.de/v3"
DW_HEADERS = {"Authorization": f"Bearer {DW_TOKEN}", "Content-Type": "application/json"}
ARCGIS = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/ArcGIS/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"
COORDS = {"Suez Canal": (30.42, 32.35), "Strait of Hormuz": (26.56, 56.25), "Strait of Malacca": (1.25, 103.50), "Bab-el-Mandeb": (12.58, 43.38), "Turkish Straits": (41.12, 29.08), "Danish Straits": (55.80, 10.60), "Dover Strait": (51.02, 1.35), "Panama Canal": (9.08, -79.68), "Lombok Strait": (-8.75, 115.75), "Strait of Gibraltar": (35.97, -5.45), "Mozambique Channel": (-17.0, 40.0), "Cape of Good Hope": (-34.36, 18.48), "Cape Horn": (-55.98, -67.27), "Sunda Strait": (-6.00, 105.87), "Luzon Strait": (20.00, 121.50), "Taiwan Strait": (24.50, 119.50), "Korea Strait": (34.50, 129.00), "Tsugaru Strait": (41.50, 140.50), "Oresund": (55.98, 12.62), "St. Lawrence Seaway": (46.50, -71.00), "Yucatan Channel": (21.50, -85.50), "Florida Strait": (24.50, -80.50), "Windward Passage": (20.00, -74.00), "Mona Passage": (18.50, -67.50), "Messina Strait": (38.25, 15.65), "Otranto Strait": (40.00, 18.50), "Sicily Channel": (37.30, 11.30), "Northwest Passage": (74.00, -100.00)}

def fetch_chokepoints(days=360):
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    records = []
    offset = 0
    while True:
        p = {"where": f"date >= DATE '{cutoff}'", "outFields": "date,portname,portid,n_total,n_container,n_tanker", "resultOffset": offset, "resultRecordCount": 2000, "orderByFields": "date", "f": "json"}
        r = requests.get(ARCGIS, params=p).json()
        features = r.get("features", [])
        if not features:
            break
        records.extend(f["attributes"] for f in features)
        offset += 2000
        time.sleep(0.3)
        print(f"  {len(records)} record...")
    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    return df

def create_chart(portname):
    r = requests.post(f"{DW_BASE}/charts", headers=DW_HEADERS, json={"title": f"{portname} - Transiti giornalieri", "type": "d3-lines", "metadata": {"describe": {"intro": f"Navi in transito per {portname}. Fonte: IMF PortWatch."}}})
    r.raise_for_status()
    return r.json()["id"]

def upload_data(cid, df):
    r = requests.put(f"{DW_BASE}/charts/{cid}/data", headers={**DW_HEADERS, "Content-Type": "text/csv"}, data=df.to_csv(index=False).encode("utf-8"))
    r.raise_for_status()

def publish_chart(cid):
    r = requests.post(f"{DW_BASE}/charts/{cid}/publish", headers=DW_HEADERS)
    r.raise_for_status()

def get_embed(cid):
    return f'<iframe src="https://datawrapper.dwcdn.net/{cid}/1/" width="600" height="400" frameborder="0"></iframe>'

print("1. Scarico dati PortWatch (360 giorni)...")
df = fetch_chokepoints(days=360)
print(f"   {len(df)} record, {df['portname'].nunique()} chokepoint")

print("2. Creo chart per ogni chokepoint...")
results = []
for portname in df["portname"].unique():
    df_port = df[df["portname"] == portname][["date", "n_total", "n_container", "n_tanker"]].sort_values("date").copy()
    df_port.columns = ["Data", "Totale navi", "Container", "Petroliere"]
    cid = create_chart(portname)
    upload_data(cid, df_port)
    publish_chart(cid)
    coords = COORDS.get(portname, (None, None))
    results.append({"name": portname, "lat": coords[0], "lon": coords[1], "avg_daily": round(df_port["Totale navi"].mean(), 1), "embed": get_embed(cid), "chart_id": cid})
    print(f"   ok {portname} -> {cid}")
    time.sleep(1)

df_out = pd.DataFrame(results)
df_out.to_csv("chokepoints_flourish.csv", index=False)
print("3. CSV salvato!")
print(df_out[["name", "lat", "lon", "avg_daily", "chart_id"]].to_string())
