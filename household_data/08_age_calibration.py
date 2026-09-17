"""
משתמש בנתוני הגילים מ-data.gov.il לאומדן עצמאי של בתי אב.
שיטה: סך מבוגרים 19+ ÷ ממוצע מבוגרים לבית-אב.

הממוצע נמדד אמפירית על ביתר (שיש לנו לה נתון רשמי).
"""
import json, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
raw = json.loads(Path("raw_population.json").read_text(encoding="utf-8"))


def get(name_options):
    for opt in name_options:
        for r in raw:
            if r.get("שם_ישוב", "").strip() == opt:
                return r
    return None


def adults(r):
    return (int(r["גיל_19_45"]) + int(r["גיל_46_55"]) +
            int(r["גיל_56_64"]) + int(r["גיל_65_פלוס"]))


def children(r):
    return int(r["גיל_0_5"]) + int(r["גיל_6_18"])


# === כיול על ביתר ===
beitar = get(["ביתר עילית"])
b_pop = int(beitar["סהכ"])
b_adults = adults(beitar)
b_children = children(beitar)
b_hh_official = 9800  # למ"ס

print("=== כיול ביתר עילית (נתון בתי אב רשמי מלמ\"ס) ===")
print(f"  אוכלוסייה במרשם:      {b_pop:,}")
print(f"  ילדים 0-18:           {b_children:,} ({b_children/b_pop*100:.1f}%)")
print(f"  מבוגרים 19+:          {b_adults:,} ({b_adults/b_pop*100:.1f}%)")
print(f"  בתי אב לפי למ\"ס:      {b_hh_official:,}")
print(f"  מבוגרים לבית-אב:      {b_adults/b_hh_official:.2f}")
print(f"  נפ׳ לבית-אב:          {b_pop/b_hh_official:.2f}")

# === בדיקה על יישובים דתיים-לאומיים גדולים (ידועים) ===
print("\n=== יישובים דתיים-לאומיים מבוססים — לבדיקה ===")
TEST = ["שילה", "עפרה", "טלמון", "עלי", "כוכב השחר", "ברכה", "תקוע"]
print(f"{'יישוב':12} {'תושבים':>8} {'ילדים':>7} {'מבוגרים':>9} {'%ילדים':>8} {'מבוגר/בא @2.5':>14} {'נפ׳/בא @2.5':>13}")
for name in TEST:
    r = get([name, name.replace(" ", "")])
    if not r: continue
    pop = int(r["סהכ"])
    ad = adults(r)
    ch = children(r)
    hh_25 = round(ad / 2.5)
    print(f"{name:12} {pop:>8,} {ch:>7,} {ad:>9,} {ch/pop*100:>7.0f}% {hh_25:>14,} {pop/hh_25:>13.1f}")

# === בדיקה — נריה (מרשם מציג 19 בלבד) ===
print("\n=== נריה — בדיקת השערת 'רישום חלקי' ===")
nerya = get(["נריה"])
if nerya:
    pop = int(nerya["סהכ"])
    ad = adults(nerya)
    ch = children(nerya)
    print(f"  במרשם: {pop} תושבים | ילדים: {ch} | מבוגרים: {ad}")
    print(f"  אם 450 משפחות אמת — מצופים כ-1,800-2,250 תושבים → המרשם משקף רישום של 1% בלבד")

# === ניסוי: אם נחשב 38 יישובי משב\"ט לפי שיטת הגילים ===
print("\n=== סיכום: 38 יישובים לפי שיטת המבוגרים ===")
SETTLEMENTS_BY_NAME = [
    ("אבני חפץ","דל"),("איתמר","דל"),("אלון מורה","דל"),("ברכה","דל"),
    ("חרמש","דל"),("יצהר","דל"),("מבוא דותן","דל"),("ענב","דל"),
    ("רחלים","דל"),("שבי שומרון","דל"),
    ("דולב","דל"),("נוה צוף","דל"),("טלמון","דל"),("כוכב השחר","דל"),
    ("מעלה לבונה","דל"),("מעלה מכמש","דל"),("נחליאל","דל"),("עטרת","דל"),
    ("עלי","דל"),("עמיחי","דל"),("עופרה","דל"),("פסגות","דל"),("שילה","דל"),
    ("כרמי צור","דל"),("תקוע","מע"),("חגי","דל"),("רימונים","מע"),
    # מאחזים — נתונים חלקיים במרשם:
    ("אחיה","דל"),("גבעות הרואה","דל"),("חרשה","דל"),("עדי עד","דל"),
    ("שבות רחל","דל"),("נריה","דל"),("כרם רעים","דל"),
]
DIVISORS = {"חר":3.5, "דל":2.5, "מע":2.2}  # מבוגרים לבית אב

total_pop = total_adults = total_children = total_hh = 0
unregistered_count = 0
for name, sect in SETTLEMENTS_BY_NAME:
    r = get([name])
    if not r:
        unregistered_count += 1
        continue
    pop = int(r["סהכ"])
    ad = adults(r)
    ch = children(r)
    hh = round(ad / DIVISORS[sect])
    total_pop += pop
    total_adults += ad
    total_children += ch
    total_hh += hh

print(f"  סה\"כ במרשם:             {total_pop:,}")
print(f"  ילדים 0-18:             {total_children:,} ({total_children/total_pop*100:.0f}%)")
print(f"  מבוגרים 19+:            {total_adults:,}")
print(f"  בתי אב לפי שיטת גילים:  {total_hh:,}")
print(f"  ממוצע נפשות לבית-אב:    {total_pop/total_hh:.1f}")
print(f"  יישובים שלא נמצאו במרשם: {unregistered_count} (מאחזים)")
