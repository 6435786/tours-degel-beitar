"""מוריד את פרופיל ה-CBS של ביתר עילית ומפיץ את כל המספרים."""
import sys, requests, pdfplumber
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

OUT = Path(__file__).parent
PDF = OUT / "beitar_cbs_profile.pdf"

URL = "https://www.cbs.gov.il/he/publications/DocLib/2026/local_authorities23/ביתר עילית.pdf"

if not PDF.exists():
    print(f"מוריד {URL}...")
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    PDF.write_bytes(r.content)
    print(f"נשמר: {PDF} ({len(r.content):,} bytes)")

with pdfplumber.open(PDF) as pdf:
    print(f"מספר עמודים: {len(pdf.pages)}\n")
    for i, page in enumerate(pdf.pages, 1):
        text = page.extract_text() or ""
        print(f"=== עמוד {i} ===")
        print(text)
        print()
