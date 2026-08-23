#!/usr/bin/env python3
"""יוצר את טבלת אירועי-המשפך של דף הנחיתה ב-Airtable.

הרצה חד-פעמית. אחריה יש להציב את מזהה הטבלה שמודפס כאן בתוך
AIRTABLE_EVENTS_TABLE_ID ב-wrangler.toml של ריפו aimprove-redirector,
ולפרוס את ה-Worker - בלי זה POST /e מחזיר 204 תקין ולא כותב כלום.

בטוח להרצה חוזרת: אם הטבלה כבר קיימת הסקריפט מדפיס את מזהה הקיימת ויוצא
בלי ליצור כפילות.

    export AIRTABLE_API_KEY=...   # או: . ~/קוד/sales-automation/.env
    python3 scripts/create-events-table.py
"""
import json
import os
import sys
import urllib.error
import urllib.request

BASE = "app5fKvxuzbFb0stR"
TABLE_NAME = "אירועי משפך - דף נחיתה"

FIELDS = [
    ("ts",           "singleLineText", None, "חותמת זמן ISO של האירוע"),
    ("vid",          "singleLineText", None, "מזהה-ביקור אפמרלי. חי ב-sessionStorage בלבד, מת עם סגירת הלשונית. מאחד את שורות אותו ביקור - ואין לו שום שימוש אחר"),
    ("event",        "singleLineText", None, "view / price / cta / end"),
    ("page",         "singleLineText", None, "איזה דף (index)"),
    ("src",          "singleLineText", None, "קוד-מקור הקמפיין, אם הגיעו דרך לינק מתויג"),
    ("depth",        "singleLineText", None, "הסקשן העמוק ביותר שנראה: hero/intro/story/proofs/roadmap/price/video/final"),
    ("seconds",      "number",         {"precision": 0}, "שניות על הדף עד היציאה"),
    ("cta_kind",     "singleLineText", None, "noam / calendly / video"),
    ("device_class", "singleLineText", None, "mobile / tablet / desktop"),
    ("country",      "singleLineText", None, "קוד מדינה מ-Cloudflare"),
    ("ip_hash",      "singleLineText", None, "SHA256(IP + מלח מתחלף-יומית). לא IP, ולא מזהה קבוע"),
]


def api(method, path, payload=None):
    req = urllib.request.Request(
        f"https://api.airtable.com/v0/{path}",
        method=method,
        data=json.dumps(payload).encode() if payload else None,
        headers={
            "Authorization": f"Bearer {os.environ['AIRTABLE_API_KEY']}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def main():
    if not os.environ.get("AIRTABLE_API_KEY"):
        sys.exit("חסר AIRTABLE_API_KEY בסביבה.")

    existing = api("GET", f"meta/bases/{BASE}/tables")
    for t in existing["tables"]:
        if t["name"] == TABLE_NAME:
            print(f"הטבלה כבר קיימת - לא נוצרה מחדש.\n  מזהה: {t['id']}")
            return

    body = {
        "name": TABLE_NAME,
        "description": (
            "אירועי משפך אנונימיים מדף הנחיתה של טירונות. שורה לכל אירוע; "
            "vid מאחד את שורות אותו ביקור. אין עוגיות, אין IP גולמי, ואין שום "
            "מזהה אישי - אותו מודל פרטיות בדיוק של טבלת הקליקים. "
            "שמירה: עד 6 חודשים."
        ),
        "fields": [
            {"name": n, "type": t, **({"options": o} if o else {}), "description": d}
            for n, t, o, d in FIELDS
        ],
    }
    try:
        created = api("POST", f"meta/bases/{BASE}/tables", body)
    except urllib.error.HTTPError as e:
        sys.exit(f"יצירת הטבלה נכשלה ({e.code}): {e.read().decode()[:400]}")

    print("הטבלה נוצרה.")
    print(f"  מזהה: {created['id']}")
    print()
    print("הצעד הבא - להציב את המזהה ב-wrangler.toml של aimprove-redirector:")
    print(f'  AIRTABLE_EVENTS_TABLE_ID    = "{created["id"]}"')
    print("ואז לפרוס: npx wrangler deploy")


if __name__ == "__main__":
    main()
