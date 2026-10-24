#!/usr/bin/env python3
"""רצועת תגובות הבוגרים מאינסטגרם ב"נעים להכיר" של index.html (24-10-2026).

המקור: scripts/cold-page-data/ig-comments.json (ציטוטים Q-0308 עד Q-0319 במאגר "ציטוטים לדפים" בדשבורד,
בלי Q-0313 שהוסר לבקשת שלהבת), והצילומים ב-students/ig/.
הרצועה יושבת מחוץ למשבצות של הדשבורד (בלי tm-slot), ולכן פרסום מהדשבורד לא נוגע בה.
הסקריפט כותב אותה מחדש בין שני הסימונים, ובטוח להרצה חוזרת. אחריו מריצים את build_cold_page.py,
כדי ש-hatzaa.html יקבל אותה גם.
"""
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "index.html"
DATA = ROOT / "scripts" / "cold-page-data" / "ig-comments.json"
START, END = "<!-- ig-strip -->", "<!-- /ig-strip -->"
ANCHOR = 'data-slot="intro-shots"'
SLOT_CLOSE = "<!-- /tm-slot --></div>"

CSS = """  /* רצועת תגובות אינסטגרם ב"נעים להכיר" (24-10-2026, scripts/build_ig_strip.py): צילומים רחבים ונמוכים,
     ולכן כרטיס נמוך ולבן ולא בגובה של הודעת וואטסאפ */
  .tm-shots--ig.is-strip { --strip-h: 116px; }
  .tm-shots--ig.is-strip .tm-shot, .tm-shots--ig.is-strip .tm-shot button { background: #fff; }
  @media (min-width: 900px) { .tm-shots--ig.is-strip { --strip-h: 146px; } }
"""
CSS_ANCHOR = "  /* חשש בלי תוכן אינו מוצג"


def strip_html(comments):
    figs = "".join(
        f'<figure class="tm-shot"><button type="button" aria-label="הגדלת התגובה של {html.escape(c["name"])}">'
        f'<img src="{c["src"]}" alt="{html.escape(c["name"] + ": " + c["alt"])}" loading="lazy"></button></figure>'
        for c in comments)
    return (f'{START}\n    <p class="tm-strip-cap">ומה בוגרים כותבים עליי באינסטגרם</p>'
            f'\n    <div class="tm-shots tm-shots--ig" data-strip="1">{figs}</div>{END}')


def main():
    comments = json.loads(DATA.read_text(encoding="utf-8"))
    missing = [c["src"] for c in comments if not (ROOT / c["src"]).is_file()]
    if missing:
        sys.exit(f"חסרים צילומים: {missing}")
    h = PAGE.read_text(encoding="utf-8")
    block = strip_html(comments)
    if START in h:
        a, z = h.index(START), h.index(END) + len(END)
        h = h[:a] + block + h[z:]
    else:
        i = h.find(ANCHOR)
        j = h.find(SLOT_CLOSE, i)
        if i < 0 or j < 0:
            sys.exit("רצועת ההודעות ב'נעים להכיר' לא נמצאה")
        j += len(SLOT_CLOSE)
        h = h[:j] + "\n    " + block + h[j:]
    if ".tm-shots--ig.is-strip" not in h:
        if h.count(CSS_ANCHOR) != 1:
            sys.exit("לא נמצא המקום לעיצוב של הרצועה")
        h = h.replace(CSS_ANCHOR, CSS + CSS_ANCHOR)
    PAGE.write_text(h, encoding="utf-8")
    print(f"נכתבה רצועה של {len(comments)} תגובות ב-{PAGE.name}")


if __name__ == "__main__":
    main()
