"""מוריד פרופיל למ"ס לעמנואל וקורא דרך pdfplumber."""
import sys, requests, pdfplumber
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

URL = "https://www.cbs.gov.il/he/publications/DocLib/2026/local_authorities23/עמנואל.pdf"
OUT = Path(__file__).parent
PDF = OUT / "emanuel_cbs.pdf"

if not PDF.exists():
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    PDF.write_bytes(r.content)

with pdfplumber.open(PDF) as pdf:
    for i, p in enumerate(pdf.pages, 1):
        text = p.extract_text() or ""
        # חיפוש שדות רלוונטיים
        if any(kw in text for kw in ["משק", "משקי", "תיב יקש", "תיב קשמ", "תוחפש", "תושפ"]):
            print(f"=== עמוד {i} ===")
            print(text[:3500])
            print()
