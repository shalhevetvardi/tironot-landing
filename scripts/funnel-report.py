#!/usr/bin/env python3
"""דוח המשפך של דף הנחיתה - כמה נכנסו, כמה ראו את המחיר, כמה הלכו לנועם.

    . ~/קוד/sales-automation/.env && python3 scripts/funnel-report.py
    python3 scripts/funnel-report.py --days 7
    python3 scripts/funnel-report.py --ab        # חצי מול חצי: הדף הקיים (a) מול הגרסה לקהל קר (b)

הדוח מדבר בעברית פשוטה ובמספרים בלבד, ומציג את שני צדי המנגנון זה מול זה
(דרישת שלהבת, 23-08): כמה נוטשים בדף, מול כמה ממשיכים לנועם ומקבלים את
ההטבה בפועל. שלושה מקורות, שכל אחד עונה על חלק אחר:
  1. טבלת אירועי-המשפך  - מה קרה בתוך הדף (המדידה שנוספה 23-08-2026)
  2. טבלת הקליקים        - כמה הגיעו לדף דרך לינק מתויג
  3. טבלת לידי נועם      - שיחות שנפתחו, קודי-הטבה שניתנו, והרשמות

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
# מ-24-10-2026 טבלת האירועים בבסיס משלה (אותו שם): "כל הלידים" עבר את מגבלת 50,000 השורות,
# והטבלה הזו גדלה בכ-19,000 שורות בחודש. הקליקים והלידים נשארו ב-BASE.
EVENTS_BASE = "appsmXIiJbUfepFhC"
_EVENTS_TABLE_IDS = set()
# מ-24-10-2026 האירועים נשמרים ב-D1 (מסד הנתונים של Cloudflare), ונקראים דרך GET /events בשירות
# הקליטה (aimprove-redirector). עם מפתח קריאה הדוח קורא משם; בלעדיו, מ-Airtable כמו קודם.
EVENTS_API = os.environ.get("EVENTS_API_URL", "https://r.aimprove.co.il/events")
EVENTS_FROM_D1 = "d1"


def _events_key():
    k = os.environ.get("EVENTS_READ_KEY", "")
    if k:
        return k
    f = os.path.expanduser("~/.claude/secrets/funnel-events.env")
    if os.path.exists(f):
        for line in open(f, encoding="utf-8"):
            if line.startswith("EVENTS_READ_KEY="):
                return line.split("=", 1)[1].strip()
    return ""


def fetch_d1_events(page=None):
    """כל האירועים של דף אחד מ-D1, בצורה של שורות Airtable ({"fields": ...}), כדי ששאר הדוח לא ישתנה."""
    out, after = [], ""
    for _ in range(400):
        q = {"page": page} if page else {}
        if after:
            q["after"] = after
        req = urllib.request.Request(
            f"{EVENTS_API}?{urllib.parse.urlencode(q)}",
            headers={"x-events-key": _events_key(), "User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            body = json.loads(r.read())
        for row in body.get("rows", []):
            f = {k: v for k, v in row.items() if k not in ("id",) and v not in ("", None)}
            out.append({"id": row.get("id"), "fields": f})
        after = body.get("next") or ""
        if not after:
            return out
    raise RuntimeError("events API stopped at 400 pages")

# סדר הסקשנים בדף - חייב להתאים ל-SECTIONS בביקון שב-index.html. "fit" ו-"what" קיימים רק בגרסה לקהל קר
# (hatzaa.html, מ-24-10-2026), מיד אחרי המסך הראשון. הדף הקיים לא שולח אותם, ולכן אצלו הסולם לא משתנה
LADDER = ["hero", "fit", "what", "intro", "story", "proofs", "roadmap", "price", "video", "final"]
HEB = {
    "hero": "הכותרת הראשית (לא גללו כמעט בכלל)",
    "fit": "למי זה מתאים (רק בגרסה לקהל קר)",
    "what": "מה בדיוק קונים כאן (רק בגרסה לקהל קר)",
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
    if table == EVENTS_FROM_D1:
        # כל הדפים, כמו מ-Airtable: הדוח מסנן לבד, ומציג כמה ביקורים בדפים אחרים לא נספרו.
        return fetch_d1_events(None)
    out, offset = [], None
    while True:
        p = {"pageSize": 100}
        if table == T_CLICKS:
            # שדה "bot" נוסף לטבלה 24-08-2026 - הטבלה מסננת את עצמה בצד השרת
            # (NOT({bot})). חתימת הפונקציה נשארת אחידה בכוונה (לא פרמטר נוסף)
            # כי test-funnel-report.py מזריק fetch_all=lambda t: ... בעל
            # ארגומנט יחיד - שינוי חתימה כאן היה שובר את הבדיקה בלי לגעת בה.
            p["filterByFormula"] = "NOT({bot})"
        if offset:
            p["offset"] = offset
        base = EVENTS_BASE if table in _EVENTS_TABLE_IDS else BASE
        d = _get(f"{base}/{urllib.parse.quote(table)}", p)
        out += d.get("records", [])
        offset = d.get("offset")
        if not offset:
            return out


def find_events_table():
    if _events_key():
        return EVENTS_FROM_D1
    for t in _get(f"meta/bases/{EVENTS_BASE}/tables")["tables"]:
        if t["name"] == EVENTS_TABLE_NAME:
            _EVENTS_TABLE_IDS.add(t["id"])
            return t["id"]
    return None


# קודי-בדיקה שנספרו בטעות כמבקרים ב-24-08-2026 (ר' docs/מדידת-משפך-דף-הנחיתה.md,
# סעיף 10) - חד-פעמיים שכבר נצפו, ומוסכמה קדימה לכל בדיקה עתידית (ידנית/CI).
TEST_SRC_EXACT = {"vo-checkout", "deploy-e2e2"}
TEST_SRC_PREFIX = "test-"


def is_test_src(src):
    s = str(src or "")
    return s in TEST_SRC_EXACT or s.startswith(TEST_SRC_PREFIX)


def pct(n, total):
    return f"{100.0 * n / total:.0f}%" if total else "-"


def bar(n, total, width=28):
    filled = round(width * n / total) if total else 0
    return "█" * filled + "·" * (width - filled)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30, help="כמה ימים אחורה (ברירת מחדל 30)")
    ap.add_argument("--ab", action="store_true", help="חצי מול חצי: index (a) מול hatzaa (b)")
    ap.add_argument("--since", default="", help="עם --ab: מאיזה תאריך (YYYY-MM-DD). ברירת מחדל: הביקור הראשון ב-b")
    args = ap.parse_args()

    if not os.environ.get("AIRTABLE_API_KEY"):
        sys.exit("חסר AIRTABLE_API_KEY. הריצי:  . ~/קוד/sales-automation/.env")
    if args.ab:
        return ab_report(args)

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
    n_excluded = 0
    other_page_vids = set()
    if not tid:
        print()
        print("  טבלת אירועי-המשפך עדיין לא קיימת, ולכן אין נתונים על מה")
        print("  שקורה בתוך הדף. ליצור אותה:")
        print("      python3 scripts/create-events-table.py")
        visits = {}
    else:
        raw = fetch_all(tid)
        test_vids = {
            str(r["fields"].get("vid", ""))
            for r in raw if is_test_src(r["fields"].get("src"))
        }
        n_excluded = len(test_vids)
        # הטבלה משותפת לכמה דפים (הגלריה, אתר אימפרוב, דפי הסקילים - ר' EV_PAGES
        # ב-Worker). בלי הסינון הם נספרו כמבקרי דף הטירונות וכמי ש"עזבו בכותרת".
        in_window = [r for r in raw if str(r["fields"].get("ts", "")) >= since_s]
        other_page_vids = {
            str(r["fields"].get("vid", ""))
            for r in in_window if str(r["fields"].get("page") or "index") != "index"
        }
        rows = [
            r for r in in_window
            if str(r["fields"].get("vid", "")) not in test_vids
            and str(r["fields"].get("page") or "index") == "index"
        ]
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
            # מ-17-10-2026 הדף שולח end שוב בכל יציאה שבה המבקר הגיע רחוק יותר,
            # ולכן לביקור יכולות להיות כמה שורות end, והסדר שלהן מ-Airtable אינו
            # מובטח. העומק כבר נלקח כמקסימום (למעלה); גם הזמן - האחרונה היא הארוכה.
            if f.get("seconds") is not None:
                v["secs"] = f["seconds"] if v["secs"] is None else max(v["secs"], f["seconds"])
        # מי שהגיע לסקשן המחיר נחשב כמי שראה אותו, גם אם שורת ה-price אבדה ביציאה
        for v in visits.values():
            if v["depth"] >= LADDER.index("price"):
                v["price"] = True

    n = len(visits)
    if tid and other_page_vids:
        print()
        print(f"  (לא נספרו {len(other_page_vids)} ביקורים מדפים אחרים שחולקים את הטבלה)")
    if n_excluded:
        print()
        print(f"  (סוננו {n_excluded} ביקורי-בדיקה מוכרים - src מתויג כבדיקה, לא בחישוב)")
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

    # ניקוי בוטים מהקליקים - שכבה שנייה. fetch_all(T_CLICKS) כבר מבקש
    # NOT({bot}) בצד השרת (24-08-2026, ר' fetch_all למעלה), אבל הלוגיקה
    # המקומית כאן נשארת: היא תופסת דפוסים (סריקת-כמה-קודים/geo/מכשיר) שהם
    # ספציפיים לכלי-האבחון הזה ולא בהכרח זהים לקריטריון ה-"bot" בטבלה, בדיוק
    # כמו בצד הפייתון של sales-automation ובצד ה-JS של tironot-control-room.
    # נמדד 23-08-2026 (לפני שהיה שדה bot): מתוך 631 קליקים גולמיים רק ~107
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

    # הצד השני של המנגנון: ההטבה של 1,400 ₪ ניתנת רק דרך נועם, אז "קיבל
    # קוד הטבה" הוא המדד לכך שהשיחה הגיעה עד ההצעה עצמה.
    got_code = [
        r for r in leads if str(r["fields"].get("קוד הטבה", "")).strip()
    ]
    enrolled = [
        r for r in got_code
        if str(r["fields"].get("סטטוס", "")) == "נרשם לקורס"
    ]

    print()
    print("-" * 62)
    print("  להשוואה, מאותה תקופה:")
    print(f"    קליקים על לינק מתויג (גולמי, כולל בוטים)  {len(clicks):>5}")
    print(f"    מתוכם בני-אדם מישראל, ככל הנראה           {len(human):>5}")
    print()
    print("  והצד השני של המנגנון - מה קורה אצל נועם:")
    print(f"    שיחות חדשות שנפתחו           {len(leads):>5}")
    print(f"    קיבלו קוד הטבה (1,400 ₪)     {len(got_code):>5}   ({pct(len(got_code), len(leads))} מהשיחות)")
    print(f"    נרשמו לקורס                  {len(enrolled):>5}")
    print()
    print("    שימי לב: שיחות נועם מגיעות גם מאינסטגרם ומקישורים ישירים,")
    print("    לא רק מהדף - אז אסור לחלק אותן במבקרי הדף.")
    if not n:
        print()
        print("    ואת המספר שבאמצע - מי מבין הנכנסים לדף ראה את המחיר -")
        print("    אף אחד משני המקורות האלה לא יודע. בשביל זה נבנתה המדידה.")
    print("=" * 62)
    print()


# ── חצי מול חצי (24-10-2026) ─────────────────────────────────────────────────
# index.html מגריל כל מבקר חדש ל-a (הדף הקיים) או ל-b (hatzaa.html), ומסמן את ההודעה לנועם
# ב-#ab-a או ב-#ab-b. הצד של הדף נספר מאירועי המשפך לפי page, והצד של נועם לפי הסימון
# בשורה הראשונה של noam_chat_log. ההחלטות: Storyteling, פרויקטים/חיפוש-SEO-GEO/06-אסטרטגיית-הדף-הקר.md.
AB_PAGES = {"index": "a", "hatzaa": "b"}
AB_NAMES = {"a": "הדף הקיים", "b": "הגרסה לקהל קר"}


def _ab_z(x1, n1, x2, n2):
    """מבחן z לשני שיעורים. |z| מתחת ל-1.96 = ההבדל עדיין יכול להיות מקרי."""
    if not n1 or not n2:
        return 0.0
    p = (x1 + x2) / (n1 + n2)
    se = (p * (1 - p) * (1 / n1 + 1 / n2)) ** 0.5
    return (x2 / n2 - x1 / n1) / se if se else 0.0


def ab_report(args):
    tid = find_events_table()
    raw = fetch_all(tid) if tid else []
    test_vids = {str(r["fields"].get("vid", "")) for r in raw if is_test_src(r["fields"].get("src"))}
    rows = [r["fields"] for r in raw
            if str(r["fields"].get("page") or "index") in AB_PAGES
            and str(r["fields"].get("vid", "")) not in test_vids]
    starts = sorted(str(f.get("ts", "")) for f in rows
                    if str(f.get("page")) == "hatzaa" and f.get("event") == "view")
    start = args.since or (starts[0] if starts else "")
    print()
    print("=" * 62)
    if not start:
        print("  חצי מול חצי: עוד אין אף ביקור בגרסה לקהל קר, ולכן אין מה להשוות.")
        print("=" * 62)
        return
    print(f"  חצי מול חצי - מ-{start[:10]}")
    print("=" * 62)

    groups = {"a": {}, "b": {}}
    for f in rows:
        if str(f.get("ts", "")) < start:
            continue
        g = AB_PAGES[str(f.get("page") or "index")]
        v = groups[g].setdefault(str(f.get("vid", "")), {"price": False, "noam": False})
        if f.get("event") == "price" or (f.get("event") == "end" and str(f.get("depth", "")) in LADDER
                                         and LADDER.index(str(f["depth"])) >= LADDER.index("price")):
            v["price"] = True
        if f.get("event") == "cta" and f.get("cta_kind") == "noam":
            v["noam"] = True

    leads = {"a": [], "b": []}
    for r in fetch_all(T_LEADS):
        if str(r.get("createdTime", "")) < start:
            continue
        first = str(r["fields"].get("noam_chat_log") or "").strip().splitlines()[:1]
        for g in ("a", "b"):
            if first and f"#ab-{g}" in first[0]:
                leads[g].append(r["fields"])

    stats = {}
    print()
    print(f"  {'':<26}{AB_NAMES['a']:>14}{AB_NAMES['b']:>18}")
    for g in ("a", "b"):
        vs = groups[g].values()
        stats[g] = {
            "n": len(groups[g]),
            "price": sum(1 for v in vs if v["price"]),
            "noam": sum(1 for v in vs if v["noam"]),
            "chats": len(leads[g]),
            "code": sum(1 for f in leads[g] if str(f.get("קוד הטבה", "")).strip()),
            "enrolled": sum(1 for f in leads[g] if str(f.get("סטטוס", "")) == "נרשם לקורס"),
        }

    def line(label, key, of=None):
        cells = []
        for g in ("a", "b"):
            s = stats[g]
            cells.append(f"{s[key]} ({pct(s[key], s[of])})" if of else str(s[key]))
        print(f"  {label:<26}{cells[0]:>14}{cells[1]:>18}")

    line("נכנסו לדף", "n")
    line("ראו את המחיר", "price", "n")
    line("לחצו לדבר עם נועם", "noam", "n")
    line("שיחות שנפתחו אצל נועם", "chats")
    line("קיבלו קוד הטבה", "code")
    line("נרשמו לקורס", "enrolled")

    z = _ab_z(stats["a"]["noam"], stats["a"]["n"], stats["b"]["noam"], stats["b"]["n"])
    print()
    if abs(z) < 1.96:
        print("  ההבדל בלחיצות לנועם עדיין יכול להיות מקרי. ממשיכים לאסוף.")
    else:
        better = "b" if z > 0 else "a"
        print(f"  ההבדל בלחיצות לנועם כבר לא מקרי: {AB_NAMES[better]} מביא יותר.")
    print("  המדד שמכריע הוא הרשמות, ולא לחיצות (מסמך 06, סעיף 8). בהרשמות צריך")
    print("  הרבה יותר זמן עד שאפשר לומר משהו, כי יש מעט מהן.")
    print("=" * 62)
    print()


if __name__ == "__main__":
    main()
