"""
מחפש את 8 היישובים החסרים בנתונים הגולמיים — בודק שמות חלופיים,
ביטויים חלקיים, ותווי דמיון.
"""

import json
from pathlib import Path

MISSING = [
    "קידה", "בית חגי", "גבעת הראל", "חוות גלעד",
    "חלמיש", "נופי נחמיה", "עינב", "עפרה"
]

# כינויים ידועים מויקיפדיה / מקורות שונים
ALIASES = {
    "חלמיש": ["נווה צוף", "חלמיש", "נווה-צוף"],
    "עפרה": ["עפרה"],
    "עינב": ["עינב"],
    "בית חגי": ["בית חגי", "בית-חגי", "בית חג'י"],
    "נופי נחמיה": ["נופי נחמיה", "נופי-נחמיה"],
    "קידה": ["קידה"],
    "גבעת הראל": ["גבעת הראל", "גבעת-הראל"],
    "חוות גלעד": ["חוות גלעד", "חוות-גלעד", "גלעד"],
}

import sys
sys.stdout.reconfigure(encoding="utf-8")
raw = json.loads(Path("raw_population.json").read_text(encoding="utf-8"))
print(f"סה\"כ רשומות במאגר: {len(raw)}\n")

def norm(s):
    return s.replace(" ", "").replace("-", "").replace("'", "").strip()

for orig in MISSING:
    print(f"--- מחפש: {orig} ---")
    candidates = ALIASES.get(orig, [orig])
    found_any = False

    # התאמה מדויקת לכל הכינויים
    for cand in candidates:
        for r in raw:
            name = r.get("שם_ישוב", "").strip()
            if norm(name) == norm(cand):
                print(f"  ✓ התאמה מדויקת: '{name}' | סהכ={r.get('סהכ')} | סמל={r.get('סמל_ישוב')}")
                found_any = True

    # חיפוש חלקי — מכיל את השם
    if not found_any:
        for cand in candidates:
            for r in raw:
                name = r.get("שם_ישוב", "").strip()
                if norm(cand) in norm(name) or norm(name) in norm(cand):
                    if len(name) > 2:
                        print(f"  ~ אולי: '{name}' | סהכ={r.get('סהכ')} | סמל={r.get('סמל_ישוב')} | מועצה={r.get('מועצה_אזורית','').strip()}")
                        found_any = True

    if not found_any:
        print(f"  ✗ לא נמצא כלום במאגר")
    print()
