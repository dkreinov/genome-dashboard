# -*- coding: utf-8 -*-
"""Capture README section screenshots from the synthetic example dashboard (Playwright).
Uses precise h2.sec heading locators (not body text) + an element screenshot for Facial."""
import os
from playwright.sync_api import sync_playwright
from PIL import Image

HERE = os.path.dirname(__file__)
URL = "file:///" + os.path.abspath(os.path.join(HERE, "..", "examples", "example_dashboard.html")).replace("\\", "/")
FULL = os.path.join(HERE, "_full.png")

# crop-from-heading targets: (out, h2 text, crop height)
CROPS = [
    ("shot_risk.png",    "Polygenic risk", 800),
    ("shot_meds.png",    "Medications",    800),
    ("shot_carrier.png", "Carrier",        560),
    ("shot_traits.png",  "Health",         720),
]

def launch(p):
    try: return p.chromium.launch()
    except Exception: return p.chromium.launch(channel="chrome")

with sync_playwright() as p:
    b = launch(p)
    pg = b.new_page(viewport={"width": 1180, "height": 1400}, device_scale_factor=1)
    pg.goto(URL, wait_until="networkidle"); pg.wait_for_timeout(800)
    pg.screenshot(path=FULL, full_page=True)
    full = Image.open(FULL); W, H = full.size
    print("full page:", full.size)
    for out, text, h in CROPS:
        try:
            box = pg.locator("h2.sec", has_text=text).first.bounding_box()
            y = max(0, min(int(box["y"]) - 22, H - h))
            full.crop((0, y, W, min(H, y + h))).save(os.path.join(HERE, out))
            print("saved", out, "y=", y)
        except Exception as e:
            print("FAILED", out, repr(e)[:80])
    # Facial section as a direct element screenshot (whole catsec, ~5 cards)
    try:
        pg.locator("section.catsec", has_text="Nasal-root depth").first.screenshot(
            path=os.path.join(HERE, "shot_facial.png"))
        print("saved shot_facial.png (element)")
    except Exception as e:
        print("FAILED facial", repr(e)[:80])
    b.close()
