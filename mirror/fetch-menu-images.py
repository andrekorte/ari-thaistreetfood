#!/usr/bin/env python3
"""Download square Clover item photos listed in menu-data.json."""
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
DEST = os.path.join(HERE, "wp-content", "uploads", "menu")
os.makedirs(DEST, exist_ok=True)

data = json.load(open(os.path.join(HERE, "menu-data.json")))
ids = [i["id"] for c in data["categories"] for i in c["items"] if i["id"]]
print(len(ids), "photos to fetch")

fail = 0
for iid in ids:
    out = os.path.join(DEST, iid + ".jpg")
    if os.path.exists(out):
        continue
    url = f"https://ap.cloverstatic.com/menu-assets/items/{iid}_576x576.jpeg"
    code = subprocess.run(
        ["curl", "-sL", "-w", "%{http_code}", "-o", out, url],
        capture_output=True, text=True,
    ).stdout
    if code != "200":
        print("FAIL", code, iid)
        os.remove(out)
        fail += 1
print("done, failures:", fail)
