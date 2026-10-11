# TKLST Reisen-Concierge (Mobile Web-App)

Statische PWA auf Vercel mit Passwortschutz.

- `public/` – App (index.html), Login, Manifest, Service Worker, Icons, Daten, Exposés
- `middleware.js` – Passwortschutz (Cookie, 1 Jahr)
- `api/login.js` – Login prüft `APP_PASSWORD`
- `build.py` – erzeugt `public/data/*` und `public/expose/*` aus `reiseplanung/`

Vercel-Projekt: Root Directory `app`, Framework „Other“, Env `APP_PASSWORD`.
Aufs iPhone: Link in Safari öffnen → Teilen → „Zum Home-Bildschirm“.
