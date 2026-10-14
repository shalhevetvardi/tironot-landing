#!/usr/bin/env python3
"""בדפים שמבקרים רואים: אין מקף ארוך (— או –), ואין חץ בקישור או בכפתור.

שלהבת, 14-10-2026: "אצלנו אין חיצים בהנעות לפעולה", ו"שאין מקפים ארוכים באף חלק בדף". באותו יום הוסרו 39 מקפים
ארוכים מדף המכירה, 99 מדף השאלות ו-40 מדף הבוגרים, ותשעה חיצים מקישורים ומכפתורים (אחד מהם נוצר מקוד, ב-39 כפתורי "לשיחה עם נועם" בדף השאלות). נבדק רק טקסט שרואים: לא <script>, לא <style>
ולא הערות HTML. מקור שמייצר טקסט לדפים (המפיץ של תאריכי המחזור, מחולל כרטיסי הבוגרים ב-sales-automation) כבר כותב
מקף רגיל; אם הבדיקה נכשלת על טקסט שנכתב שם, מתקנים במקור ולא רק בדף.

    python3 scripts/test-typography.py      ← "כל הבדיקות עברו", או רשימת המקומות ויציאה 1
"""
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DASHES = re.compile("[—–]")
ARROW_IN_LINK = re.compile(r"<(a|button)\b[^>]*>((?:(?!</\1>).)*?[←→»](?:(?!</\1>).)*)</\1>", re.S)


def visible(html: str) -> str:
    """הדף בלי script, style והערות. אורך זהה, כדי שמספרי השורות יישארו נכונים."""
    for pat in (r"(?is)<(script|style)\b.*?</\1>", r"(?s)<!--.*?-->"):
        html = re.sub(pat, lambda m: re.sub(r"[^\n]", " ", m.group(0)), html)
    return html


def script_strings(html: str):
    """מחרוזות בתוך <script> (בלי הערות JS): טקסט שקוד מכניס לדף, כמו כפתור שנוסף בזמן הטעינה.
    נמדד 14-10-2026: בדף השאלות 39 כפתורי "לשיחה עם נועם" נוצרו מ-JS עם חץ, והבדיקה של הטקסט הסטטי לא ראתה אותם."""
    for m in re.finditer(r"(?is)<script\b[^>]*>(.*?)</script>", html):
        js = re.sub(r"(?s)/\*.*?\*/", lambda x: re.sub(r"[^\n]", " ", x.group(0)), m.group(1))
        js = re.sub(r"(?m)(^|[^:\\])//.*$", lambda x: x.group(1) + " " * (len(x.group(0)) - len(x.group(1))), js)
        for sm in re.finditer(r"'(?:[^'\\\n]|\\.)*'|\"(?:[^\"\\\n]|\\.)*\"|`(?:[^`\\]|\\.)*`", js):
            yield m.start(1) + sm.start(), sm.group(0)


def page_problems(rel: str, html: str) -> list:
    text = visible(html)
    line = lambda i: text.count("\n", 0, i) + 1                        # noqa: E731
    out = [f"{rel}:{line(m.start())}: מקף ארוך: ...{text[max(0, m.start() - 40):m.end() + 20].strip()}..."
           for m in DASHES.finditer(text)]
    out += [f"{rel}:{line(m.start())}: חץ בקישור או בכפתור: {re.sub(r'<[^>]+>', '', m.group(2)).strip()[:60]}"
            for m in ARROW_IN_LINK.finditer(text)]
    out += [f"{rel}:{html.count(chr(10), 0, i) + 1}: חץ או מקף ארוך בטקסט שקוד מכניס לדף: {lit[:60]}"
            for i, lit in script_strings(html) if re.search("[←→»\u2014\u2013]", lit)]
    return out


def pages() -> list:
    return subprocess.run(["git", "-C", str(ROOT), "ls-files", "*.html"], capture_output=True, text=True, check=True).stdout.split()


if __name__ == "__main__":
    files = pages()
    if len(files) < 5:
        print("לא נמצאו דפים - הבדיקה עצמה שבורה")
        sys.exit(2)
    bad = [p for rel in files for p in page_problems(rel, (ROOT / rel).read_text(encoding="utf-8"))]
    if bad:
        print("\n".join(bad))
        sys.exit(1)
    print("כל הבדיקות עברו")
