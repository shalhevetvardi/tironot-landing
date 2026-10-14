#!/usr/bin/env python3
"""בכל דף שכתוב בו המחיר 9,300, לידו כתוב שאפשר לקבל הטבה של 1,400 ₪ בשיחה עם נועם.

שלהבת, 14-10-2026: "תמיד ליד 9,300 צריך להופיע שאם רוצים 1,400 ש"ח הנחה, אפשר לדבר עם נועם."
"ליד" = עד WINDOW תווים מטקסט הדף (בלי תגיות), לפני המחיר או אחריו.

דפי ארה"ב (usa/) מוחרגים: לא הוכרע אם ההטבה דרך נועם חלה על משתתפים מחו"ל (14-10-2026).
כשזה יוכרע - להוריד את ההחרגה, או לכתוב כאן למה היא נשארת.

    python3 scripts/test-price-noam.py      ← "כל הבדיקות עברו", או רשימת המקומות החסרים ויציאה 1
"""
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
WINDOW = 150
PRICE = re.compile(r"9[,.]?300")
EXEMPT_PREFIXES = ("usa/",)


def page_text(html: str) -> str:
    html = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", html)
    html = re.sub(r"(?s)<!--.*?-->", " ", html)
    html = re.sub(r"<[^>]+>", " ", html)
    html = html.replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", html)


def problems() -> list:
    files = subprocess.run(["git", "-C", str(ROOT), "ls-files", "*.html"],
                           capture_output=True, text=True, check=True).stdout.split()
    out, seen = [], 0
    for rel in files:
        if rel.startswith(EXEMPT_PREFIXES):
            continue
        text = page_text((ROOT / rel).read_text(encoding="utf-8"))
        for m in PRICE.finditer(text):
            seen += 1
            near = text[max(0, m.start() - WINDOW):m.end() + WINDOW]
            if "1,400" not in near or "נועם" not in near:
                out.append(f"{rel}: ...{text[max(0, m.start() - 60):m.end() + 60].strip()}...")
    if seen == 0:
        out.append("לא נמצא אף מופע של 9,300 בדפים - כנראה שהבדיקה עצמה שבורה (או שהמחיר השתנה ויש לעדכן אותה)")
    return out


if __name__ == "__main__":
    bad = problems()
    if bad:
        print("ליד המחיר 9,300 חסר שאפשר לקבל הטבה של 1,400 ₪ בשיחה עם נועם:")
        print("\n".join(f"  - {b}" for b in bad))
        sys.exit(1)
    print("כל הבדיקות עברו")
