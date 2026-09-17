"""מחפש את 4 היישובים הנוספים: תל ציון, מעלה עמוס, מיצד, עמנואל."""
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

raw = json.loads(Path("raw_population.json").read_text(encoding="utf-8"))
TARGETS = ["תל ציון", "מעלה עמוס", "מיצד", "עמנואל"]

def adults(r):
    return (int(r["גיל_19_45"]) + int(r["גיל_46_55"]) +
            int(r["גיל_56_64"]) + int(r["גיל_65_פלוס"]))

def children(r):
    return int(r["גיל_0_5"]) + int(r["גיל_6_18"])

def norm(s):
    return s.replace(" ", "").replace("-", "").strip()

for t in TARGETS:
    found = False
    for r in raw:
        name = r.get("שם_ישוב", "").strip()
        if norm(name) == norm(t):
            print(f"✓ {t}:")
            print(f"   במרשם:    '{name}' | סמל={r['סמל_ישוב']}")
            print(f"   מועצה:    {r.get('מועצה_אזורית','').strip() or 'עיר/מועצה מקומית'}")
            print(f"   תושבים:   {r['סהכ']}")
            print(f"   ילדים:    {children(r)}")
            print(f"   מבוגרים:  {adults(r)}")
            print()
            found = True
            break
    if not found:
        print(f"✗ {t}: לא נמצא — חיפוש דמיון:")
        for r in raw:
            name = r.get("שם_ישוב", "").strip()
            if t in name or name in t or norm(t)[:3] in norm(name):
                print(f"   אולי: '{name}' | סמל={r['סמל_ישוב']} | סהכ={r['סהכ']} | {r.get('מועצה_אזורית','').strip()}")
        print()
