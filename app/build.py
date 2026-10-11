#!/usr/bin/env python3
"""Baut die Daten der App „TKLST Reisen-Concierge“ aus dem Repo.

- Exposés (reiseplanung/dossiers/<slug>.html/.pdf) → app/public/expose/
- Reise-Übersicht (reiseplanung/trips/*.json) → app/public/data/trips.json
- Favoriten (reiseplanung/GEDAECHTNIS.md) → app/public/data/favoriten.json
- Icons → app/public/icons/

Aufruf (nach jedem neuen Exposé): python3 app/build.py
"""
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "app" / "public"
TRIPS = ROOT / "reiseplanung" / "trips"
DOSS = ROOT / "reiseplanung" / "dossiers"
MEM = ROOT / "reiseplanung" / "GEDAECHTNIS.md"

EXPOSE_WRAP = """<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#FBFAF4"><link rel="apple-touch-icon" href="/icons/apple-touch-icon.png">
<style>:root{{color-scheme:light}} .back{{position:sticky;top:0;z-index:5;display:flex;gap:12px;align-items:center;
padding:calc(env(safe-area-inset-top,0px) + 10px) 16px 10px;background:#FBFAF4;border-bottom:1px solid #E6E0D3;
font:600 15px "Helvetica Neue",Helvetica,Arial,sans-serif}} .back a{{color:#6F6A52;text-decoration:none}}</style>
</head><body><nav class="back"><a href="/">‹ Alle Reisen</a><a href="/expose/{slug}.pdf" style="margin-left:auto">PDF</a></nav>
{body}</body></html>"""


def build_expose():
    out = PUB / "expose"
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("*"):
        f.unlink()
    for html in DOSS.glob("*.html"):
        if html.name.endswith("-print.html"):
            continue
        slug = html.stem
        (out / f"{slug}.html").write_text(EXPOSE_WRAP.format(slug=slug, body=html.read_text(encoding="utf-8")), encoding="utf-8")
        pdf = DOSS / f"{slug}.pdf"
        if pdf.exists():
            shutil.copy(pdf, out / pdf.name)


def build_trips():
    trips = []
    for f in sorted(TRIPS.glob("*.json")):
        t = json.loads(f.read_text(encoding="utf-8"))
        m = t["meta"]
        if not (DOSS / f"{m['slug']}.html").exists():
            continue
        rec = t.get("recommendation", {})
        hotel = next((h for h in t.get("hotels", []) if h["id"] == rec.get("hotel")), None)
        trips.append({
            "slug": m["slug"], "title": m["title"], "route": m.get("route", ""), "dates": m["dates"],
            "start": m.get("start", ""), "end": m.get("end", ""), "travellers": m.get("travellers", ""),
            "status": m.get("status", ""), "headline": rec.get("headline", ""), "todo": t.get("todo", []),
            "hotel": hotel["name"] if hotel else "",
            "days": [{"label": d["label"], "date": d["date"], "items": d["items"]} for d in t.get("days", [])],
            "pdf": (DOSS / f"{m['slug']}.pdf").exists(), "archiv": bool(m.get("archiv")),
        })
    trips.sort(key=lambda x: x["start"], reverse=True)
    (PUB / "data").mkdir(parents=True, exist_ok=True)
    (PUB / "data" / "trips.json").write_text(json.dumps(trips, ensure_ascii=False, indent=1), encoding="utf-8")
    return len(trips)


def table_rows(md, heading):
    m = re.search(rf"## {re.escape(heading)}[^\n]*\n(.*?)(?=\n## |\Z)", md, re.S)
    if not m:
        return []
    rows = [r for r in m.group(1).splitlines() if r.startswith("|")][2:]
    cells = [[c.strip().replace("**", "") for c in r.strip("|").split("|")] for r in rows]
    return [c for c in cells if c and c[0] not in ("–", "")]


def build_favs():
    md = MEM.read_text(encoding="utf-8")
    favs = {
        "hotels": [{"stadt": r[0], "name": r[1], "warum": r[2]} for r in table_rows(md, "Lieblingshotels")],
        "orte": [{"stadt": r[0], "name": r[1], "typ": r[2], "warum": r[3]} for r in table_rows(md, "Lieblingsrestaurants")],
        "nogos": [{"was": r[0], "warum": r[1]} for r in table_rows(md, "No-Gos")],
    }
    (PUB / "data" / "favoriten.json").write_text(json.dumps(favs, ensure_ascii=False, indent=1), encoding="utf-8")


def build_icons():
    icons = PUB / "icons"
    if (icons / "icon-512.png").exists():
        return
    from PIL import Image, ImageDraw, ImageFont
    icons.mkdir(parents=True, exist_ok=True)
    font_path = next((p for p in ["/usr/share/fonts/opentype/inter/Inter-Bold.otf",
                                  "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"] if Path(p).exists()), None)
    for size, name in [(512, "icon-512.png"), (192, "icon-192.png"), (180, "apple-touch-icon.png")]:
        img = Image.new("RGB", (size, size), "#F4F3E7")
        d = ImageDraw.Draw(img)
        r = int(size * 0.30)
        cx, cy = size // 2, int(size * 0.44)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#C3C88A")
        font = ImageFont.truetype(font_path, int(size * 0.24)) if font_path else ImageFont.load_default()
        d.text((cx, cy), "TK", fill="#1C1C1A", font=font, anchor="mm")
        small = ImageFont.truetype(font_path, int(size * 0.085)) if font_path else ImageFont.load_default()
        d.text((cx, int(size * 0.86)), "REISEN", fill="#6F6A52", font=small, anchor="mm")
        img.save(icons / name)


if __name__ == "__main__":
    build_expose()
    n = build_trips()
    build_favs()
    build_icons()
    print(f"App-Daten gebaut: {n} Reisen, Favoriten, Icons → {PUB}")
