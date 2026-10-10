# Reiseplanung – Backlog (Laura & Toby)

Persönlicher Reise-Concierge für Ruby Recruiting Hub, TK EST und privat.

## Arbeitsweise
1. Agent „Route & Preise“: Bahn, Flug, Fernbus, Mietwagen, Taxi/Uber – günstigste, schnellste und empfohlene Variante.
2. Agent „Unterkunft“: Boutique/Luxus mit Preis-Leistung, Stadt-bekannt, gute Bewertung; je eine 5★/6★-Alternative; Restaurant-Tipps.
3. Prüfschritt: Jedes Ergebnis wird auf Realität, Aktualität und Buchbarkeit geprüft, bevor es weitergegeben wird.
4. Coaching: aktiv hinterfragen (z. B. Vorabend-Anreise, wenn günstiger und angenehmer).

## Interaktionsregel (gilt ab 2026-10-10, IMMER)
- Fehlende Infos/Fragen IMMER als Klick-Fragen stellen (AskUserQuestion), nie als Freitext-Frage.
- Lieber zu viele als zu wenige Fragen; nichts auslassen; in Kategorien bündeln.
- Toby antwortet nur per Klick → Antwortoptionen so bauen, dass alle realistischen Werte (Beträge, Zeiten, Orte, Präferenzen) anklickbar sind; keine Option darf Freitext voraussetzen.

## Reiseprofil (Stand 2026-10-10)
| Thema | Antwort |
|---|---|
| Ziele | Inland und Europa |
| Reisende | wechselnd: Laura, Toby oder beide |
| Anlass / Kostenträger | gemischt: Ruby Recruiting, TK EST, privat |
| Termine | komplett flexibel |
| Flug | immer mitprüfen |
| Flugklasse | Premium Economy |
| Bahnklasse | Smart vergleichen: Standard 2. Kl. Flex mit BC50 + Sitzplatz; 1. Kl. nur bei kleinem Aufpreis (< ca. 30 €) oder langer Arbeitsfahrt |
| BahnCard / Abos | Toby: BahnCard 50, 2. Klasse + Deutschlandticket (Laura: nur Deutschlandticket) |

## Grunddaten Tickets & Abos (IMMER berücksichtigen)
**Toby**
- BahnCard 50, 2. Klasse
  - 50 % auf Flexpreis 2. Klasse, 25 % auf Sparpreise 2. Klasse (Konditionen vor Buchung auf bahn.de gegenprüfen)
  - Gilt nicht für Tickets der 1. Klasse → bei jeder Bahnreise vergleichen: 2. Kl. Flex mit BC50 vs. 1. Kl. Spar ohne Rabatt vs. Upgrade-Möglichkeit
  - Preise im Vergleich immer MIT BahnCard-Rabatt rechnen und ausweisen
- Deutschlandticket
  - Deckt bundesweit Nahverkehr ab: U-/S-Bahn, Tram, Bus, RE/RB 2. Klasse – nicht ICE/IC/EC
  - Letzte Meile (Bahnhof ↔ Hotel/Termin) in Stuttgart, Berlin & Co. kostet 0 € → Taxi nur bei Gepäck, Zeitdruck, später Uhrzeit oder Komfortwunsch
  - Taxi/Uber in Vergleichen immer gegen die kostenlose ÖPNV-Option stellen
- Kein Flex-Aufpreis für City-Ticket nötig (Deutschlandticket deckt das ab)

**Laura**
- Deutschlandticket (Nahverkehr/letzte Meile 0 €)
- Keine BahnCard → zahlt Fernverkehr voll; bei gemeinsamen Reisen beide Preise getrennt ausweisen
- Bei gemeinsamen Reisen Sparpreise bevorzugt prüfen (Rabattgefälle zwischen Toby und Laura beachten)
- Laufend mitrechnen: Lohnt sich eine BahnCard 25/50 für Laura? (Hinweis geben, sobald Fahrten das rechtfertigen)

## Output-Standard: Reisedossier (Vorbild: Hendriks China-Dossier, 6 Seiten A4)
Jede größere Reise endet mit einem PDF-Dossier:
1. Deckblatt: Titel, Untertitel, Status („alles gebucht" / offen), 4 Kennzahlen (Nächte, km, Kosten, Zeitverschiebung), Zeitleiste der Nächte, Routenkarte, Stationen-Tabelle (Ort, Nächte, Unterkunft, wofür).
2. „Drei Dinge, die zählen": die 3 kritischsten Punkte der Reise.
3. „Was für wen": Interessen je Person (Laura / Toby / gemeinsam) pro Station.
4. Fahrplan Tag für Tag: fest gebucht (rot) vs. Programm-Idee (flexibel); Abfahrtszeiten mit Puffer, Zug-/Flugnummer, Wagen/Sitz.
5. Transfers Tür-zu-Tür mit Dauer und Fallback; Plan B je Risiko (Wetter, Ausfall, Grenze).
6. Je Station: Einordnung, Highlights, Restaurants mit Preis p. P., Wetter, Mobilität, Hoteladresse in Landessprache fürs Taxi.
7. Praktisch: Bezahlen, Apps, Internet, Strom, Notfallnummern, Sprachkarte, Allergie-/Unverträglichkeitskarte in Landessprache.
8. To-dos unterwegs (Reservierungen, späten Check-in ankündigen) + Quellen und Stand-Datum.

Ergänzungen für uns (fehlen bei Hendrik):
- Kosten je Kostenträger (Ruby Recruiting / TK EST / privat) + Belegliste
- Storno-Fristen und Buchungsnummern je Leistung
- Hotelname und Kategorie überall (bei Hendrik teils nur „gebucht")
- Komfort-Standard: Bahn 1. Klasse (Hendrik: ein Zug 2. Kl.)
- Business-Block: Termine, Adressen, Ansprechpartner, Meeting-Puffer
- Prüfschritt: Dossier gegen Buchungen gegenlesen (bei Hendrik steht „Sebastians Extras" ohne Sebastian)

## Learnings aus Testlauf 1 (Stuttgart–Berlin, 11.–13.10.2026)
- Cloud-Umgebung: bahn.de, DB-API, Booking, Google, Hotel-Websites gesperrt → nur Websuche, keine Live-Preise. Für echte Planung: auf herdr oder mit Claude in Chrome arbeiten (Live-Zugriff auf DB Navigator/bahn.de, Booking).
- Prüfschritt hat gegriffen: kein Ergebnis ohne Kennzeichnung VERIFIZIERT/GESCHÄTZT; Sonntagsverkehr des Sprinters unbestätigt.
- Event-Check lohnt sich (World Health Summit, Bar Convent, Festival of Lights → Preisdruck).
- Coaching-Regel: harte Zeitvorgaben hinterfragen, wenn eine knapp spätere Direktverbindung deutlich mehr Komfort/Zeit bringt.

## Offene Fragen
- [x] Bahnklasse: smart vergleichen
- [x] BahnCard Toby: BC50 2. Kl. + Deutschlandticket
- [x] Laura: nur Deutschlandticket
- [ ] Auto: eigenes/Firmenauto, Mietwagen, Taxi/Uber/Chauffeur, ÖPNV letzte Meile
- [ ] Priorität Zeit vs. Geld vs. Komfort
- [ ] Budget An-/Abreise pro Person
- [ ] Gepäck
- [ ] Hotel: Zimmeranzahl, Preisrahmen/Nacht, Ketten/Programme, Must-haves, Storno
- [ ] Essen: Küche, Niveau, Unverträglichkeiten
- [ ] Erste konkrete Reise: Start, Ziel, Zeitraum

## Erledigt
- [x] Grundprofil erfasst
