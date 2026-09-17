"""סורק את כל היישובים תחת מועצות השומרון/מטה בנימין/גוש עציון/הר חברון."""
import json, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
raw = json.loads(Path("raw_population.json").read_text(encoding="utf-8"))

TARGET = ["שומרון", "מטה בנימין", "גוש עציון", "הר חברון"]
for council in TARGET:
    print(f"\n=== מועצה: {council} ===")
    matches = [r for r in raw if r.get("מועצה_אזורית", "").strip() == council]
    matches.sort(key=lambda r: r.get("שם_ישוב", ""))
    for r in matches:
        name = r.get("שם_ישוב", "").strip()
        pop = r.get("סהכ", 0)
        print(f"  {name:30s}  סמל={r.get('סמל_ישוב')}  סהכ={pop}")
