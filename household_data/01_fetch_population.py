"""
שולף אוכלוסייה רשמית מ-data.gov.il (רשות האוכלוסין וההגירה)
ל-38 יישובי משרד הביטחון + ביתר עילית.
מקור: דאטה-סט "תושבים בישראל לפי ישובים וקבוצות גיל" — מתעדכן שבועית.
"""

import requests
import json
import csv
from pathlib import Path

BASE = "https://data.gov.il/api/3/action"
RESOURCE_ID = "64edd0ee-3d5d-43ce-8562-c336c24dbc1f"

# 38 יישובי משרד הביטחון
SETTLEMENTS = [
    "אבני חפץ", "איתמר", "אלון מורה", "עדי עד", "אחיה", "קידה",
    "בית חגי", "ברכה", "גבעות הרואה", "גבעת הראל", "דולב", "חוות גלעד",
    "חלמיש", "חרמש", "חרשה", "טלמון", "יצהר", "כוכב השחר",
    "כרם רעים", "כרמי צור", "מבוא דותן", "מעלה לבונה", "מעלה מכמש",
    "נופי נחמיה", "נחליאל", "נריה", "עטרת", "עינב", "עלי", "עמיחי",
    "עפרה", "פסגות", "רחלים", "רימונים", "שבות רחל", "שבי שומרון",
    "שילה", "תקוע"
]
COMPARE = ["ביתר עילית"]

# שמות חלופיים — אומתו מול ה-CSV של רשות האוכלוסין
ALIASES = {
    "בית חגי": ["חגי"],          # סמל 3764, מועצת הר חברון
    "חלמיש": ["נוה צוף"],         # סמל 3573, מטה בנימין
    "עינב": ["ענב"],              # סמל 3712, שומרון
    "עפרה": ["עופרה"],            # סמל 3617, מטה בנימין
    "ברכה": ["ברכה", "הר ברכה"],
    "עדי עד": ["עדי עד", "עדי-עד"],
}

# מאחזים שלא במרשם רשות האוכלוסין — דורשים מקור חיצוני
NOT_IN_REGISTRY = ["קידה", "גבעת הראל", "חוות גלעד", "נופי נחמיה"]

OUT_DIR = Path(__file__).parent
OUT_DIR.mkdir(exist_ok=True)


def fetch_all_records():
    """שולף את כל הרשומות (כ-1,287) מהמאגר."""
    url = f"{BASE}/datastore_search"
    params = {"resource_id": RESOURCE_ID, "limit": 2000}
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()
    if not data.get("success"):
        raise RuntimeError(f"API failure: {data}")
    records = data["result"]["records"]
    print(f"  שלפתי {len(records)} רשומות מהמאגר")
    return records


def find_settlement(name, records):
    """מחפש יישוב לפי שם + שמות חלופיים."""
    candidates = ALIASES.get(name, [name])
    for cand in candidates:
        # התאמה מדויקת אחרי trim
        for r in records:
            if r.get("שם_ישוב", "").strip() == cand.strip():
                return r
        # ניסיון: ללא רווחים
        cand_norm = cand.replace(" ", "").replace("-", "")
        for r in records:
            rec_norm = r.get("שם_ישוב", "").replace(" ", "").replace("-", "").strip()
            if rec_norm == cand_norm:
                return r
    return None


def main():
    print("שולף נתונים מ-data.gov.il…")
    records = fetch_all_records()

    # שמירה גולמית לבדיקה
    raw_path = OUT_DIR / "raw_population.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"  נשמר raw: {raw_path}")

    rows = []
    missing = []
    for name in SETTLEMENTS + COMPARE:
        rec = find_settlement(name, records)
        if rec:
            rows.append({
                "שם_בקשה": name,
                "שם_במאגר": rec.get("שם_ישוב", "").strip(),
                "סמל_ישוב": rec.get("סמל_ישוב"),
                "מועצה_אזורית": rec.get("מועצה_אזורית", "").strip(),
                "נפה": rec.get("נפה", "").strip(),
                "סהכ_תושבים": rec.get("סהכ"),
                "גיל_0_5": rec.get("גיל_0_5"),
                "גיל_6_18": rec.get("גיל_6_18"),
                "גיל_19_45": rec.get("גיל_19_45"),
                "גיל_46_55": rec.get("גיל_46_55"),
                "גיל_56_64": rec.get("גיל_56_64"),
                "גיל_65_פלוס": rec.get("גיל_65_פלוס"),
            })
        else:
            missing.append(name)

    out_csv = OUT_DIR / "population_results.csv"
    with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        w.writeheader()
        w.writerows(rows)
    print(f"\nנמצאו: {len(rows)} | חסרים: {len(missing)}")
    print(f"CSV נשמר ב: {out_csv}")

    if missing:
        print("\nיישובים שלא נמצאו (נדרש מקור אלטרנטיבי או תיקון שם):")
        for m in missing:
            print(f"  - {m}")

    # סטטיסטיקה מהירה
    total_pop = sum(int(r["סהכ_תושבים"] or 0) for r in rows if r["שם_בקשה"] != "ביתר עילית")
    beitar = next((r for r in rows if r["שם_בקשה"] == "ביתר עילית"), None)
    print(f"\n— סיכום —")
    print(f"סך תושבים ב-38 יישובי משרד הביטחון שנמצאו: {total_pop:,}")
    if beitar:
        print(f"ביתר עילית (לשם השוואה): {int(beitar['סהכ_תושבים']):,}")


if __name__ == "__main__":
    main()
