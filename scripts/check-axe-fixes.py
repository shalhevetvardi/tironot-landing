#!/usr/bin/env python3
"""בדיקה שתיקוני הנגישות של סריקת axe (12-10-2026) עדיין במקומם.

שימוש: python3 scripts/check-axe-fixes.py [שורש-הריפו]
קוד יציאה 0 = כל התיקונים במקום, 1 = לפחות תיקון אחד נעלם.
Stdlib בלבד. זו לא סריקת נגישות: היא רק מוודאת שהשורות שתוקנו לא חזרו.
"""
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
fails = []


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def check(ok, msg):
    if not ok:
        fails.append(msg)


# A. כפתור "פרטיות" הצף: בלי opacity (היה .55, ניגודיות 3.2-3.4)
banner = read("consent-banner.js")
m = re.search(r"function addReopener\(\) \{(.*?)\n    \}\n", banner, re.S)
check(m is not None, "consent-banner.js: הפונקציה addReopener לא נמצאה")
if m:
    check("opacity" not in m.group(1),
          "consent-banner.js: ב-addReopener חזר opacity (כפתור הפרטיות הצף, ניגודיות 3.2-3.4)")

# B. פסקת ה-hero: בלי opacity (היה .94, ניגודיות 4.46)
index = read("index.html")
m = re.search(r"\.hero__sub \{([^}]*)\}", index)
check(m is not None, "index.html: הכלל .hero__sub לא נמצא")
if m:
    check("opacity" not in m.group(1), "index.html: ב-.hero__sub חזר opacity (ניגודיות 4.46)")

# C. כל iframe שנוצר ב-JavaScript מקבל title לפני src
for rel in ("index.html", "faq/index.html"):
    lines = read(rel).splitlines()
    created = [i for i, ln in enumerate(lines) if "createElement('iframe')" in ln]
    check(len(created) == 2, f"{rel}: נמצאו {len(created)} יצירות iframe במקום 2 (נדרש לעדכן את הבדיקה)")
    for i in created:
        window = "\n".join(lines[i + 1:i + 3])
        t = window.find("iframe.title =")
        s = window.find("iframe.src =")
        check(t != -1 and (s == -1 or t < s),
              f"{rel}:{i + 1}: ל-iframe שנוצר כאן אין iframe.title לפני iframe.src")

# D. התאמות צבע טקסט (כל אחת: מחרוזת שחייבת להיות, ומחרוזת שאסור שתחזור)
COLOUR = [
    ("index.html", ".jrn-bridge { margin-top: 42px; font-size: clamp(15px, 1.6vw, 17px); font-weight: 600; color: #fff; }",
     ".jrn-bridge { margin-top: 42px; font-size: clamp(15px, 1.6vw, 17px); font-weight: 600; color: rgba(255,255,255,.82); }"),
    ("index.html", ".proof__ceiling .accent-blue { color: #226EBF; }"),
    ("index.html", 'style="color:#5D58F2">חני', 'style="color:var(--purple)">חני'),
    ("index.html", 'style="color:#8A6E00">', 'style="color:#9A7B00">'),
    ("faq/index.html", "color:#557594; text-align:center", "color:#5a7a9a; text-align:center"),
    ("faq/index.html", ".jrn-step--done .jrn-label { color: #058657;", ".jrn-step--done .jrn-label { color: var(--green);"),
    ("faq/index.html", '.cat-card[data-cat="fit"] .card-desc { opacity: 1; }'),
    ("bogrim/index.html", "color: rgba(255,255,255,0.65); max-width: 720px;", "color: rgba(255,255,255,0.45); max-width: 720px;"),
    ("usa/index.html", "footer{text-align:center; color:#766F86;", "footer{text-align:center; color:#8A8398;"),
    ("usa/index.html", ".bl a{color:#2067B2}"),
    ("usa/en/index.html", "footer{text-align:center; color:#766F86;", "footer{text-align:center; color:#8A8398;"),
    ("usa/en/index.html", ".bl a{color:#2067B2}"),
    ("usa/en/index.html", ".links .row span{display:block; color:#B9B2D7;", ".links .row span{display:block; color:#A79ECC;"),
]
for entry in COLOUR:
    rel, must = entry[0], entry[1]
    must_not = entry[2] if len(entry) > 2 else None
    text = read(rel)
    check(must in text, f"{rel}: חסר התיקון {must!r}")
    if must_not:
        check(must_not not in text, f"{rel}: חזר הערך הישן {must_not!r}")

if fails:
    print("FAIL:")
    for f in fails:
        print(" -", f)
    sys.exit(1)
print("OK: כל תיקוני axe במקומם")
