#!/usr/bin/env python3
"""import_faq_quotes_data.py - מביא לריפו את הבחירות של שלהבת לרצועות הציטוטים בדף השאלות (13-10-2026).

    python3 scripts/import_faq_quotes_data.py            # כותב את scripts/faq-quotes-data/*.json
    python3 scripts/import_faq_quotes_data.py --check    # לא כותב; יוצא בכשל אם הקבצים בריפו לא מעודכנים

סבבי הבחירה והעריכה נעשים בתיקיית עבודה במחשב (~/Documents/aimprove-demos/ציטוטים-לשאלות/). כדי שהדף לא יהיה
תלוי במחשב אחד, מה שמוצג בדף נשמר כאן בריפו, ו-scripts/build_faq_quotes.py בונה ממנו.

הריפו ציבורי, ולכן נכנס רק מה שכבר מוצג בדף השאלות:
  * רק שאלות q07-q41 (q01-q05 הן לשוניות בדף המכירה, והבחירות שלהן מנוהלות בדשבורד עד הפרסום).
  * בלי פריטים שסומנו "exclude" בקובץ העבודה.
  * מכל פריט רק qid, name, role, photo, text; ומכל שאלה רק id ונוסח השאלה.
אחרי הרצה: python3 scripts/build_faq_quotes.py, ואז python3 scripts/test-faq-quotes.py.

הנתונים שבריפו הם המקור של הדף, וקובץ העבודה הוא הטיוטה שממנה הם מתעדכנים. לכן הסקריפט מדפיס, כרטיס אחר כרטיס, מה
ישתנה בנתונים שבריפו. שינוי ברשימה שלא אתה עשית פירושו שהנתונים שבריפו חדשים מקובץ העבודה (תיקון שנעשה ממחשב אחר,
או ישירות בריפו): לא כותבים, אלא מעדכנים קודם את קובץ העבודה. מריצים --check לפני הכתיבה כדי לראות את הרשימה.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "scripts" / "faq-quotes-data"
WORK = Path.home() / "Documents" / "aimprove-demos" / "ציטוטים-לשאלות"
FAQ_RANGE = range(7, 42)
FIELDS = ("qid", "name", "role", "photo", "text")


def build(placements: dict, items: list) -> dict:
    ids = [f"q{n:02d}" for n in FAQ_RANGE]
    out_p = {}
    for qid in ids:
        rows = [{k: r.get(k) or "" for k in FIELDS} for r in placements.get(qid, []) if not r.get("exclude")]
        if rows:
            out_p[qid] = rows
    out_q = [{"id": str(x["id"]).lower(), "q": x["q"]} for x in items if str(x["id"]).lower() in out_p]
    return {"placements.json": out_p, "questions.json": out_q}


def changes(old: dict, new: dict) -> list:
    """מה ישתנה בנתונים שבריפו, שורה לכל כרטיס. נועד לכך שייבוא מקובץ עבודה ישן לא ימחק בשקט תיקון שכבר בריפו."""
    out = []
    for q in sorted(set(old) | set(new)):
        a, b = old.get(q, []), new.get(q, [])
        ka, kb = [r["qid"] for r in a], [r["qid"] for r in b]
        for qid in dict.fromkeys(ka + kb):
            ra, rb = [r for r in a if r["qid"] == qid], [r for r in b if r["qid"] == qid]
            who = (rb or ra)[0].get("name", "")
            if len(ra) != len(rb):
                out.append(f"{q} {qid} {who}: {'נוסף' if len(rb) > len(ra) else 'הוסר'}")
                continue
            fields = sorted({k for x, y in zip(ra, rb) for k in FIELDS if x.get(k) != y.get(k)})
            if fields:
                out.append(f"{q} {qid} {who}: השתנה {', '.join(fields)}")
        if ka != kb and sorted(ka) == sorted(kb):
            out.append(f"{q}: סדר הכרטיסים השתנה")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--placements", default=str(WORK / "סבב2" / "placements-final.json"))
    ap.add_argument("--items", default=str(WORK / "items.json"))
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    files = build(json.loads(Path(args.placements).read_text(encoding="utf-8")),
                  json.loads(Path(args.items).read_text(encoding="utf-8")))
    current = DATA / "placements.json"
    diff = changes(json.loads(current.read_text(encoding="utf-8")) if current.exists() else {}, files["placements.json"])
    if diff:
        print(f"מה ישתנה בנתונים שבריפו ({len(diff)}):")
        for line in diff[:60]:
            print("  " + line)
        if len(diff) > 60:
            print(f"  ועוד {len(diff) - 60}")
    stale = []
    for name, data in files.items():
        text = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
        path = DATA / name
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            stale.append(name)
            if not args.check:
                DATA.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
    n = sum(len(v) for v in files["placements.json"].values())
    print(f"שאלות: {len(files['placements.json'])}, ציטוטים: {n}" + (f" | {'לא מעודכן' if args.check else 'נכתב'}: {', '.join(stale)}" if stale else " | הכול מעודכן"))
    return 1 if (args.check and stale) else 0


if __name__ == "__main__":
    sys.exit(main())
