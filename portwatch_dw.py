import requests
import pandas as pd
import time
import os
from datetime import datetime, timedelta

DW_TOKEN = os.environ["DW_TOKEN"]
DW_BASE = "https://api.datawrapper.de/v3"
DW_HEADERS = {
    "Authorization": f"Bearer {DW_TOKEN}",
    "Content-Type": "application/json"
}

ARCGIS = (
    "https://services9.arcgis.com/weJ1QsnbMYJlCHdG"
    "/ArcGIS/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"
)

CHOKEPOINT_COORDS = {
    "Suez Canal":            (30.42,  32.35),
    "Strait of Hormuz":      (26.56,  56.25),
    "Strait of Malacca":     ( 1.25, 103.50),
    "Bab-el-Mandeb":         (12.58,  43.38),
    "Turkish Straits":       (41.12,  29.08),
    "Danish Straits":        (55.80,  10.60),
    "Dover Strait":          (51.02,   1.35),
    "Panama Canal":          ( 9.08, -79.68),
    "Lombok Strait":         (-8.75, 115.75),
    "Strait of Gibraltar":   (35.97,  -5.45),
    "Mozambique Channel":    (-17.0,   40.0),
    "Cape of Good Hope":     (-34.36,  18.48),
    "Cape Horn":             (-55.98, -67.27),
    "Sunda Strait":          (-6.00, 105.87),
    "Luzon Strait":          (20.00, 121.50),
    "Taiwan Strait":         (24.50, 119.50),
    "Korea Strait":          (34.50, 129.00),
    "Tsugaru Strait":        (41.50, 140.50),
    "Øresund":               (55.98,  12.62),
    "St. Lawrence Seaway":   (46.50, -71.00),
    "Yucatan Channel":       (21.50, -85.50),
    "Florida Strait":        (24.50, -80.50),
    "Windward Passage":      (20.00, -74.00),
    "Mona Passage":          (18.50, -67.50),
    "Messina Strait":        (38.25,  15.65),
    "Otranto Strait":        (40.00,  18.50),
    "Sicily Channel":        (37.30,
