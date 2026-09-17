"""
בונה את קובץ ה-Excel הסופי:
  גיליון 1: README — שקיפות ומגבלות
  גיליון 2: יישובים (כל הנתונים)
  גיליון 3: סיכום פר מועצה
  גיליון 4: מתודולוגיה ומקורות
"""
import csv
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT = Path(__file__).parent
IN_CSV = OUT / "consolidated.csv"
OUT_XLSX = OUT / "בתי_אב_38_יישובים.xlsx"

# צבעים
HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
ALT_FILL    = PatternFill("solid", fgColor="F2F2F2")
NOTE_FILL   = PatternFill("solid", fgColor="FFF2CC")
WHITE = Font(color="FFFFFF", bold=True, size=11)
BOLD  = Font(bold=True, size=11)
TITLE = Font(bold=True, size=14, color="1F4E79")
NORMAL = Font(size=11)
THIN = Side(border_style="thin", color="BFBFBF")
BORDER = Border(top=THIN, bottom=THIN, left=THIN, right=THIN)

def rtl(ws):
    ws.sheet_view.rightToLeft = True

def fit(ws, widths):
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

def style_header(ws, row, cols):
    for col in range(1, cols + 1):
        c = ws.cell(row=row, column=col)
        c.fill = HEADER_FILL
        c.font = WHITE
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = BORDER

# === קריאת CSV ===
rows = []
with open(IN_CSV, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        rows.append(r)

# ===================================================================
# גיליון 1: README
# ===================================================================
wb = Workbook()
ws = wb.active
ws.title = "README"
rtl(ws)

ws["A1"] = "בתי אב ב-38 יישובי משרד הביטחון + ביתר עילית להשוואה"
ws["A1"].font = Font(bold=True, size=16, color="1F4E79")
ws.merge_cells("A1:B1")

ws["A3"] = "מסמך זה"
ws["A3"].font = TITLE
ws["A4"] = ("מסכם את מספר התושבים ובתי האב ב-38 יישובי משרד הביטחון "
            "(המופיעים ברשימת זכאות נסיעות), בתוספת ביתר עילית כעיר חרדית להשוואה.")
ws["A4"].alignment = Alignment(wrap_text=True, vertical="top")
ws.row_dimensions[4].height = 40

ws["A6"] = "מקורות עיקריים"
ws["A6"].font = TITLE
sources = [
    ("מרשם רשות האוכלוסין וההגירה (data.gov.il)",
     "אוכלוסייה רשמית פר יישוב, מתעדכן שבועית. נכון ל-2026-05-17. "
     "מקור הכי מהימן לאוכלוסייה — אבל לא מספק מספר משקי בית."),
    ("ויקיפדיה — טבלאות המועצות האזוריות",
     "נתוני CBS נכון 2024-2025. שימשו לאימות צולב ולכמה יישובים שבהם מספר משפחות מוצג ישירות."),
    ("חיפושים פרטניים (אתרי goyosh, מועצות אזוריות, ויקיפדיה פר יישוב)",
     "לכל יישוב שהמרשם הרשמי הציג מספר חשוד-נמוך (מאחזים, יישובים חדשים שפוצלו ממאומה) — "
     "נשלף מספר משפחות עדכני מטקסט המאמר."),
    ("דוח אוכלוסייה של מועצת יש\"ע, ינואר 2025",
     "529,704 תושבים בכ-150 יישובים. שימש לאימות סכומי כלל יו\"ש."),
]
r = 7
for src, desc in sources:
    ws.cell(row=r, column=1, value=src).font = BOLD
    ws.cell(row=r, column=2, value=desc).alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[r].height = 45
    r += 1

ws.cell(row=r+1, column=1, value="מגבלות ואי-ודאות").font = TITLE
r += 2
limits = [
    ("אין מאגר רשמי 'משקי בית פר יישוב'",
     "למ\"ס מפרסם משקי בית רק לערים מעל 50K תושבים. עבור מועצות אזוריות — אין נתון רשמי."),
    ("רישום במרשם vs מציאות בשטח",
     "ביישובים חדשים/מאחזים שזה עתה הוכרו, רק חלק מהתושבים שינו רישום כתובת. "
     "לדוגמה: נריה במרשם=19, במציאות ~450 משפחות. במקרים אלו השתמשנו במספר המשפחות מהטקסט."),
    ("בתי אב מחושבים לפי ממוצע מגזרי",
     "כשאין מספר משפחות ישיר, חישבנו בתי-אב = אוכלוסייה ÷ ממוצע נפשות לבית-אב פר מגזר "
     "(7.8 לחרדי, 5.0 לדתי-לאומי, 4.0 למעורב). מקור: CBS משפחות 2024."),
    ("כל מספר כאן הוא אומדן",
     "למידע מדויק 100% — יש לפנות ישירות למזכירות היישוב או למועצה האזורית."),
]
for title, desc in limits:
    ws.cell(row=r, column=1, value=title).font = BOLD
    ws.cell(row=r, column=2, value=desc).alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[r].height = 45
    r += 1

fit(ws, [38, 70])

# ===================================================================
# גיליון 2: יישובים
# ===================================================================
ws2 = wb.create_sheet("יישובים")
rtl(ws2)

headers = ["#", "שם יישוב", "מועצה", "הוקם", "מגזר",
           "תושבים — מרשם 2026", "תושבים — ויקי 2025",
           "אוכלוסייה — אומדן עדכני",
           "משפחות (מקור ישיר)", "שנת נתון משפחות",
           "בתי אב — אומדן", "מקור אוכלוסייה", "אופן חישוב בתי-אב"]
for col, h in enumerate(headers, 1):
    ws2.cell(row=1, column=col, value=h)
style_header(ws2, 1, len(headers))
ws2.row_dimensions[1].height = 38

# סדר: לפי מועצה, ואז לפי שם. ביתר עילית בסוף נפרד.
yosh = [r for r in rows if r["שם"] != "ביתר עילית"]
beitar = [r for r in rows if r["שם"] == "ביתר עילית"]
order = {"שומרון":1, "מטה בנימין":2, "גוש עציון":3, "הר חברון":4}
yosh.sort(key=lambda r: (order.get(r["מועצה"], 99), r["שם"]))

r_idx = 2
for i, r in enumerate(yosh, 1):
    vals = [i, r["שם"], r["מועצה"], int(r["הוקם"]), r["מגזר"],
            int(r["תושבים_מרשם_2026"]) if r["תושבים_מרשם_2026"] else None,
            int(r["תושבים_ויקי_2025"]) if r["תושבים_ויקי_2025"] else None,
            int(r["אוכלוסייה_אומדן_עדכני"]) if r["אוכלוסייה_אומדן_עדכני"] else None,
            int(r["משפחות_מקור_ישיר"]) if r["משפחות_מקור_ישיר"] else None,
            int(r["שנת_משפחות"]) if r["שנת_משפחות"] else None,
            int(r["בתי_אב_אומדן"]) if r["בתי_אב_אומדן"] else None,
            r["מקור_אוכלוסייה"], r["אופן_חישוב_בתי_אב"]]
    for col, v in enumerate(vals, 1):
        c = ws2.cell(row=r_idx, column=col, value=v)
        c.font = NORMAL
        c.border = BORDER
        c.alignment = Alignment(horizontal="center" if col in (1,4,6,7,8,9,10,11) else "right",
                                vertical="center", wrap_text=True)
        if i % 2 == 0:
            c.fill = ALT_FILL
    r_idx += 1

# שורת סיכום 38
ws2.cell(row=r_idx, column=2, value="סך הכל 38 יישובי משרד הביטחון").font = BOLD
ws2.cell(row=r_idx, column=8, value=sum(int(r["אוכלוסייה_אומדן_עדכני"] or 0) for r in yosh)).font = BOLD
ws2.cell(row=r_idx, column=11, value=sum(int(r["בתי_אב_אומדן"] or 0) for r in yosh)).font = BOLD
for col in range(1, len(headers)+1):
    ws2.cell(row=r_idx, column=col).fill = HEADER_FILL
    ws2.cell(row=r_idx, column=col).font = WHITE
    ws2.cell(row=r_idx, column=col).border = BORDER
r_idx += 2

# ביתר להשוואה
ws2.cell(row=r_idx, column=2, value="להשוואה — עיר חרדית").font = TITLE
r_idx += 1
for r in beitar:
    vals = ["", r["שם"], r["מועצה"], int(r["הוקם"]), r["מגזר"],
            int(r["תושבים_מרשם_2026"]) if r["תושבים_מרשם_2026"] else None,
            int(r["תושבים_ויקי_2025"]) if r["תושבים_ויקי_2025"] else None,
            int(r["אוכלוסייה_אומדן_עדכני"]) if r["אוכלוסייה_אומדן_עדכני"] else None,
            "—", "—",
            int(r["בתי_אב_אומדן"]) if r["בתי_אב_אומדן"] else None,
            r["מקור_אוכלוסייה"], r["אופן_חישוב_בתי_אב"]]
    for col, v in enumerate(vals, 1):
        c = ws2.cell(row=r_idx, column=col, value=v)
        c.font = BOLD
        c.fill = NOTE_FILL
        c.border = BORDER
        c.alignment = Alignment(horizontal="center" if col in (1,4,6,7,8,11) else "right",
                                vertical="center", wrap_text=True)
    r_idx += 1

fit(ws2, [4, 16, 12, 8, 12, 14, 14, 16, 14, 11, 14, 32, 24])
ws2.freeze_panes = "A2"

# ===================================================================
# גיליון 3: סיכום פר מועצה
# ===================================================================
ws3 = wb.create_sheet("סיכום פר מועצה")
rtl(ws3)
ws3.cell(row=1, column=1, value="מועצה").font = BOLD
ws3.cell(row=1, column=2, value="# יישובים").font = BOLD
ws3.cell(row=1, column=3, value="תושבים").font = BOLD
ws3.cell(row=1, column=4, value="בתי אב (אומדן)").font = BOLD
ws3.cell(row=1, column=5, value="ממוצע נפשות לבית-אב").font = BOLD
style_header(ws3, 1, 5)

councils = {}
for r in yosh:
    c = r["מועצה"]
    pop = int(r["אוכלוסייה_אומדן_עדכני"] or 0)
    hh = int(r["בתי_אב_אומדן"] or 0)
    councils.setdefault(c, {"n":0, "pop":0, "hh":0})
    councils[c]["n"]  += 1
    councils[c]["pop"] += pop
    councils[c]["hh"]  += hh

ridx = 2
for c, d in sorted(councils.items(), key=lambda kv: -kv[1]["pop"]):
    ws3.cell(row=ridx, column=1, value=c)
    ws3.cell(row=ridx, column=2, value=d["n"])
    ws3.cell(row=ridx, column=3, value=d["pop"])
    ws3.cell(row=ridx, column=4, value=d["hh"])
    ws3.cell(row=ridx, column=5, value=round(d["pop"]/d["hh"], 1) if d["hh"] else "")
    for col in range(1, 6):
        ws3.cell(row=ridx, column=col).border = BORDER
        ws3.cell(row=ridx, column=col).alignment = Alignment(horizontal="center", vertical="center")
    ridx += 1

# שורת סיכום
ws3.cell(row=ridx, column=1, value="סך הכל 38 יישובים").font = BOLD
ws3.cell(row=ridx, column=2, value=sum(d["n"] for d in councils.values())).font = BOLD
ws3.cell(row=ridx, column=3, value=sum(d["pop"] for d in councils.values())).font = BOLD
ws3.cell(row=ridx, column=4, value=sum(d["hh"] for d in councils.values())).font = BOLD
total_pop = sum(d["pop"] for d in councils.values())
total_hh  = sum(d["hh"] for d in councils.values())
ws3.cell(row=ridx, column=5, value=round(total_pop/total_hh, 1) if total_hh else "").font = BOLD
for col in range(1, 6):
    ws3.cell(row=ridx, column=col).fill = HEADER_FILL
    ws3.cell(row=ridx, column=col).font = WHITE
    ws3.cell(row=ridx, column=col).border = BORDER
    ws3.cell(row=ridx, column=col).alignment = Alignment(horizontal="center", vertical="center")
ridx += 2

# ביתר נפרד
ws3.cell(row=ridx, column=1, value="להשוואה — ביתר עילית").font = TITLE
ridx += 1
b = next(r for r in rows if r["שם"] == "ביתר עילית")
ws3.cell(row=ridx, column=1, value="ביתר עילית (חרדי)")
ws3.cell(row=ridx, column=2, value=1)
ws3.cell(row=ridx, column=3, value=int(b["אוכלוסייה_אומדן_עדכני"]))
ws3.cell(row=ridx, column=4, value=int(b["בתי_אב_אומדן"]))
ws3.cell(row=ridx, column=5, value=round(int(b["אוכלוסייה_אומדן_עדכני"])/int(b["בתי_אב_אומדן"]), 1))
for col in range(1, 6):
    ws3.cell(row=ridx, column=col).fill = NOTE_FILL
    ws3.cell(row=ridx, column=col).font = BOLD
    ws3.cell(row=ridx, column=col).border = BORDER
    ws3.cell(row=ridx, column=col).alignment = Alignment(horizontal="center", vertical="center")

fit(ws3, [22, 14, 14, 18, 22])

# ===================================================================
# גיליון 4: מתודולוגיה
# ===================================================================
ws4 = wb.create_sheet("מתודולוגיה")
rtl(ws4)
ws4["A1"] = "מתודולוגיה ומקורות"
ws4["A1"].font = TITLE

methodology = [
    ("שלב 1: שאיבת אוכלוסייה רשמית",
     "API של data.gov.il, מאגר 'תושבים בישראל לפי ישובים וקבוצות גיל' "
     "(resource_id: 64edd0ee-3d5d-43ce-8562-c336c24dbc1f). "
     "נכון ל-2026-05-17. סופק על ידי רשות האוכלוסין וההגירה. "
     "מצא 31 מתוך 39 יישובים בשם המקורי, 4 נוספים בשמות חלופיים "
     "(בית חגי=חגי, חלמיש=נוה צוף, עינב=ענב, עפרה=עופרה)."),
    ("שלב 2: זיהוי מספרים חשודים",
     "ב-7 יישובים המרשם הציג מספרים נמוכים משמעותית מהמציאות בשטח (פי 2-100). "
     "סיבה: יישובים שזה עתה הוכרו כעצמאיים, רוב התושבים עדיין רשומים תחת היישוב האם. "
     "דוגמאות: נריה (מרשם 19, מציאות 450 משפחות), שבות רחל (42→150), אחיה (70→82)."),
    ("שלב 3: השלמת חוסרים",
     "ל-4 מאחזים שלא במרשם כלל (קידה, גבעת הראל, חוות גלעד, נופי נחמיה): "
     "נשלפו מספרי משפחות עדכניים מויקיפדיה, אתר המועצה האזורית, ואתרי goyosh.co.il / homee.co.il."),
    ("שלב 4: חישוב בתי-אב",
     "לכל יישוב שאין לו מספר משפחות ישיר: בתי-אב = אוכלוסייה ÷ ממוצע נפשות לבית-אב פר מגזר. "
     "ערכי הממוצע נלקחו מ-CBS דוח 'משפחות בישראל' 2024."),
    ("שלב 5: אימות סכומי",
     "סכום אוכלוסיית 38 היישובים = ~68,000 תושבים. "
     "סך אוכלוסיית יש\"ע (יש\"ע ינואר 2025): 529,704. "
     "כלומר 38 היישובים הם ~13% מאוכלוסיית יש\"ע — סביר עבור 38 יישובים מתוך כ-150."),
]
r = 3
for title, desc in methodology:
    ws4.cell(row=r, column=1, value=title).font = BOLD
    ws4.cell(row=r, column=2, value=desc).alignment = Alignment(wrap_text=True, vertical="top")
    ws4.row_dimensions[r].height = 75
    r += 1

# טבלת ממוצעי מגזר
ws4.cell(row=r+1, column=1, value="ממוצע נפשות לבית-אב פר מגזר").font = TITLE
r += 2
ws4.cell(row=r, column=1, value="מגזר").font = BOLD
ws4.cell(row=r, column=2, value="נפ׳/בא").font = BOLD
ws4.cell(row=r, column=3, value="הערה").font = BOLD
style_header(ws4, r, 3)
r += 1
sector_data = [
    ("חרדי", 7.8, "ביתר עילית, מודיעין עילית. ילודה ~6.5"),
    ("דתי-לאומי", 5.0, "ישובי יו\"ש דתיים. ילודה ~4.0"),
    ("מעורב", 4.0, "תקוע, רימונים"),
    ("חילוני", 3.1, "ממוצע ארצי, לצורך השוואה בלבד"),
]
for s, avg, note in sector_data:
    ws4.cell(row=r, column=1, value=s)
    ws4.cell(row=r, column=2, value=avg)
    ws4.cell(row=r, column=3, value=note)
    for col in range(1, 4):
        ws4.cell(row=r, column=col).border = BORDER
    r += 1

fit(ws4, [30, 50, 35])

# שמירה
wb.save(OUT_XLSX)
print(f"נשמר: {OUT_XLSX}")
print(f"גודל קובץ: {OUT_XLSX.stat().st_size:,} bytes")
