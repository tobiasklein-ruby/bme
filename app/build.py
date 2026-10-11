#!/usr/bin/env python3
"""Baut die Daten der App „TKLST Reisen-Concierge“ aus dem Repo.

Jede Person bekommt einen eigenen Ordner app/public/u/<name>/ – nur mit den Reisen,
die laut meta.sichtbar für sie freigegeben sind. Die Middleware leitet /me/… auf den
eigenen Ordner um und sperrt fremde Ordner (Server-seitig, nicht nur ausgeblendet).

- Exposés → u/<name>/expose/, Reise-Übersicht → u/<name>/data/trips.json
- Rückfragen → u/<name>/data/rueckfragen.json (nur an diese Person gerichtete)
- Favoriten (gemeinsam, aus GEDAECHTNIS.md) → u/<name>/data/favoriten.json
- Icons → app/public/icons/

Aufruf (nach jedem neuen Exposé): python3 app/build.py
"""
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "app" / "public"
USERS = ["Toby", "Laura"]
TRIPS = ROOT / "reiseplanung" / "trips"
DOSS = ROOT / "reiseplanung" / "dossiers"
MEM = ROOT / "reiseplanung" / "GEDAECHTNIS.md"

EXPOSE_WRAP = """<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#FBFAF4"><link rel="apple-touch-icon" href="/icons/apple-touch-icon.png">
<style>:root{{color-scheme:light}} .back{{position:sticky;top:0;z-index:5;display:flex;gap:12px;align-items:center;
padding:calc(env(safe-area-inset-top,0px) + 10px) 16px 10px;background:#FBFAF4;border-bottom:1px solid #E6E0D3;
font:600 15px "Helvetica Neue",Helvetica,Arial,sans-serif}} .back a{{color:#6F6A52;text-decoration:none}}</style>
</head><body><nav class="back"><a href="/">‹ Alle Reisen</a><a href="/me/expose/{slug}.pdf" style="margin-left:auto">PDF</a></nav>
{body}</body></html>"""


def visible(meta):
    vis = meta.get("sichtbar")
    if not vis:
        raise SystemExit(f"meta.sichtbar fehlt in {meta['slug']} – bitte [\"Toby\"], [\"Laura\"] oder beide eintragen.")
    return [u for u in USERS if u in vis]


def udir(user):
    return PUB / "u" / user.lower()


def build_expose(trip_files):
    for meta in trip_files:
        slug = meta["slug"]
        html = DOSS / f"{slug}.html"
        for user in visible(meta):
            out = udir(user) / "expose"
            out.mkdir(parents=True, exist_ok=True)
            (out / f"{slug}.html").write_text(EXPOSE_WRAP.format(slug=slug, body=html.read_text(encoding="utf-8")), encoding="utf-8")
            pdf = DOSS / f"{slug}.pdf"
            if pdf.exists():
                shutil.copy(pdf, out / pdf.name)


def load_trips():
    out = []
    for f in sorted(TRIPS.glob("*.json")):
        t = json.loads(f.read_text(encoding="utf-8"))
        if (DOSS / f"{t['meta']['slug']}.html").exists():
            out.append(t)
    return out


def build_trips(all_trips):
    per_user = {u: [] for u in USERS}
    for t in all_trips:
        m = t["meta"]
        rec = t.get("recommendation", {})
        hotel = next((h for h in t.get("hotels", []) if h["id"] == rec.get("hotel")), None)
        entry = {
            "slug": m["slug"], "title": m["title"], "route": m.get("route", ""), "dates": m["dates"],
            "start": m.get("start", ""), "end": m.get("end", ""), "travellers": m.get("travellers", ""),
            "status": m.get("status", ""), "headline": rec.get("headline", ""), "todo": t.get("todo", []),
            "hotel": hotel["name"] if hotel else "",
            "days": [{"label": d["label"], "date": d["date"], "items": d["items"]} for d in t.get("days", [])],
            "pdf": (DOSS / f"{m['slug']}.pdf").exists(), "archiv": bool(m.get("archiv")),
            "gemeinsam": len(visible(m)) > 1,
        }
        for user in visible(m):
            per_user[user].append(entry)
    for user, trips in per_user.items():
        trips.sort(key=lambda x: x["start"], reverse=True)
        d = udir(user) / "data"
        d.mkdir(parents=True, exist_ok=True)
        (d / "trips.json").write_text(json.dumps(trips, ensure_ascii=False, indent=1), encoding="utf-8")
        (d / "profil.json").write_text(json.dumps({"name": user}, ensure_ascii=False), encoding="utf-8")
    return {u: len(t) for u, t in per_user.items()}


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
    for user in USERS:
        (udir(user) / "data").mkdir(parents=True, exist_ok=True)
        (udir(user) / "data" / "favoriten.json").write_text(json.dumps(favs, ensure_ascii=False, indent=1), encoding="utf-8")


def build_rueckfragen():
    src = ROOT / "reiseplanung" / "RUECKFRAGEN.json"
    items = json.loads(src.read_text(encoding="utf-8")) if src.exists() else []
    for user in USERS:
        offen = [{k: q.get(k) for k in ("id", "von", "frage", "optionen")} for q in items
                 if q.get("status") == "offen" and q.get("von") == user]
        (udir(user) / "data" / "rueckfragen.json").write_text(json.dumps(offen, ensure_ascii=False, indent=1), encoding="utf-8")


def build_icons():
    icons = PUB / "icons"
    if (icons / "icon-512.png").exists() and (icons / ".v2").exists():
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
        font = ImageFont.truetype(font_path, int(size * 0.135)) if font_path else ImageFont.load_default()
        d.text((cx, cy), "TKLST", fill="#1C1C1A", font=font, anchor="mm")
        small = ImageFont.truetype(font_path, int(size * 0.085)) if font_path else ImageFont.load_default()
        d.text((cx, int(size * 0.86)), "REISEN", fill="#6F6A52", font=small, anchor="mm")
        img.save(icons / name)
    (icons / ".v2").write_text("TKLST")


if __name__ == "__main__":
    shutil.rmtree(PUB / "u", ignore_errors=True)
    trips = load_trips()
    build_expose([t["meta"] for t in trips])
    n = build_trips(trips)
    build_favs()
    build_rueckfragen()
    build_icons()
    print(f"App-Daten gebaut: Reisen je Person {n}, Favoriten, Rückfragen, Icons → {PUB}")
