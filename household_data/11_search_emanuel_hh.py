"""מחפש במפורש את שדה משקי הבית בכל עמודי הפרופיל של עמנואל."""
import sys, pdfplumber, re
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

with pdfplumber.open("emanuel_cbs.pdf") as pdf:
    print(f"מספר עמודים: {len(pdf.pages)}")
    for i, p in enumerate(pdf.pages, 1):
        text = p.extract_text() or ""
        # מילות מפתח בעברית עם RTL הפוך:
        # "משקי בית" → "תיב יקשמ" / "תיב קשמ"
        # "ממוצע" → "עצוממ"
        # "מספר" → "רפסמ"
        # "תיב יקש" appears, search for context
        for kw in ["תיב יקשמ", "תיב קשמ", "ןדמוא", "תוחפשמ", "םייפלא"]:
            for m in re.finditer(re.escape(kw), text):
                start = max(0, m.start()-50)
                end = min(len(text), m.end()+80)
                ctx = text[start:end].replace("\n", " | ")
                print(f"עמוד {i} | מצא '{kw}': {ctx}")
        print()
