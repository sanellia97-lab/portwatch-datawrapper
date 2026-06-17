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
NOMI_IT = {"Suez Canal": "Canale di Suez", "Strait of Hormuz": "Stretto di Hormuz", "Strait of Malacca": "Stretto di Malacca", "Bab-el-Mandeb": "Stretto di Bab-el-Mandeb", "Turkish Straits": "Stretti turchi (Bosforo/Dardanelli)", "Danish Straits": "Stretti danesi", "Dover Strait": "Stretto di Dover", "Panama Canal": "Canale di Panama", "Lombok Strait": "Stretto di Lombok", "Strait of Gibraltar": "Stretto di Gibilterra", "Mozambique Channel": "Canale del Mozambico", "Cape of Good Hope": "Capo di Buona Speranza", "Cape Horn": "Capo Horn", "Sunda Strait": "Stretto della Sonda", "Luzon Strait": "Stretto di Luzon", "Taiwan Strait": "Stretto di Taiwan", "Korea Strait": "Stretto di Corea", "Tsugaru Strait": "Stretto di Tsugaru", "Oresund": "Stretto di Oresund", "St. Lawrence Seaway": "Via navigabile del San Lorenzo", "Yucatan Channel": "Canale dello Yucatan", "Florida Strait": "Stretto della Florida", "Windward Passage": "Passo di Sopravvento", "Mona Passage": "Passo di Mona", "Messina Strait": "Stretto di Messina", "Otranto Strait": "Stretto di Otranto", "Sicily Channel": "Canale di Sicilia", "Northwest Passage": "Passaggio a Nord-Ovest"}

def fetch_chokepoints(days=1825):
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    records = []
    offset = 0
    while True:
        p = {"where": f"date >= DATE '{cutoff}'", "outFields": "date,portname,n_total", "resultOffset": offset, "resultRecordCount": 2000, "orderByFields": "date", "f": "json"}
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
    nome_it = NOMI_IT.get(portname, portname)
    r = requests.post(f"{DW_BASE}/charts", headers=DW_HEADERS, json={
        "title": f"I passaggi negli ultimi 5 anni — {nome_it}",
        "type": "column-chart",
        "metadata": {
            "describe": {
                "intro": "Totale mensile dei transiti. Fonte: IMF PortWatch."
            },
            "visualize": {
                "x-grid": "off",
                "y-grid": "on"
            }
        }
    })
    r.raise_for_status()
    return r.json()["id"]

def upload_data(cid, df):
    r = requests.put(f"{DW_BASE}/charts/{cid}/data", headers={**DW_HEADERS, "Content-Type": "text/csv"}, data=df.to_csv(index=False).encode("utf-8"))
    r.raise_for_status()

def publish_chart(cid):
    r = requests.post(f"{DW_BASE}/charts/{cid}/publish", headers=DW_HEADERS)
    if r.status_code != 200:
        print(f"   (publish skippato: {r.status_code})")

def get_embed(cid):
    return f'<iframe src="https://datawrapper.dwcdn.net/{cid}/1/" width="600" height="400" frameborder="0"></iframe>'

print("1. Scarico dati PortWatch (5 anni)...")
df = fetch_chokepoints(days=1825)
print(f"   {len(df)} record, {df['portname'].nunique()} chokepoint")

print("2. Aggrego per mese...")
df["mese"] = df["date"].dt.to_period("M").dt.to_timestamp()
df_monthly = df.groupby(["portname", "mese"])["n_total"].sum().reset_index()
df_monthly.columns = ["portname", "mese", "n_total"]

print("3. Creo chart per ogni chokepoint...")
results = []
for portname in df_monthly["portname"].unique():
    df_port = df_monthly[df_monthly["portname"] == portname][["mese", "n_total"]].sort_values("mese").copy()
    df_port.columns = ["Mese", "Transiti totali"]
    nome_it = NOMI_IT.get(portname, portname)
    cid = create_chart(portname)
    upload_data(cid, df_port)
    publish_chart(cid)
    coords = COORDS.get(portname, (None, None))
    results.append({"name": portname, "name_it": nome_it, "lat": coords[0], "lon": coords[1], "avg_monthly": round(df_port["Transiti totali"].mean(), 0), "embed": get_embed(cid), "chart_id": cid})
    print(f"   ok {nome_it} -> {cid}")
    time.sleep(1)

df_final = pd.DataFrame(results)
df_final.to_csv("chokepoints_flourish.csv", index=False)
print("4. CSV per Flourish salvato!")
print(df_final[["name_it", "lat", "lon", "avg_monthly", "chart_id"]].to_string())
