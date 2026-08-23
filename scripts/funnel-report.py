#!/usr/bin/env python3
"""דוח המשפך של דף הנחיתה - כמה נכנסו, כמה ראו את המחיר, כמה הלכו לנועם.

    . ~/קוד/sales-automation/.env && python3 scripts/funnel-report.py
    python3 scripts/funnel-report.py --days 7

הדוח מדבר בעברית פשוטה ובמספרים בלבד. שלושה מקורות, שכל אחד עונה על חלק אחר:
  1. טבלת אירועי-המשפך  - מה קרה בתוך הדף (המדידה שנוספה 23-08-2026)
  2. טבלת הקליקים        - כמה הגיעו לדף דרך לינק מתויג
  3. טבלת לידי נועם      - כמה שיחות נפתחו בפועל, מכל המקורות

⚠️ שלוש הערות-דיוק שחייבות להישאר בדוח, אחרת המספרים מטעים:
  - "לחצו על נועם" נמדד בדף. הוא אינו זהה ל"פתחו שיחה" - הלחיצה פותחת את
    וואטסאפ, ומשם אפשר לא לשלוח. שני המספרים מוצגים בנפרד בכוונה.
  - לידי נועם מגיעים גם מאינסטגרם ומקישורים ישירים, לא רק מהדף. אסור לחלק
    אותם במבקרי הדף ולקרוא לזה "אחוז המרה".
  - ביקור נספר לפי vid, שחי בלשונית אחת. אותו אדם שחוזר מחר נספר שוב.
"""
import argparse
import collections
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "app5fKvxuzbFb0stR"
T_CLICKS = "tblhpYSrbQyXwhen7"
T_LEADS = "tblWrBSnk2GxQYOXI"
EVENTS_TABLE_NAME = "אירועי משפך - דף נחיתה"

# סדר הסקשנים בדף - חייב להתאים ל-SECTIONS בביקון שב-index.html
LADDER = ["hero", "intro", "story", "proofs", "roadmap", "price", "video", "final"]
HEB = {
    "hero": "הכותרת הראשית (לא גללו כמעט בכלל)",
    "intro": "פתיח - למי זה מיועד",
    "story": "הסיפור",
    "proofs": "המלצות והוכחות",
    "roadmap": "מפת המסע",
    "price": "אזור המחיר",
    "video": "הסרטון של נועם",
    "final": "הקריאה לפעולה בסוף",
}


def _get(path, params=None):
    url = f"https://api.airtable.com/v0/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {os.environ['AIRTABLE_API_KEY']}"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def fetch_all(table):
    out, offset = [], None
    while True:
        p = {"pageSize": 100}
        if offset:
            p["offset"] = offset
        d = _get(f"{BASE}/{urllib.parse.quote(table)}", p)
        out += d.get("records", [])
        offset = d.get("offset")
        if not offset:
            return out


def find_events_table():
    for t in _get(f"meta/bases/{BASE}/tables")["tables"]:
        if t["name"] == EVENTS_TABLE_NAME:
            return t["id"]
    return None


def pct(n, total):
    return f"{100.0 * n / total:.0f}%" if total else "-"


def bar(n, total, width=28):
    filled = round(width * n / total) if total else 0
    return "█" * filled + "·" * (width - filled)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30, help="כמה ימים אחורה (ברירת מחדל 30)")
    args = ap.parse_args()

    if not os.environ.get("AIRTABLE_API_KEY"):
        sys.exit("חסר AIRTABLE_API_KEY. הריצי:  . ~/קוד/sales-automation/.env")

    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=args.days)
    since_s = since.isoformat()
    d1 = since.strftime("%d/%m/%Y")
    d2 = dt.datetime.now(dt.timezone.utc).strftime("%d/%m/%Y")

    print()
    print("=" * 62)
    print(f"  משפך דף הנחיתה של טירונות - {d1} עד {d2}")
    print("=" * 62)

    # ── 1. המשפך בתוך הדף ─────────────────────────────────────────────────────
    tid = find_events_table()
    if not tid:
        print()
        print("  טבלת אירועי-המשפך עדיין לא קיימת, ולכן אין נתונים על מה")
        print("  שקורה בתוך הדף. ליצור אותה:")
        print("      python3 scripts/create-events-table.py")
        visits = {}
    else:
        rows = [r for r in fetch_all(tid) if str(r["fields"].get("ts", "")) >= since_s]
        visits = collections.defaultdict(
            lambda: {"price": False, "cta": set(), "depth": -1, "src": "", "dev": "", "secs": None}
        )
        for r in rows:
            f = r["fields"]
            v = visits[str(f.get("vid", ""))]
            ev = str(f.get("event", ""))
            if ev == "price":
                v["price"] = True
            if ev == "cta" and f.get("cta_kind"):
                v["cta"].add(str(f["cta_kind"]))
            d = str(f.get("depth", ""))
            if d in LADDER:
                v["depth"] = max(v["depth"], LADDER.index(d))
            if f.get("src"):
                v["src"] = str(f["src"])
            if f.get("device_class"):
                v["dev"] = str(f["device_class"])
            if f.get("seconds") is not None:
                v["secs"] = f["seconds"]
        # מי שהגיע לסקשן המחיר נחשב כמי שראה אותו, גם אם שורת ה-price אבדה ביציאה
        for v in visits.values():
            if v["depth"] >= LADDER.index("price"):
                v["price"] = True

    n = len(visits)
    if n:
        saw_price = sum(1 for v in visits.values() if v["price"])
        clicked_noam = sum(1 for v in visits.values() if "noam" in v["cta"])
        clicked_cal = sum(1 for v in visits.values() if "calendly" in v["cta"])
        clicked_vid = sum(1 for v in visits.values() if "video" in v["cta"])

        print()
        print(f"  נכנסו לדף            {n:>5}   {bar(n, n)}  100%")
        print(f"  ראו את המחיר         {saw_price:>5}   {bar(saw_price, n)}  {pct(saw_price, n)}")
        print(f"  לחצו לדבר עם נועם    {clicked_noam:>5}   {bar(clicked_noam, n)}  {pct(clicked_noam, n)}")
        print()
        print(f"  הפער שנשאל עליו: {n - saw_price} מתוך {n} עזבו לפני שראו את המחיר.")
        print(f"  ומתוך {saw_price} שכן ראו אותו, {saw_price - clicked_noam} לא לחצו על נועם"
              f" ({pct(saw_price - clicked_noam, saw_price)} ממי שראה מחיר).")
        if clicked_cal or clicked_vid:
            print()
            print(f"  לחצו על 'צפו בסרטון' מכרטיס המחיר: {clicked_vid}")
            print(f"  ביקשו שיחה ישירה עם שלהבת:          {clicked_cal}")

        print()
        print("  איפה בדיוק עזבו:")
        depths = collections.Counter(
            LADDER[v["depth"]] if v["depth"] >= 0 else "hero" for v in visits.values()
        )
        for name in LADDER:
            c = depths.get(name, 0)
            if c:
                mark = "  ← המחיר" if name == "price" else ""
                print(f"    {HEB[name]:<34} {c:>4}  {pct(c, n):>4}{mark}")

        devs = collections.Counter(v["dev"] or "לא ידוע" for v in visits.values())
        print()
        print("  מכשיר: " + " · ".join(f"{k} {c}" for k, c in devs.most_common()))

        secs = sorted(v["secs"] for v in visits.values() if v["secs"] is not None)
        if secs:
            print(f"  זמן חציוני על הדף: {secs[len(secs) // 2]} שניות")

        by_src = collections.Counter(v["src"] for v in visits.values() if v["src"])
        if by_src:
            print()
            print("  מאיפה הגיעו (לפי קוד-מקור):")
            for s, c in by_src.most_common(10):
                sp = sum(1 for v in visits.values() if v["src"] == s and v["price"])
                cn = sum(1 for v in visits.values() if v["src"] == s and "noam" in v["cta"])
                print(f"    {s:<12} {c:>4} ביקורים · {sp} ראו מחיר · {cn} לחצו על נועם")

    # ── 2. הקשר: כמה הגיעו לדף, וכמה שיחות נפתחו ─────────────────────────────
    clicks = [
        r["fields"] for r in fetch_all(T_CLICKS)
        if str(r["fields"].get("slug", "")).startswith("p-")
        and str(r["fields"].get("ts", "")) >= since_s
    ]
    leads = [r for r in fetch_all(T_LEADS) if str(r.get("createdTime", "")) >= since_s]

    # ניקוי בוטים מהקליקים. נמדד 23-08-2026: מתוך 631 קליקים גולמיים רק ~107
    # היו בני-אדם מישראל - 387 מארה"ב ו-36 מסין, ו-65 כתובות סרקו 3+ קודים
    # שונים באותו יום (זחלני ספוטיפיי/יוטיוב/מנועי-חיפוש שפותחים כל לינק).
    # הצגת המספר הגולמי לבדו מטעה, ולכן שניהם מוצגים.
    sweep = {}
    for f in clicks:
        k = (f.get("ip_hash", ""), str(f.get("ts", ""))[:10])
        sweep.setdefault(k, set()).add(f.get("slug"))
    sweepers = {k for k, v in sweep.items() if len(v) >= 3 and k[0]}
    human = set()
    for f in clicks:
        k = (f.get("ip_hash", ""), str(f.get("ts", ""))[:10])
        if f.get("prefetch") or k in sweepers:
            continue
        if str(f.get("country", "")) != "IL" or str(f.get("device_class", "")) == "unknown":
            continue
        human.add((f.get("ip_hash", ""), f.get("slug"), str(f.get("ts", ""))[:10]))

    print()
    print("-" * 62)
    print("  להשוואה, מאותה תקופה:")
    print(f"    קליקים על לינק מתויג (גולמי, כולל בוטים)  {len(clicks):>5}")
    print(f"    מתוכם בני-אדם מישראל, ככל הנראה           {len(human):>5}")
    print(f"    שיחות חדשות שנפתחו עם נועם   {len(leads):>5}")
    print()
    print("    שימי לב: שיחות נועם מגיעות גם מאינסטגרם ומקישורים ישירים,")
    print("    לא רק מהדף - אז אסור לחלק אותן במבקרי הדף.")
    if not n:
        print()
        print("    ואת המספר שבאמצע - מי מבין הנכנסים לדף ראה את המחיר -")
        print("    אף אחד משני המקורות האלה לא יודע. בשביל זה נבנתה המדידה.")
    print("=" * 62)
    print()


if __name__ == "__main__":
    main()
