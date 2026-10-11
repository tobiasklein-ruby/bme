#!/usr/bin/env python3
"""Baut aus einer Reise-JSON (reiseplanung/trips/*.json) das Entscheidungs-Exposé.

Alle Summen, Differenzen und Balkenlängen werden hier berechnet, nie von Hand.
Ausgabe: <slug>.html (Fragment fürs Web-Artifact), <slug>-print.html und <slug>.pdf.

Aufruf: python3 reiseplanung/tool/build_dossier.py reiseplanung/trips/2026-10-berlin.json
"""
import html
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dossiers"
CONF = {"gruen": ("live/primär", "c-g"), "gelb": ("belegt, nicht live", "c-y"), "rot": ("Schätzung", "c-r")}


def e(s):
    return html.escape(str(s))


def eur(v):
    return f"{round(v):,}".replace(",", ".") + " €"


def eur_range(lo, hi):
    if hi >= 100:
        lo, hi = round(lo / 10) * 10, round(hi / 10) * 10
    lo, hi = round(lo), round(hi)
    return eur(lo) if lo == hi else f"{lo:,}–{hi:,} €".replace(",", ".")


def hours(v):
    return f"{v:.1f}".replace(".", ",").replace(",0", "") + " h"


def signed(v, unit):
    if abs(v) < 0.05:
        return "gleich"
    sign = "+" if v > 0 else "−"
    num = eur(abs(v)) if unit == "€" else hours(abs(v))
    return sign + num


def dot(conf):
    label, cls = CONF[conf]
    return f'<span class="dot {cls}" title="{e(label)}"></span>'


def compute(trip):
    hotels = {h["id"]: h for h in trip["hotels"]}
    rec_hotel = hotels[trip["recommendation"]["hotel"]]
    n = trip["meta"]["nights"]
    hotel_lo, hotel_hi = rec_hotel["night"][0] * n, rec_hotel["night"][1] * n
    for o in trip["options"]:
        o["travel_lo"] = sum(c["min"] for c in o["costs"])
        o["travel_hi"] = sum(c["max"] for c in o["costs"])
        o["total_lo"] = o["travel_lo"] + hotel_lo
        o["total_hi"] = o["travel_hi"] + hotel_hi
        o["total_mid"] = (o["total_lo"] + o["total_hi"]) / 2
        o["door_mid"] = sum(o["door_h"]) / 2
        o["lost_h"] = max(o["door_mid"] - o["work_h"], 0)
    rec = next(o for o in trip["options"] if o["id"] == trip["recommendation"]["option"])
    for o in trip["options"]:
        o["d_eur"] = o["total_mid"] - rec["total_mid"]
        o["d_door"] = o["door_mid"] - rec["door_mid"]
        o["d_lost"] = o["lost_h"] - rec["lost_h"]
        o["rec"] = o is rec
    for h in trip["hotels"]:
        h["lo"], h["hi"] = h["night"][0] * n, h["night"][1] * n
        h["d"] = (h["lo"] + h["hi"]) / 2 - (hotel_lo + hotel_hi) / 2
        h["rec"] = h is rec_hotel
    return rec, rec_hotel, (hotel_lo, hotel_hi)


def bars_cost(options):
    top = max(o["total_hi"] for o in options) * 1.08
    rows, y = [], 8
    for o in options:
        x0 = 120 + o["total_lo"] / top * 360
        x1 = 120 + o["total_hi"] / top * 360
        xm = 120 + o["total_mid"] / top * 360
        cls = "b-rec" if o["rec"] else "b-alt"
        rows.append(
            f'<text x="0" y="{y+15}" class="lbl">{e(o["id"])} · {e(o["name"])}</text>'
            f'<rect x="120" y="{y+4}" width="{xm-120:.1f}" height="16" rx="3" class="{cls}"/>'
            f'<line x1="{x0:.1f}" x2="{x1:.1f}" y1="{y+12}" y2="{y+12}" class="whisk"/>'
            f'<text x="{x1+8:.1f}" y="{y+16}" class="val">{e(eur_range(o["total_lo"], o["total_hi"]))}</text>'
        )
        y += 34
    return f'<svg viewBox="0 0 680 {y}" class="chart" role="img" aria-label="Gesamtkosten je Option">{"".join(rows)}</svg>'


def bars_time(options, use_word="Arbeit"):
    top = max(o["door_mid"] for o in options) * 1.05
    rows, y = [], 8
    for o in options:
        wl = o["work_h"] / top * 360
        tl = o["door_mid"] / top * 360
        rows.append(
            f'<text x="0" y="{y+15}" class="lbl">{e(o["id"])} · {e(o["name"])}</text>'
            f'<rect x="120" y="{y+4}" width="{tl:.1f}" height="16" rx="3" class="b-lost"/>'
            + (f'<rect x="120" y="{y+4}" width="{wl:.1f}" height="16" rx="3" class="b-work"/>' if wl > 0 else "")
            + f'<text x="{120+tl+8:.1f}" y="{y+16}" class="val">{e(hours(o["door_mid"]))} · davon {e(hours(o["work_h"]))} {e(use_word)}</text>'
        )
        y += 34
    return f'<svg viewBox="0 0 680 {y}" class="chart" role="img" aria-label="Reisezeit und Arbeitszeit je Option">{"".join(rows)}</svg>'


def render(trip):
    m = trip["meta"]
    use_label = m.get("use_label", "Arbeitszeit")
    use_word = m.get("use_word", "Arbeit")
    lost_note = m.get("lost_note", "„Verlorene Zeit“ ist die Reisezeit, in der du nicht arbeiten kannst.")
    rec, rec_hotel, hotel_rng = compute(trip)
    opts = trip["options"]

    cards = []
    for o in opts:
        chips = "" if o["rec"] else (
            f'<div class="chips"><span class="chip">{e(signed(o["d_eur"], "€"))}</span>'
            f'<span class="chip">{e(signed(o["d_door"], "h"))} unterwegs</span>'
            f'<span class="chip">{e(signed(o["d_lost"], "h"))} verlorene Zeit</span></div>'
        )
        badge = '<span class="pill">Empfehlung</span>' if o["rec"] else f'<span class="pill ghost">Option {e(o["id"])}</span>'
        cards.append(f'''
<article class="opt{' rec' if o['rec'] else ''}">
  {badge}
  <h3>{e(o['name'])}</h3>
  <p class="sub">{e(o['detail'])}</p>
  <div class="big">{e(eur_range(o['total_lo'], o['total_hi']))}</div>
  <p class="cap">gesamt inkl. {m['nights']} Nächte {e(rec_hotel['name'])}</p>
  <dl>
    <div><dt>Tür zu Tür</dt><dd>{e(hours(o['door_mid']))}</dd></div>
    <div><dt>{e(use_label)}</dt><dd>{e(hours(o['work_h']))}</dd></div>
    <div><dt>Verlorene Zeit</dt><dd>{e(hours(o['lost_h']))}</dd></div>
  </dl>
  {chips}
  <ul class="pm">{''.join(f'<li class="p">{e(x)}</li>' for x in o['plus'])}{''.join(f'<li class="m">{e(x)}</li>' for x in o['minus'])}</ul>
</article>''')

    hotel_cards = []
    for h in trip["hotels"]:
        tag = "Empfehlung" if h["rec"] else ("Top-Haus" if h.get("top") else signed(h["d"], "€"))
        hotel_cards.append(f'''
<article class="hotel{' rec' if h['rec'] else ''}">
  <div class="hrow"><h4>{e(h['name'])}</h4><span class="pill{'' if h['rec'] else ' ghost'}">{e(tag)}</span></div>
  <p class="sub">{e(h['style'])} · {e(h['where'])}</p>
  <div class="hnum"><b>{e(eur_range(h['lo'], h['hi']))}</b><span>{m['nights']} Nächte · Bewertung {e(h['rating'])} {dot(h['conf'])}</span></div>
  <p class="pmline"><span class="p">{e(h['plus'])}</span><span class="m">{e(h['minus'])}</span></p>
</article>''')

    cost_rows = "".join(
        f'<tr><td>{e(c["label"])}</td><td class="num">{e(eur_range(c["min"], c["max"]))}</td><td>{dot(c["conf"])}</td></tr>'
        for c in rec["costs"]
    )
    cost_rows += f'<tr><td>{m["nights"]} Nächte {e(rec_hotel["name"])}</td><td class="num">{e(eur_range(*hotel_rng))}</td><td>{dot(rec_hotel["conf"])}</td></tr>'
    cost_rows += f'<tr class="sum"><td>Summe für {e(m["payer"])}</td><td class="num">{e(eur_range(rec["total_lo"], rec["total_hi"]))}</td><td></td></tr>'

    save_rows = "".join(
        f'<tr><td>{e(s["label"])}</td><td class="num save">−{e(eur_range(*s["save"]))}</td><td class="muted">{e(s["tradeoff"])}</td></tr>'
        for s in trip["savings"]
    )

    days = "".join(
        f'''<div class="dcol"><h4>{e(d['label'])} <span>{e(d['date'])} · {e(d['theme'])}</span></h4><ol>'''
        + "".join(f'<li class="{"fix" if i["fix"] else ""}"><time>{e(i["t"])}</time><span>{e(i["what"])}</span></li>' for i in d["items"])
        + "</ol></div>"
        for d in trip["days"]
    )

    eves = "".join(
        f'<div class="eve"><h4>{e(ev["day"])}abend</h4><div class="picks">'
        + "".join(
            f'<a class="pick{" on" if p.get("pick") else ""}" href="{e(p["link"])}"><span class="lvl">{e(p["level"])}</span>'
            f'<b>{e(p["name"])}</b><span>{e(p["food"])}</span><span class="pr">{e(p["price"])} p. P.</span></a>'
            for p in ev["picks"])
        + "</div></div>"
        for ev in trip["evenings"]
    )

    facts = "".join(f'<div><dt>{e(f["label"])}</dt><dd>{e(f["value"])}</dd></div>' for f in trip["facts"])
    srcs = "".join(f'<tr><td>{dot(s["conf"])}</td><td>{e(s["what"])}</td><td class="muted">{e(s["src"])}</td></tr>' for s in trip["sources"])
    todo = "".join(f'<li><span class="box" aria-hidden="true"></span>{e(t)}</li>' for t in trip["todo"])
    why = "".join(f"<li>{e(w)}</li>" for w in trip["recommendation"]["why"])

    return f'''<title>Exposé {e(m['title'])}</title>
<style>
/* Layout: Entscheidungs-Exposé – Seite 1 Entscheidung (Optionen A/B/C), Seite 2 Kosten, Seite 3 Ablauf, Seite 4 Abende, Seite 5 Daten. Ruby-CI hell. */
:root {{
  --bg: #FBFAF4; --paper: #FFFFFF; --soft: #F4F3E7; --line: #E6E0D3;
  --fg: #1C1C1A; --muted: #6E6A5E; --olive: #6F6A52; --ruby: #C3C88A; --ruby-soft: #EEF0DA;
  --good: #3F7A4A; --mid: #B07A1C; --bad: #B0462F;
  --font: "Helvetica Neue", Helvetica, Inter, Arial, sans-serif;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg: #181818; --paper: #202020; --soft: #262624; --line: #3a3833; --fg: #F4F3E7; --muted: #b5b1a3;
  --olive: #C3C88A; --ruby: #C3C88A; --ruby-soft: #2b2d21; --good: #7fbf8a; --mid: #e0b060; --bad: #e88a73; color-scheme: dark; }} }}
:root[data-theme="dark"] {{
  --bg: #181818; --paper: #202020; --soft: #262624; --line: #3a3833; --fg: #F4F3E7; --muted: #b5b1a3;
  --olive: #C3C88A; --ruby: #C3C88A; --ruby-soft: #2b2d21; --good: #7fbf8a; --mid: #e0b060; --bad: #e88a73; color-scheme: dark; }}
* {{ box-sizing: border-box; }}
html {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
body {{ margin: 0; background: var(--bg); color: var(--fg); font-family: var(--font); font-size: 16px; line-height: 1.55; }}
.wrap {{ max-width: 1040px; margin: 0 auto; padding-inline: 24px; padding-block: 40px 72px; display: grid; gap: 72px; }}
h1, h2, h3, h4 {{ margin: 0; text-wrap: balance; }}
h1 {{ font-size: clamp(34px, 6vw, 56px); line-height: 1.04; letter-spacing: -0.025em; font-weight: 700; }}
h2 {{ font-size: 13px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--olive); font-weight: 700; }}
h3 {{ font-size: 24px; letter-spacing: -0.01em; }}
h4 {{ font-size: 17px; }}
p {{ margin: 0; }}
a {{ color: inherit; }}
a:focus-visible {{ outline: 2px solid var(--olive); outline-offset: 3px; }}
section {{ display: grid; gap: 24px; }}
.top {{ display: flex; justify-content: space-between; gap: 16px; flex-wrap: wrap; align-items: baseline; font-size: 12px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted); }}
.top b {{ color: var(--fg); letter-spacing: 0.16em; }}
.hero {{ display: grid; gap: 14px; }}
.meta {{ display: flex; flex-wrap: wrap; gap: 8px 22px; color: var(--muted); font-size: 15px; }}
.status {{ background: #F6E7D6; color: #8A5317; border-radius: 999px; padding: 2px 12px; font-size: 12px; font-weight: 600; }}
.verdict {{ background: var(--ruby-soft); border-radius: 18px; padding: 24px 28px; display: grid; gap: 10px; }}
.verdict p {{ font-size: 21px; font-weight: 600; letter-spacing: -0.01em; max-width: 46ch; }}
.verdict ul {{ margin: 0; padding-left: 20px; color: var(--muted); display: grid; gap: 4px; }}
.opts {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 20px; }}
.opt {{ background: var(--paper); border: 1px solid var(--line); border-radius: 18px; padding: 22px; display: grid; gap: 10px; align-content: start; min-width: 0; }}
.opt.rec {{ border: 2px solid var(--ruby); box-shadow: 0 6px 24px rgba(111,106,82,.12); }}
.pill {{ justify-self: start; background: var(--ruby); color: #1C1C1A; font-size: 11px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; border-radius: 999px; padding: 3px 10px; white-space: nowrap; }}
.pill.ghost {{ background: var(--soft); color: var(--muted); }}
.sub {{ color: var(--muted); font-size: 14px; }}
.big {{ font-size: 34px; font-weight: 700; letter-spacing: -0.02em; font-variant-numeric: tabular-nums; margin-top: 6px; }}
.cap {{ color: var(--muted); font-size: 12.5px; margin-top: -6px; }}
dl {{ margin: 0; display: grid; gap: 6px; }}
dl div {{ display: flex; justify-content: space-between; gap: 12px; border-top: 1px solid var(--line); padding-top: 6px; font-variant-numeric: tabular-nums; }}
dt {{ color: var(--muted); font-size: 14px; }}
dd {{ margin: 0; font-weight: 700; }}
.chips {{ display: flex; flex-wrap: wrap; gap: 6px; }}
.chip {{ background: var(--soft); border-radius: 999px; padding: 2px 10px; font-size: 12.5px; font-weight: 600; font-variant-numeric: tabular-nums; }}
.pm {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 4px; font-size: 14px; }}
.pm li::before {{ display: inline-block; width: 18px; font-weight: 700; }}
.pm .p::before {{ content: "+"; color: var(--good); }}
.pm .m::before {{ content: "–"; color: var(--bad); }}
.charts {{ display: grid; grid-template-columns: 1fr; gap: 28px; max-width: 780px; }}
.chartbox {{ display: grid; gap: 8px; min-width: 0; }}
.chartbox h4 {{ font-size: 14px; color: var(--muted); font-weight: 600; }}
.chart {{ width: 100%; height: auto; overflow: visible; }}
.chart .lbl {{ font-size: 13px; fill: var(--fg); font-weight: 600; }}
.chart .val {{ font-size: 12.5px; fill: var(--muted); font-variant-numeric: tabular-nums; }}
.chart .b-rec {{ fill: var(--ruby); }}
.chart .b-alt {{ fill: var(--line); }}
.chart .whisk {{ stroke: var(--olive); stroke-width: 2; }}
.chart .b-lost {{ fill: var(--line); }}
.chart .b-work {{ fill: var(--ruby); }}
.legend {{ display: flex; gap: 16px; font-size: 12.5px; color: var(--muted); flex-wrap: wrap; }}
.legend i {{ display: inline-block; width: 12px; height: 12px; border-radius: 3px; vertical-align: -1px; margin-right: 6px; }}
.todo {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 10px; font-size: 17px; }}
.todo li {{ display: flex; gap: 12px; align-items: baseline; }}
.box {{ width: 16px; height: 16px; border: 2px solid var(--olive); border-radius: 4px; flex: none; transform: translateY(2px); }}
.hotels {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }}
.hotel {{ background: var(--paper); border: 1px solid var(--line); border-radius: 16px; padding: 18px 20px; display: grid; gap: 6px; min-width: 0; }}
.hotel.rec {{ border: 2px solid var(--ruby); }}
.hrow {{ display: flex; justify-content: space-between; gap: 12px; align-items: center; }}
.hnum {{ display: flex; gap: 12px; align-items: baseline; flex-wrap: wrap; }}
.hnum b {{ font-size: 22px; font-variant-numeric: tabular-nums; }}
.hnum span {{ color: var(--muted); font-size: 13px; }}
.pmline {{ display: flex; gap: 16px; flex-wrap: wrap; font-size: 14px; }}
.pmline .p::before {{ content: "+ "; color: var(--good); font-weight: 700; }}
.pmline .m::before {{ content: "– "; color: var(--bad); font-weight: 700; }}
.two {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 32px; }}
.tbl {{ overflow-x: auto; }}
table {{ width: 100%; border-collapse: collapse; font-size: 15px; }}
td {{ padding: 10px 12px 10px 0; border-bottom: 1px solid var(--line); vertical-align: top; }}
td.num {{ text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; font-weight: 600; }}
td.save {{ color: var(--good); }}
tr.sum td {{ border-bottom: 0; font-weight: 700; font-size: 17px; padding-top: 14px; }}
.muted {{ color: var(--muted); font-size: 14px; }}
.dot {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%; vertical-align: 0; }}
.c-g {{ background: var(--good); }} .c-y {{ background: var(--mid); }} .c-r {{ background: var(--bad); }}
.days {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 28px; }}
.dcol {{ display: grid; gap: 12px; align-content: start; min-width: 0; }}
.dcol h4 span {{ display: block; font-size: 13px; color: var(--muted); font-weight: 500; }}
.dcol ol {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 2px; border-left: 2px solid var(--line); }}
.dcol li {{ display: grid; grid-template-columns: 52px 1fr; gap: 10px; padding: 7px 0 7px 14px; position: relative; }}
.dcol li::before {{ content: ""; position: absolute; left: -6px; top: 14px; width: 10px; height: 10px; border-radius: 50%; background: var(--bg); border: 2px solid var(--line); }}
.dcol li.fix::before {{ background: var(--ruby); border-color: var(--olive); }}
.dcol li.fix span {{ font-weight: 700; }}
.dcol time {{ font-variant-numeric: tabular-nums; color: var(--olive); font-weight: 700; }}
.eves {{ display: grid; gap: 28px; }}
.eve {{ display: grid; gap: 12px; }}
.picks {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }}
.pick {{ text-decoration: none; background: var(--paper); border: 1px solid var(--line); border-radius: 14px; padding: 16px 18px; display: grid; gap: 3px; min-width: 0; }}
.pick.on {{ border: 2px solid var(--ruby); }}
.pick:hover {{ border-color: var(--olive); }}
.pick .lvl {{ font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--olive); font-weight: 700; }}
.pick b {{ font-size: 18px; }}
.pick span {{ color: var(--muted); font-size: 14px; }}
.pick .pr {{ color: var(--fg); font-weight: 600; font-variant-numeric: tabular-nums; }}
.facts {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 20px; margin: 0; }}
.facts div {{ display: grid; gap: 2px; border-top: 2px solid var(--ruby); padding-top: 8px; }}
.facts dt {{ font-size: 12px; letter-spacing: 0.1em; text-transform: uppercase; }}
.facts dd {{ font-weight: 500; font-size: 14.5px; }}
.key {{ display: flex; gap: 18px; flex-wrap: wrap; font-size: 13px; color: var(--muted); }}
footer {{ font-size: 12.5px; color: var(--muted); border-top: 1px solid var(--line); padding-top: 16px; }}
@media screen and (max-width: 760px) {{
  .opts, .charts, .hotels, .two, .days, .picks {{ grid-template-columns: 1fr; }}
  .facts {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
  .wrap {{ padding-inline: 16px; gap: 56px; }}
}}
@media print {{
  @page {{ size: A4; margin: 14mm; }}
  body {{ font-size: 11.5px; background: #FBFAF4; }}
  .wrap {{ max-width: none; padding: 0; gap: 26px; }}
  .pb {{ break-before: page; }}
  .opt, .hotel, .pick, .dcol, .verdict, tr {{ break-inside: avoid; }}
  .big {{ font-size: 26px; }} h1 {{ font-size: 40px; }} h3 {{ font-size: 19px; }}
  .verdict p {{ font-size: 16px; }} .todo {{ font-size: 13px; }} table {{ font-size: 11.5px; }}
  .opt {{ box-shadow: none; padding: 16px; gap: 7px; }}
  .verdict {{ padding: 16px 20px; }}
  .hotel, .pick {{ padding: 12px 14px; }}
  .dcol li {{ padding: 4px 0 4px 12px; }}
  section {{ gap: 14px; }}
}}
@media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important; }} }}
</style>
<div class="wrap">

<section>
  <div class="top"><b>Ruby Recruiting Hub · Reise-Concierge</b><span>Exposé · Stand {e(m['stand'])}</span></div>
  <div class="hero">
    <span class="status" style="justify-self:start">{e(m['status'])}</span>
    <h1>{e(m['title'])}</h1>
    <div class="meta"><span>{e(m['route'])}</span><span>{e(m['dates'])}</span><span>{e(m['travellers'])} · {e(m['purpose'])}</span><span>Kosten: {e(m['payer'])}</span></div>
  </div>
  <div class="verdict"><h2>Unsere Empfehlung</h2><p>{e(trip['recommendation']['headline'])}</p><ul>{why}</ul></div>
</section>

<section>
  <h2>Drei Wege, ein Vergleich</h2>
  <div class="opts">{''.join(cards)}</div>
  <div class="charts">
    <div class="chartbox"><h4>Gesamtkosten (Balken = Mitte, Linie = Spanne)</h4>{bars_cost(opts)}</div>
    <div class="chartbox"><h4>Zeit unterwegs, hin und zurück</h4>{bars_time(opts, use_word)}
      <div class="legend"><span><i style="background:var(--ruby)"></i>{e(use_label)}</span><span><i style="background:var(--line)"></i>verlorene Zeit</span></div></div>
  </div>
  <p class="muted">{e(lost_note)} Differenzen beziehen sich auf die Empfehlung.</p>
</section>

<section>
  <h2>Heute erledigen</h2>
  <ul class="todo">{todo}</ul>
</section>

<section class="pb">
  <h2>Hotel wählen</h2>
  <div class="hotels">{''.join(hotel_cards)}</div>
  <div class="two">
    <div><h2 style="margin-bottom:10px">Kosten der Empfehlung</h2><div class="tbl"><table>{cost_rows}</table></div></div>
    <div><h2 style="margin-bottom:10px">Sparhebel</h2><div class="tbl"><table>{save_rows}</table></div></div>
  </div>
  <div class="key"><span>{dot('gruen')} live oder Primärquelle</span><span>{dot('gelb')} belegt, aber nicht live</span><span>{dot('rot')} Schätzung, vor Buchung live prüfen</span></div>
</section>

<section class="pb">
  <h2>Ablauf</h2>
  <div class="days">{days}</div>
  <p class="muted">Gefüllte Punkte sind feste Zeiten. Alles andere ist ein Vorschlag.</p>
</section>

<section>
  <h2>Abende</h2>
  <div class="eves">{eves}</div>
  <dl class="facts">{facts}</dl>
</section>

<section class="pb">
  <h2>Woher die Zahlen kommen</h2>
  <div class="tbl"><table>{srcs}</table></div>
  <div class="key"><span>{dot('gruen')} live oder Primärquelle</span><span>{dot('gelb')} belegt, aber nicht live</span><span>{dot('rot')} Schätzung</span></div>
</section>

<footer>Erstellt vom Reise-Concierge für Toby &amp; Laura · Summen und Differenzen automatisch berechnet aus {e(m['slug'])}.json</footer>
</div>
'''


def find_chrome():
    for c in [os.environ.get("CHROME"), "chromium", "chromium-browser", "google-chrome"]:
        if c and shutil.which(c):
            return shutil.which(c)
    for p in sorted(Path("/opt/pw-browsers").glob("chromium-*/chrome-linux/chrome")):
        return str(p)
    return None


def main():
    src = Path(sys.argv[1])
    trip = json.loads(src.read_text(encoding="utf-8"))
    slug = trip["meta"]["slug"]
    OUT.mkdir(exist_ok=True)
    frag = render(trip)
    (OUT / f"{slug}.html").write_text(frag, encoding="utf-8")
    page = '<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><style>:root{color-scheme:light}</style></head><body>' + frag + "</body></html>"
    printable = OUT / f"{slug}-print.html"
    printable.write_text(page, encoding="utf-8")
    chrome = find_chrome()
    if not chrome:
        print("Kein Chromium gefunden – PDF übersprungen. HTML:", printable)
        return
    pdf = OUT / f"{slug}.pdf"
    subprocess.run([chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                    "--force-prefers-color-scheme=light", f"--print-to-pdf={pdf}", printable.as_uri()],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    print("OK:", OUT / f"{slug}.html", pdf)


if __name__ == "__main__":
    main()
