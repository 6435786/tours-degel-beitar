"""
מאחד את כל המקורות לטבלת אמת אחת:
- data.gov.il (רשות האוכלוסין) — נכון ל-2026-05-17
- Wikipedia (טבלאות המועצות האזוריות) — נכון 2024-2025
- חיפושים בודדים למאחזים — מספר משפחות עדכני

מחלק לפי מגזר ומחשב אומדן בתי-אב.
"""

import csv, json
from pathlib import Path

OUT = Path(__file__).parent

# נתונים מאוחדים פר יישוב — כל מה שאספתי
# שדות:
#   pop_reg = אוכלוסייה במרשם data.gov.il (נכון 2026-05-17). ריק אם לא נמצא.
#   pop_wiki = אוכלוסייה לפי טבלת ויקיפדיה (CBS ~2023-2024). ריק אם הוצג רק "משפחות".
#   families = מספר משפחות כפי שמופיע בויקיפדיה/חיפוש (None אם אין).
#   year_families = שנה של נתון המשפחות
#   sector = מגזר עיקרי: חרדי / דתי-לאומי / מעורב / חילוני
#   founded = שנת הקמה
#   council = מועצה אזורית

DATA = {
    # מועצה אזורית שומרון
    "אבני חפץ":      {"council":"שומרון","founded":1990,"pop_reg":2742,"pop_wiki":2670,"families":None,"sector":"דתי-לאומי"},
    "איתמר":         {"council":"שומרון","founded":1984,"pop_reg":1734,"pop_wiki":1641,"families":None,"sector":"דתי-לאומי"},
    "אלון מורה":     {"council":"שומרון","founded":1980,"pop_reg":2164,"pop_wiki":2075,"families":None,"sector":"דתי-לאומי"},
    "ברכה":          {"council":"שומרון","founded":1983,"pop_reg":3404,"pop_wiki":3318,"families":None,"sector":"דתי-לאומי"},
    "חוות גלעד":     {"council":"שומרון","founded":2002,"pop_reg":None,"pop_wiki":None,"families":80,"year_families":2024,"sector":"דתי-לאומי"},
    "חרמש":          {"council":"שומרון","founded":1983,"pop_reg":304,"pop_wiki":298,"families":None,"sector":"דתי-לאומי"},
    "יצהר":          {"council":"שומרון","founded":1983,"pop_reg":2707,"pop_wiki":2495,"families":None,"sector":"דתי-לאומי"},
    "מבוא דותן":     {"council":"שומרון","founded":1981,"pop_reg":955,"pop_wiki":838,"families":None,"sector":"דתי-לאומי"},
    "נופי נחמיה":    {"council":"שומרון","founded":2002,"pop_reg":None,"pop_wiki":None,"families":94,"year_families":2023,"sector":"דתי-לאומי"},
    "עינב":          {"council":"שומרון","founded":1981,"pop_reg":1345,"pop_wiki":1265,"families":None,"sector":"דתי-לאומי"},
    "רחלים":         {"council":"שומרון","founded":1991,"pop_reg":1348,"pop_wiki":1262,"families":None,"sector":"דתי-לאומי"},
    "שבי שומרון":    {"council":"שומרון","founded":1977,"pop_reg":1182,"pop_wiki":1178,"families":None,"sector":"דתי-לאומי"},

    # מועצה אזורית מטה בנימין
    "אחיה":          {"council":"מטה בנימין","founded":1997,"pop_reg":70,"pop_wiki":None,"families":82,"year_families":2023,"sector":"דתי-לאומי"},
    "גבעות הרואה":   {"council":"מטה בנימין","founded":2003,"pop_reg":151,"pop_wiki":None,"families":50,"year_families":2025,"sector":"דתי-לאומי"},
    "גבעת הראל":     {"council":"מטה בנימין","founded":1998,"pop_reg":None,"pop_wiki":None,"families":105,"year_families":2025,"sector":"דתי-לאומי"},
    "דולב":          {"council":"מטה בנימין","founded":1983,"pop_reg":1678,"pop_wiki":1593,"families":None,"sector":"דתי-לאומי"},
    "חלמיש":         {"council":"מטה בנימין","founded":1977,"pop_reg":1525,"pop_wiki":1500,"families":None,"sector":"דתי-לאומי"},
    "חרשה":          {"council":"מטה בנימין","founded":1997,"pop_reg":60,"pop_wiki":None,"families":75,"year_families":2025,"sector":"דתי-לאומי"},
    "טלמון":         {"council":"מטה בנימין","founded":1989,"pop_reg":6274,"pop_wiki":6133,"families":None,"sector":"דתי-לאומי"},
    "כוכב השחר":     {"council":"מטה בנימין","founded":1980,"pop_reg":3042,"pop_wiki":2850,"families":None,"sector":"דתי-לאומי"},
    "כרם רעים":      {"council":"מטה בנימין","founded":2001,"pop_reg":70,"pop_wiki":1200,"families":200,"year_families":2024,"sector":"דתי-לאומי"},
    "מעלה לבונה":    {"council":"מטה בנימין","founded":1984,"pop_reg":1073,"pop_wiki":1006,"families":None,"sector":"דתי-לאומי"},
    "מעלה מכמש":     {"council":"מטה בנימין","founded":1981,"pop_reg":2337,"pop_wiki":2328,"families":None,"sector":"דתי-לאומי"},
    "נחליאל":        {"council":"מטה בנימין","founded":1984,"pop_reg":1056,"pop_wiki":798,"families":None,"sector":"דתי-לאומי"},
    "נריה":          {"council":"מטה בנימין","founded":1991,"pop_reg":19,"pop_wiki":None,"families":450,"year_families":2023,"sector":"דתי-לאומי"},
    "עדי עד":        {"council":"מטה בנימין","founded":1990,"pop_reg":38,"pop_wiki":None,"families":50,"year_families":2025,"sector":"דתי-לאומי"},
    "עטרת":          {"council":"מטה בנימין","founded":1981,"pop_reg":832,"pop_wiki":716,"families":None,"sector":"דתי-לאומי"},
    "עלי":           {"council":"מטה בנימין","founded":1984,"pop_reg":4847,"pop_wiki":5040,"families":None,"sector":"דתי-לאומי"},
    "עמיחי":         {"council":"מטה בנימין","founded":2017,"pop_reg":409,"pop_wiki":409,"families":None,"sector":"דתי-לאומי"},
    "עפרה":          {"council":"מטה בנימין","founded":1975,"pop_reg":3324,"pop_wiki":3209,"families":None,"sector":"דתי-לאומי"},
    "פסגות":         {"council":"מטה בנימין","founded":1981,"pop_reg":2332,"pop_wiki":2341,"families":None,"sector":"דתי-לאומי"},
    "קידה":          {"council":"מטה בנימין","founded":2003,"pop_reg":None,"pop_wiki":None,"families":150,"year_families":2025,"sector":"דתי-לאומי"},
    "רימונים":       {"council":"מטה בנימין","founded":1980,"pop_reg":710,"pop_wiki":673,"families":None,"sector":"מעורב"},
    "שבות רחל":      {"council":"מטה בנימין","founded":1992,"pop_reg":42,"pop_wiki":None,"families":150,"year_families":2025,"sector":"דתי-לאומי"},
    "שילה":          {"council":"מטה בנימין","founded":1978,"pop_reg":6227,"pop_wiki":6290,"families":None,"sector":"דתי-לאומי"},

    # מועצה אזורית גוש עציון
    "כרמי צור":      {"council":"גוש עציון","founded":1984,"pop_reg":1119,"pop_wiki":987,"families":None,"sector":"דתי-לאומי"},
    "תקוע":          {"council":"גוש עציון","founded":1977,"pop_reg":5054,"pop_wiki":4900,"families":None,"sector":"מעורב"},

    # מועצה אזורית הר חברון
    "בית חגי":       {"council":"הר חברון","founded":1984,"pop_reg":848,"pop_wiki":851,"families":None,"sector":"דתי-לאומי"},

    # להשוואה — אוכלוסייה ממרשם current; בתי אב מעיריית ביתר 2026.
    "ביתר עילית":    {"council":"(עיר)","founded":1985,"pop_reg":75514,"pop_wiki":73719,
                      "households_direct":11500,"year_families":2026,"families":None,"sector":"חרדי"},
}

# ממוצע נפשות לבית-אב פר מגזר
NEFASHOT_PER_HOUSEHOLD = {
    "חרדי":        6.7,    # למ"ס פרופיל ביתר עילית 2023
    "דתי-לאומי":   5.0,    # יישובי יו"ש דתיים
    "מעורב":       4.0,
    "חילוני":      3.1,
}


def best_population(d):
    """
    סדר עדיפויות (כלל יסוד: לא לנחש):
    1. אם יש מרשם — להשתמש בו.
    2. חריג: אם יש דיווח משפחות גדול (>500 נפש) ומרשם נמוך משמעותית (פי 4+) →
       סימן שהמרשם חלקי (מאחז שזה עתה הוכר). השתמש באומדן ממשפחות.
    3. ויקיפדיה.
    4. אומדן ממשפחות.
    """
    reg, wiki, fam = d.get("pop_reg"), d.get("pop_wiki"), d.get("families")
    avg = NEFASHOT_PER_HOUSEHOLD[d["sector"]]
    est_from_fam = round(fam * avg) if fam else None

    if est_from_fam and reg and est_from_fam > reg * 4 and est_from_fam > 500:
        return est_from_fam
    if reg is not None:
        return reg
    if wiki is not None:
        return wiki
    return est_from_fam


def best_households(d):
    """
    סדר עדיפויות:
    1. households_direct — נתון רשמי של למ"ס (ערים 50K+).
    2. אם האוכלוסייה מבוססת על families (מאחזים) — קח את families.
    3. חישוב מהאוכלוסייה.
    """
    if d.get("households_direct"):
        return d["households_direct"]
    pop = best_population(d)
    if pop is None:
        return None
    fam = d.get("families")
    avg = NEFASHOT_PER_HOUSEHOLD[d["sector"]]
    if fam and pop == round(fam * avg):
        return fam
    return round(pop / avg)


def main():
    rows = []
    for name, d in DATA.items():
        pop = best_population(d)
        hh = best_households(d)
        avg = NEFASHOT_PER_HOUSEHOLD[d["sector"]]

        source_pop = []
        if d.get("pop_reg"):  source_pop.append(f"מרשם:{d['pop_reg']}")
        if d.get("pop_wiki"): source_pop.append(f"ויקי:{d['pop_wiki']}")
        if not source_pop:    source_pop.append(f"אומדן ממשפחות")

        source_hh = "מקור ישיר" if d.get("families") else f"אומדן ({avg} נפ׳/בא)"

        rows.append({
            "שם": name,
            "מועצה": d["council"],
            "הוקם": d["founded"],
            "מגזר": d["sector"],
            "תושבים_מרשם_2026": d.get("pop_reg") or "",
            "תושבים_ויקי_2025": d.get("pop_wiki") or "",
            "אוכלוסייה_אומדן_עדכני": pop or "",
            "משפחות_מקור_ישיר": d.get("families") or "",
            "שנת_משפחות": d.get("year_families") or "",
            "בתי_אב_אומדן": hh or "",
            "מקור_אוכלוסייה": " | ".join(source_pop),
            "אופן_חישוב_בתי_אב": source_hh,
        })

    out = OUT / "consolidated.csv"
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # סיכומים
    yosh_rows = [r for r in rows if r["שם"] != "ביתר עילית"]
    total_pop = sum(int(r["אוכלוסייה_אומדן_עדכני"] or 0) for r in yosh_rows)
    total_hh  = sum(int(r["בתי_אב_אומדן"]      or 0) for r in yosh_rows)
    beitar = next(r for r in rows if r["שם"] == "ביתר עילית")
    print(f"38 יישובי משרד הביטחון: {total_pop:,} תושבים, ~{total_hh:,} בתי אב")
    print(f"ביתר עילית (השוואה):    {beitar['אוכלוסייה_אומדן_עדכני']:,} תושבים, ~{beitar['בתי_אב_אומדן']:,} בתי אב")
    print(f"\nנכתב: {out}")


if __name__ == "__main__":
    main()
