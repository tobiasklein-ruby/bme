#!/usr/bin/env bash
# Richtet im bme-Repo einen Auto-Push ein: Nach jedem Commit wird der aktuelle Branch sofort gepusht.
# Einmalig auf herdr ausführen: bash reiseplanung/tool/install-autopush.sh
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
hook=.git/hooks/post-commit
cat > "$hook" <<'HOOK'
#!/usr/bin/env bash
branch=$(git rev-parse --abbrev-ref HEAD)
git push -q origin "$branch" >/dev/null 2>&1 || echo "Auto-Push fehlgeschlagen – bitte 'git push' prüfen." >&2
HOOK
chmod +x "$hook"
echo "Auto-Push aktiv: $hook"
