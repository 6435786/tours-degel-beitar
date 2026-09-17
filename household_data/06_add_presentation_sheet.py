"""
מוסיף לקובץ Excel הקיים גיליון 'תצוגה לישיבה' — מסודר וברור,
מסמן בבירור מה רשמי, מה דיווח קהילתי, ומה אומדן.
לא מערבב — כל מספר עם מקור.

כולל עמודת "אומדן בתי אב לפי גילים" — שיטה עצמאית:
  בתי אב ≈ מבוגרים 19+ ÷ ממוצע מבוגרים/בא (3.47 חרדי, 2.5 דתי, 2.2 מעורב)
  הממוצע 3.47 מכויל על ביתר (יש לנו לה את התשובה הרשמית).
"""
import csv, json
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT = Path(__file__).parent
XLSX = OUT / "בתי_אב_38_יישובים.xlsx"

# === קוד צבעים ===
HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
WHITE = Font(color="FFFFFF", bold=True, size=11)

# רמת ביטחון
HARD_FILL = PatternFill("solid", fgColor="C6EFCE")  # ירוק — נתון רשמי במרשם
MED_FILL  = PatternFill("solid", fgColor="FFEB9C")  # צהוב — מספר משפחות מדווח (לא רשמי)
SOFT_FILL = PatternFill("solid", fgColor="FFC7CE")  # אדום בהיר — אומדן מחושב

BORDER = Border(top=Side(border_style="thin", color="999999"),
                bottom=Side(border_style="thin", color="999999"),
                left=Side(border_style="thin", color="999999"),
                right=Side(border_style="thin", color="999999"))
BOLD = Font(bold=True, size=11)
TITLE = Font(bold=True, size=14, color="1F4E79")
NORMAL = Font(size=11)

# === נתונים — מסונכרנים עם 04_build_consolidated ===
# שדות: pop_reg, pop_wiki, families (None אם אין נתון ישיר), year_families, sector, council, founded
DATA = {
    # מועצה אזורית שומרון
    "אבני חפץ":     {"council":"שומרון","founded":1990,"sector":"דתי-לאומי","pop_reg":2742,"pop_wiki":2670,"families":None},
    "איתמר":        {"council":"שומרון","founded":1984,"sector":"דתי-לאומי","pop_reg":1734,"pop_wiki":1641,"families":None},
    "אלון מורה":    {"council":"שומרון","founded":1980,"sector":"דתי-לאומי","pop_reg":2164,"pop_wiki":2075,"families":None},
    "ברכה":         {"council":"שומרון","founded":1983,"sector":"דתי-לאומי","pop_reg":3404,"pop_wiki":3318,"families":None},
    "חוות גלעד":    {"council":"שומרון","founded":2002,"sector":"דתי-לאומי","pop_reg":None,"pop_wiki":None,"families":80,"year_families":2024,"note":"מאחז — לא במרשם רשמי. דיווח מויקיפדיה ויושקה."},
    "חרמש":         {"council":"שומרון","founded":1983,"sector":"דתי-לאומי","pop_reg":304,"pop_wiki":298,"families":None},
    "יצהר":         {"council":"שומרון","founded":1983,"sector":"דתי-לאומי","pop_reg":2707,"pop_wiki":2495,"families":None},
    "מבוא דותן":    {"council":"שומרון","founded":1981,"sector":"דתי-לאומי","pop_reg":955,"pop_wiki":838,"families":None},
    "נופי נחמיה":   {"council":"שומרון","founded":2002,"sector":"דתי-לאומי","pop_reg":None,"pop_wiki":None,"families":94,"year_families":2023,"note":"מאחז שהוכר רק 3/2025. דיווח 2023 מויקיפדיה."},
    "עינב":         {"council":"שומרון","founded":1981,"sector":"דתי-לאומי","pop_reg":1345,"pop_wiki":1265,"families":None},
    "רחלים":        {"council":"שומרון","founded":1991,"sector":"דתי-לאומי","pop_reg":1348,"pop_wiki":1262,"families":None},
    "שבי שומרון":   {"council":"שומרון","founded":1977,"sector":"דתי-לאומי","pop_reg":1182,"pop_wiki":1178,"families":None},

    # מועצה אזורית מטה בנימין
    "אחיה":         {"council":"מטה בנימין","founded":1997,"sector":"דתי-לאומי","pop_reg":70,"pop_wiki":None,"families":82,"year_families":2023,"note":"דיווח ויקיפדיה 2023: 82 משפחות — לאימות."},
    "גבעות הרואה":  {"council":"מטה בנימין","founded":2003,"sector":"דתי-לאומי","pop_reg":151,"pop_wiki":None,"families":50,"year_families":2025,"note":"פער בין מרשם (151) ל-50 משפ׳ ויקי — לבדיקה."},
    "גבעת הראל":    {"council":"מטה בנימין","founded":1998,"sector":"דתי-לאומי","pop_reg":None,"pop_wiki":None,"families":105,"year_families":2025,"note":"מאחז — לא במרשם. דיווח טבלת ויקיפדיה 2025."},
    "דולב":         {"council":"מטה בנימין","founded":1983,"sector":"דתי-לאומי","pop_reg":1678,"pop_wiki":1593,"families":None},
    "חלמיש":        {"council":"מטה בנימין","founded":1977,"sector":"דתי-לאומי","pop_reg":1525,"pop_wiki":1500,"families":None,"note":"שם רשמי במרשם: 'נוה צוף'."},
    "חרשה":         {"council":"מטה בנימין","founded":1997,"sector":"דתי-לאומי","pop_reg":60,"pop_wiki":None,"families":75,"year_families":2025,"note":"דיווח ויקיפדיה 2025: 75 משפחות — לאימות."},
    "טלמון":        {"council":"מטה בנימין","founded":1989,"sector":"דתי-לאומי","pop_reg":6274,"pop_wiki":6133,"families":None},
    "כוכב השחר":    {"council":"מטה בנימין","founded":1980,"sector":"דתי-לאומי","pop_reg":3042,"pop_wiki":2850,"families":None},
    "כרם רעים":     {"council":"מטה בנימין","founded":2001,"sector":"דתי-לאומי","pop_reg":70,"pop_wiki":1200,"families":200,"year_families":2024,"note":"פער קיצוני: מרשם 70, ויקי 1,200/200 משפ׳. שני מקורות לא רשמיים מאשרים."},
    "מעלה לבונה":   {"council":"מטה בנימין","founded":1984,"sector":"דתי-לאומי","pop_reg":1073,"pop_wiki":1006,"families":None},
    "מעלה מכמש":    {"council":"מטה בנימין","founded":1981,"sector":"דתי-לאומי","pop_reg":2337,"pop_wiki":2328,"families":None},
    "נחליאל":       {"council":"מטה בנימין","founded":1984,"sector":"דתי-לאומי","pop_reg":1056,"pop_wiki":798,"families":None},
    "נריה":         {"council":"מטה בנימין","founded":1991,"sector":"דתי-לאומי","pop_reg":19,"pop_wiki":None,"families":450,"year_families":2023,"note":"פער קיצוני: מרשם 19, אך ויקיפדיה ומקורות יישובים מדווחים על ~450 משפחות. סביר שהמרשם משקף רק תיק חדש."},
    "עדי עד":       {"council":"מטה בנימין","founded":1990,"sector":"דתי-לאומי","pop_reg":38,"pop_wiki":None,"families":50,"year_families":2025,"note":"מרשם 38 נפש vs ויקי 50 משפ׳ — אי-ודאות גבוהה."},
    "עטרת":         {"council":"מטה בנימין","founded":1981,"sector":"דתי-לאומי","pop_reg":832,"pop_wiki":716,"families":None},
    "עלי":          {"council":"מטה בנימין","founded":1984,"sector":"דתי-לאומי","pop_reg":4847,"pop_wiki":5040,"families":None},
    "עמיחי":        {"council":"מטה בנימין","founded":2017,"sector":"דתי-לאומי","pop_reg":409,"pop_wiki":409,"families":None},
    "עפרה":         {"council":"מטה בנימין","founded":1975,"sector":"דתי-לאומי","pop_reg":3324,"pop_wiki":3209,"families":None,"note":"שם רשמי במרשם: 'עופרה'."},
    "פסגות":        {"council":"מטה בנימין","founded":1981,"sector":"דתי-לאומי","pop_reg":2332,"pop_wiki":2341,"families":None},
    "קידה":         {"council":"מטה בנימין","founded":2003,"sector":"דתי-לאומי","pop_reg":None,"pop_wiki":None,"families":150,"year_families":2025,"note":"מאחז — לא במרשם. דיווח טבלת ויקיפדיה: 150+ משפחות."},
    "רימונים":      {"council":"מטה בנימין","founded":1980,"sector":"מעורב","pop_reg":710,"pop_wiki":673,"families":None},
    "שבות רחל":     {"council":"מטה בנימין","founded":1992,"sector":"דתי-לאומי","pop_reg":42,"pop_wiki":None,"families":150,"year_families":2025,"note":"מרשם 42 נפש vs 150 משפ׳ ויקי. סביר שמתועד תחת שילה."},
    "שילה":         {"council":"מטה בנימין","founded":1978,"sector":"דתי-לאומי","pop_reg":6227,"pop_wiki":6290,"families":None},

    # מועצה אזורית גוש עציון
    "כרמי צור":     {"council":"גוש עציון","founded":1984,"sector":"דתי-לאומי","pop_reg":1119,"pop_wiki":987,"families":None},
    "תקוע":         {"council":"גוש עציון","founded":1977,"sector":"מעורב","pop_reg":5054,"pop_wiki":4900,"families":None},

    # מועצה אזורית הר חברון
    "בית חגי":      {"council":"הר חברון","founded":1984,"sector":"דתי-לאומי","pop_reg":848,"pop_wiki":851,"families":None,"note":"שם רשמי במרשם: 'חגי'."},

    # להשוואה — ביתר עילית + יישובים חרדיים נוספים שהוסיף המשתמש
    "ביתר עילית":   {"council":"(עיר חרדית)","founded":1985,"sector":"חרדי","compare":True,
                     "pop_reg":75514,"pop_wiki":73719,"families":None,
                     "households_direct":11500,"year_hh":2026,
                     "note":"אוכלוסייה: מרשם רשות האוכלוסין (עדכני 2026-05-17). משקי בית: 11,500 — מסר עיריית ביתר עילית 2026. ערך זה תואם את אומדן הגידול מסקר למ\"ס 2022 (9,800) ב-3.5%/שנה."},
    "תל ציון":      {"council":"מטה בנימין","founded":2000,"sector":"חרדי","compare":True,
                     "pop_reg":7641,"pop_wiki":7209,"families":1250,"year_families":2018,
                     "note":"מספר משפחות: ויקיפדיה מציינת 'כ-1,250 משפחות באמצע 2018'. כיום סביר שגבוה יותר עקב גידול חרדי טיפוסי, אך אין נתון רשמי עדכני."},
    "מעלה עמוס":    {"council":"גוש עציון","founded":1981,"sector":"חרדי","compare":True,
                     "pop_reg":1561,"pop_wiki":1340,"families":None,
                     "note":"יישוב חרדי. אין נתון משפחות עדכני אמין — היישוב גדל בפעימות אכלוסים (לא גידול טבעי לינארי), כך שדיווחים ישנים (50-100 משפחות) אינם בני-תוקף. בא מחושב מהאוכלוסייה ÷ 6.7."},
    "מיצד":         {"council":"גוש עציון","founded":1983,"sector":"חרדי","compare":True,
                     "pop_reg":1647,"pop_wiki":1513,"families":200,"year_families":2024,
                     "note":"שם רשמי במרשם: 'אספר' (= מיצד = מצד שמעון). חרדי. מקור: ויקיפדיה 2024 — 'קהילת מיצד מונה כמאתיים משפחות'."},
    "עמנואל":       {"council":"(מועצה מקומית)","founded":1983,"sector":"חרדי","compare":True,
                     "pop_reg":6605,"pop_wiki":None,"families":1200,"year_families":2025,
                     "note":"מועצה מקומית חרדית. מקור: 'מ-600 משפחות בתחילת הדרך, צמחה ליותר מ-1,200 משפחות' (מקור משני; מצוטט בויקיפדיה, JDN, hzahav). פרופיל למ\"ס לא כולל ספירת בא ישירה למועצות מקומיות."},
}

NEFASHOT_PER_HOUSEHOLD = {"חרדי":6.7, "דתי-לאומי":5.0, "מעורב":4.0, "חילוני":3.1}

# מבוגרים לבית-אב — מכויל אמפירית מול ביתר עילית (נתון רשמי 9,800 בתי אב מלמ"ס)
ADULTS_PER_HOUSEHOLD = {"חרדי":3.47, "דתי-לאומי":2.5, "מעורב":2.2, "חילוני":2.0}

# טעינת נתוני גילים מהמרשם — לחישוב מבוגרים 19+
def load_age_data():
    raw = json.loads(Path("raw_population.json").read_text(encoding="utf-8"))
    # אינדוקס לפי שם
    by_name = {}
    for r in raw:
        name = r.get("שם_ישוב", "").strip()
        if not name: continue
        adults = (int(r["גיל_19_45"]) + int(r["גיל_46_55"]) +
                  int(r["גיל_56_64"]) + int(r["גיל_65_פלוס"]))
        children_count = int(r["גיל_0_5"]) + int(r["גיל_6_18"])
        by_name[name] = {"adults": adults, "children": children_count,
                         "total": int(r["סהכ"])}
    return by_name

AGE_DATA = load_age_data()

# מיפוי שמות שלנו לשמות במרשם (אם שונים)
NAME_IN_REGISTRY = {
    "בית חגי": "חגי",
    "חלמיש": "נוה צוף",
    "עינב": "ענב",
    "עפרה": "עופרה",
    "מיצד": "אספר",
}

def adults_for(name):
    """מחזיר מספר מבוגרים 19+ של היישוב, אם הוא במרשם. אחרת None."""
    reg_name = NAME_IN_REGISTRY.get(name, name)
    return AGE_DATA.get(reg_name, {}).get("adults")


def classify(d):
    """
    מחזיר tuple: (סוג_נתון, אוכלוסייה, בתי_אב, מקור, רמת_ביטחון, fill)
    """
    reg = d.get("pop_reg")
    fam = d.get("families")
    hh_direct = d.get("households_direct")
    avg = NEFASHOT_PER_HOUSEHOLD[d["sector"]]
    est_from_fam = round(fam * avg) if fam else None

    # 0: בא רשמי (למ"ס/עירייה) + מרשם — שניהם רשמיים
    if hh_direct and reg:
        return ("רשמי", reg, hh_direct,
                f"מרשם 2026 + בא: עירייה/למ\"ס {d.get('year_hh','')}",
                "גבוהה", HARD_FILL)

    # 1: אין במרשם — רק דיווח משפחות
    if reg is None and fam:
        return ("דיווח קהילתי", est_from_fam, fam,
                f"ויקיפדיה {d.get('year_families','')}",
                "בינונית", MED_FILL)

    # 2: פער דרמטי (פי 4+ ו->500 נפש) — מרשם חלקי, דיווח משפחות אמין
    if (fam and reg and est_from_fam and
            est_from_fam > reg * 4 and est_from_fam > 500):
        return ("דיווח קהילתי", est_from_fam, fam,
                f"מרשם:{reg} (חלקי) | ויקי {d.get('year_families','')}: {fam} משפ׳",
                "בינונית", MED_FILL)

    # 3: יחס תואם בין families לאוכלוסייה (0.7-1.5x) — שני המקורות עקביים
    if reg is not None and fam is not None and est_from_fam:
        ratio = est_from_fam / reg
        if 0.7 <= ratio <= 1.5:
            return ("רשמי + מקור משפחות", reg, fam,
                    f"מרשם 2026 + ויקיפדיה {d.get('year_families','')}",
                    "גבוהה", HARD_FILL)

    # 4: יש מרשם בלבד (או families לא עקבי) — מרשם + אומדן בא מהמגזר
    if reg is not None:
        hh_est = round(reg / avg)
        return ("רשמי", reg, hh_est,
                f"מרשם 2026 | בא: אומדן ({avg} נפ׳/בא)",
                "גבוהה (פופ׳)", HARD_FILL)

    # 5: אין כלום
    return ("אומדן בלבד", None, None, "—", "—", SOFT_FILL)


def main():
    wb = load_workbook(XLSX)

    # אם הגיליון כבר קיים — נמחק ונבנה מחדש
    if "תצוגה לישיבה" in wb.sheetnames:
        del wb["תצוגה לישיבה"]
    ws = wb.create_sheet("תצוגה לישיבה", 1)  # נכנס במקום השני (אחרי README)
    ws.sheet_view.rightToLeft = True

    # === כותרת ===
    ws["A1"] = "נתוני אוכלוסייה ובתי אב — 38 יישובי משרד הביטחון"
    ws["A1"].font = Font(bold=True, size=16, color="1F4E79")
    ws.merge_cells("A1:J1")

    ws["A2"] = ("נכון ל-19/5/2026 | מקור עיקרי: מרשם רשות האוכלוסין (data.gov.il, מתעדכן שבועית). "
                "עמודת 'בתי אב לפי גילים' = מבוגרים 19+ ÷ ממוצע מבוגרים לבית-אב "
                "(3.47 חרדי / 2.5 דתי-לאומי / 2.2 מעורב — מכויל על נתוני למ\"ס לביתר).")
    ws["A2"].font = Font(italic=True, size=10, color="595959")
    ws.merge_cells("A2:L2")
    ws["A2"].alignment = Alignment(wrap_text=True, vertical="center")
    ws.row_dimensions[2].height = 45

    # === מקרא צבעים ===
    ws["A4"] = "מקרא"
    ws["A4"].font = BOLD
    legend = [
        ("נתון רשמי במרשם רשות האוכלוסין", HARD_FILL, "ביטחון גבוה — מתעדכן שבועית"),
        ("מספר משפחות מדווח (ויקי/קהילה)", MED_FILL, "ביטחון בינוני — לא רשמי, אך מקור משני אמין"),
        ("ללא נתון", SOFT_FILL, "אין מידע — דורש בירור ישיר"),
    ]
    for i, (label, fill, desc) in enumerate(legend, 5):
        c1 = ws.cell(row=i, column=1, value=label)
        c1.fill = fill
        c1.alignment = Alignment(horizontal="right", vertical="center")
        c1.border = BORDER
        c2 = ws.cell(row=i, column=2, value=desc)
        c2.font = NORMAL
        c2.alignment = Alignment(horizontal="right", vertical="center")
        ws.merge_cells(start_row=i, start_column=2, end_row=i, end_column=4)

    # === כותרות עמודות ===
    HEADER_ROW = 9
    headers = ["#", "יישוב", "מועצה", "מגזר", "סיווג הנתון",
               "אוכלוסייה", "מבוגרים 19+", "בתי אב (אומדן עיקרי)",
               "בתי אב (לפי גילים)", "שנת נתון משפ׳", "מקור", "הערה"]
    for col, h in enumerate(headers, 1):
        c = ws.cell(row=HEADER_ROW, column=col, value=h)
        c.fill = HEADER_FILL
        c.font = WHITE
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = BORDER
    ws.row_dimensions[HEADER_ROW].height = 42

    # === מיון: לפי מועצה, אז לפי אוכלוסייה יורד ===
    council_order = {"שומרון":1, "מטה בנימין":2, "גוש עציון":3, "הר חברון":4}
    items = [(name, d, classify(d)) for name, d in DATA.items()]
    # יישובי משב"ט (38) לעומת יישובי השוואה (חרדיים)
    yosh = [x for x in items if not x[1].get("compare")]
    beitar = [x for x in items if x[1].get("compare")]
    yosh.sort(key=lambda x: (council_order[x[1]["council"]],
                              -(x[2][1] or 0)))  # פופ' יורד בתוך מועצה
    # יישובי ההשוואה: ביתר ראשון, אחר כך לפי אוכלוסייה יורד
    beitar.sort(key=lambda x: (0 if x[0]=="ביתר עילית" else 1, -(x[2][1] or 0)))

    r = HEADER_ROW + 1
    current_council = None
    serial = 0
    for name, d, (kind, pop, hh, src, conf, fill) in yosh:
        if d["council"] != current_council:
            # שורת הפרדה למועצה
            current_council = d["council"]
            cc = ws.cell(row=r, column=1, value=f"— מועצה אזורית {current_council} —")
            cc.font = BOLD
            cc.fill = PatternFill("solid", fgColor="DCE6F1")
            cc.alignment = Alignment(horizontal="center", vertical="center")
            ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=10)
            r += 1

        serial += 1
        year_fam = d.get("year_families", "") if d.get("families") else \
                   d.get("year_hh", "") if d.get("households_direct") else ""
        note = d.get("note", "")

        # אומדן בתי אב לפי גילים — מבוגרים 19+ ÷ מבוגרים/בא לפי מגזר
        ads = adults_for(name)
        ads_per_hh = ADULTS_PER_HOUSEHOLD[d["sector"]]
        hh_by_age = round(ads / ads_per_hh) if ads else None

        values = [serial, name, d["council"], d["sector"], kind,
                  pop if pop is not None else "—",
                  ads if ads is not None else "—",
                  hh if hh is not None else "—",
                  hh_by_age if hh_by_age is not None else "—",
                  year_fam, src, note]
        for col, v in enumerate(values, 1):
            c = ws.cell(row=r, column=col, value=v)
            c.font = NORMAL
            c.border = BORDER
            c.alignment = Alignment(horizontal="center" if col in (1,4,5,6,7,8,9,10) else "right",
                                     vertical="center", wrap_text=True)
            c.fill = fill
        ws.row_dimensions[r].height = 28
        r += 1

    # === שורת סיכום ===
    r += 1
    total_pop = sum((c[2][1] or 0) for c in yosh)
    total_hh  = sum((c[2][2] or 0) for c in yosh)
    total_adults = sum((adults_for(n) or 0) for n,_,_ in yosh)
    total_hh_age = sum(round((adults_for(n) or 0) / ADULTS_PER_HOUSEHOLD[d["sector"]])
                       for n,d,_ in yosh)
    ws.cell(row=r, column=2, value="סך הכל — 38 יישובי משרד הביטחון")
    ws.cell(row=r, column=6, value=total_pop)
    ws.cell(row=r, column=7, value=total_adults)
    ws.cell(row=r, column=8, value=total_hh)
    ws.cell(row=r, column=9, value=total_hh_age)
    for col in range(1, 13):
        cell = ws.cell(row=r, column=col)
        cell.fill = HEADER_FILL
        cell.font = WHITE
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = BORDER
    ws.row_dimensions[r].height = 28
    r += 2

    # === יישובי השוואה — חרדיים ===
    ws.cell(row=r, column=1, value="להשוואה — יישובים חרדיים").font = TITLE
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=12)
    r += 1
    for idx, (name, d, (kind, pop, hh, src, conf, fill)) in enumerate(beitar, 1):
        ads = adults_for(name)
        hh_by_age = round(ads / ADULTS_PER_HOUSEHOLD[d["sector"]]) if ads else None
        values = [idx, name, d["council"], d["sector"], kind,
                  pop, ads or "—", hh, hh_by_age or "—",
                  d.get("year_hh", ""), src, d.get("note", "")]
        for col, v in enumerate(values, 1):
            c = ws.cell(row=r, column=col, value=v)
            c.font = BOLD
            c.border = BORDER
            c.alignment = Alignment(horizontal="center" if col in (1,4,5,6,7,8,9,10) else "right",
                                     vertical="center", wrap_text=True)
            c.fill = PatternFill("solid", fgColor="FFF2CC")
        ws.row_dimensions[r].height = 40
        r += 1

    # שורת סיכום ליישובי השוואה
    total_pop_chr = sum((c[2][1] or 0) for c in beitar)
    total_hh_chr  = sum((c[2][2] or 0) for c in beitar)
    ws.cell(row=r, column=2, value=f"סך הכל — {len(beitar)} יישובים חרדיים")
    ws.cell(row=r, column=6, value=total_pop_chr)
    ws.cell(row=r, column=8, value=total_hh_chr)
    for col in range(1, 13):
        cell = ws.cell(row=r, column=col)
        cell.fill = HEADER_FILL
        cell.font = WHITE
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = BORDER
    ws.row_dimensions[r].height = 28
    r += 3

    # ==========================================================
    # טבלה מסכמת להשוואה — שמות + מספרים בלבד
    # ==========================================================
    ALT_FILL_LOCAL = PatternFill("solid", fgColor="F2F2F2")

    # כותרת ראשית
    ws.cell(row=r, column=1, value="טבלה מסכמת להשוואה — אוכלוסייה ובתי אב")
    ws.cell(row=r, column=1).font = Font(bold=True, size=14, color="1F4E79")
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=12)
    r += 2

    # כותרות צד ימין / שמאל
    ws.cell(row=r, column=1, value=f"38 יישובי משרד הביטחון")
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=3)
    ws.cell(row=r, column=5, value=f"יישובים חרדיים להשוואה")
    ws.merge_cells(start_row=r, start_column=5, end_row=r, end_column=7)
    for col in (1, 5):
        c = ws.cell(row=r, column=col)
        c.fill = HEADER_FILL
        c.font = Font(color="FFFFFF", bold=True, size=12)
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = BORDER
    ws.row_dimensions[r].height = 24
    r += 1

    # subheaders
    sub_headers = [(1,"יישוב"), (2,"נפשות"), (3,"בתי אב"),
                   (5,"יישוב"), (6,"נפשות"), (7,"בתי אב")]
    for col, h in sub_headers:
        c = ws.cell(row=r, column=col, value=h)
        c.fill = PatternFill("solid", fgColor="4472C4")
        c.font = Font(color="FFFFFF", bold=True, size=10)
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = BORDER
    ws.row_dimensions[r].height = 22
    r += 1

    data_start = r
    max_rows = max(len(yosh), len(beitar))
    for i in range(max_rows):
        if i < len(yosh):
            n, d, (kind, pop, hh, *_) = yosh[i]
            ws.cell(row=r, column=1, value=n)
            ws.cell(row=r, column=2, value=pop if pop is not None else "—")
            ws.cell(row=r, column=3, value=hh  if hh  is not None else "—")
        if i < len(beitar):
            n, d, (kind, pop, hh, *_) = beitar[i]
            ws.cell(row=r, column=5, value=n)
            ws.cell(row=r, column=6, value=pop if pop is not None else "—")
            ws.cell(row=r, column=7, value=hh  if hh  is not None else "—")
        for col in (1,2,3,5,6,7):
            c = ws.cell(row=r, column=col)
            c.border = BORDER
            c.font = NORMAL
            c.alignment = Alignment(horizontal="center" if col in (2,3,6,7) else "right",
                                    vertical="center")
            if i % 2 == 0:
                c.fill = ALT_FILL_LOCAL
        ws.row_dimensions[r].height = 19
        r += 1

    # שורת סיכום
    sum_pop_yosh = sum((y[2][1] or 0) for y in yosh)
    sum_hh_yosh  = sum((y[2][2] or 0) for y in yosh)
    sum_pop_chr  = sum((b[2][1] or 0) for b in beitar)
    sum_hh_chr   = sum((b[2][2] or 0) for b in beitar)
    ws.cell(row=r, column=1, value="סך הכל")
    ws.cell(row=r, column=2, value=sum_pop_yosh)
    ws.cell(row=r, column=3, value=sum_hh_yosh)
    ws.cell(row=r, column=5, value="סך הכל")
    ws.cell(row=r, column=6, value=sum_pop_chr)
    ws.cell(row=r, column=7, value=sum_hh_chr)
    for col in (1,2,3,5,6,7):
        c = ws.cell(row=r, column=col)
        c.fill = HEADER_FILL
        c.font = WHITE
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = BORDER
    ws.row_dimensions[r].height = 24
    r += 1

    # === רוחב עמודות ===
    widths = [4, 17, 11, 11, 13, 11, 11, 14, 14, 9, 32, 46]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    # הרחבת עמודות הטבלה המסכמת — אם צריך
    ws.column_dimensions["A"].width = 17
    ws.column_dimensions["E"].width = 17

    ws.freeze_panes = "A10"
    ws.print_options.horizontalCentered = True
    ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True

    # שמירה
    wb.save(XLSX)

    # סטטיסטיקה
    hard = sum(1 for n,d,(k,p,h,s,c,f) in yosh if k.startswith("רשמי"))
    med  = sum(1 for n,d,(k,p,h,s,c,f) in yosh if k == "דיווח קהילתי")
    print(f"גיליון נוסף: 'תצוגה לישיבה' בקובץ {XLSX}")
    print(f"  רשמי (מרשם): {hard} יישובים")
    print(f"  דיווח קהילתי (לא רשמי): {med} יישובים")
    print(f"  סך אוכלוסייה משוערכת: {total_pop:,}")
    print(f"  סך בתי אב משוערכים: {total_hh:,}")


if __name__ == "__main__":
    main()
