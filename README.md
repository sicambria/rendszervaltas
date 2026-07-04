# Rendszerváltás Követő

Prototípus weboldal, amely a Tisza Párt 2026-os kormányprogramjának (`tisza2026.pdf`) vállalásait és azok megvalósulási állapotát követi nyomon, hiteles forrásokkal alátámasztva.

Élő oldal: https://sicambria.github.io/rendszervaltas/

## Felépítés

- `index.html` — a statikus oldal (React + Tailwind CDN-ről, build lépés nélkül).
- `promises_data.js` — az 1000+ vállalás adatai (kategória, státusz, leírás, hiteles források).
- `tisza2026.pdf` / `extract_promises.py` — az eredeti forrásdokumentum és a belőle vállalásokat kinyerő szkript.
- `CHANGELOG.md` — minden státuszváltozás és forrás dátumozva.

## Frissítési folyamat

A `.github/workflows/weekly-update.yml` hetente (hétfőnként) lefuttat egy kutató-validáló Claude Code pipeline-t, amely:

1. Utánanéz a legutóbbi frissítés óta történt fejleményeknek, és frissíti a `promises_data.js` érintett tételeinek státuszát és forrásait.
2. Egy független második lépésben ellenőrzi a változtatásokat (forrás valódisága, logikus státuszváltás).
3. Sikeres ellenőrzés esetén közvetlenül a `main` ágra kerül (a GitHub Pages ezután automatikusan újratölti az oldalt); sikertelen ellenőrzés esetén GitHub issue-t nyit emberi felülvizsgálatra.

## Licenc

A weboldal tartalma [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.hu) licenc alatt érhető el.

Kapcsolat: rendszervaltozas@pm.me
