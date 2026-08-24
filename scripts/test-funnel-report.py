"""בודק את חישוב המשפך על נתונים בנויים, שהתשובה עליהם ידועה מראש.

    . ~/קוד/sales-automation/.env && python3 scripts/test-funnel-report.py

לא נוגע ב-Airtable - מזריק שורות מזויפות במקום fetch_all. מריצים אותו אחרי
כל שינוי ב-funnel-report.py, ובמיוחד אחרי שינוי ב-LADDER או בשמות האירועים:
שם-אירוע שמשתנה בביקון ולא כאן נראה בדוח בדיוק כמו "אף אחד לא הגיע לשם".
"""
import datetime as dt, importlib.util, sys, io, contextlib

spec = importlib.util.spec_from_file_location("fr", "scripts/funnel-report.py")
fr = importlib.util.module_from_spec(spec); spec.loader.exec_module(fr)

NOW = dt.datetime.now(dt.timezone.utc).isoformat()

def ev(vid, event, **kw):
    f = {"ts": NOW, "vid": vid, "event": event, "page": "index"}
    f.update(kw)
    return {"fields": f, "createdTime": NOW}

# ── תרחיש בנוי ביד. 6 ביקורים, והתשובה הנכונה ידועה: ──
#  v1 נטש בהירו                              ← לא ראה מחיר, לא לחץ
#  v2 הגיע לסיפור ונטש                       ← לא ראה מחיר, לא לחץ
#  v3 ראה מחיר ונטש                          ← ראה מחיר, לא לחץ
#  v4 ראה מחיר ולחץ על נועם                  ← ראה מחיר, לחץ
#  v5 לא נשלחה לו שורת price אך עומקו final  ← נספר כמי שראה מחיר (הגיבוי)
#  v6 ראה מחיר ולחץ פעמיים על נועם + קלנדלי  ← נספר פעם אחת בכל סוג
ROWS = [
    ev("v1","view"), ev("v1","end", depth="hero", seconds=4, device_class="mobile"),
    ev("v2","view"), ev("v2","end", depth="story", seconds=30, device_class="mobile"),
    ev("v3","view"), ev("v3","price"), ev("v3","end", depth="price", seconds=90, device_class="desktop"),
    ev("v4","view", src="p96"), ev("v4","price", src="p96"),
      ev("v4","cta", cta_kind="noam", src="p96"), ev("v4","end", depth="final", seconds=210, device_class="mobile", src="p96"),
    ev("v5","view"), ev("v5","end", depth="final", seconds=150, device_class="desktop"),
    ev("v6","view", src="p96"), ev("v6","price", src="p96"),
      ev("v6","cta", cta_kind="noam", src="p96"), ev("v6","cta", cta_kind="noam", src="p96"),
      ev("v6","cta", cta_kind="calendly", src="p96"), ev("v6","end", depth="final", seconds=300, device_class="mobile", src="p96"),
]

# צד ההטבה: 3 שיחות - אחת עם קוד+נרשמה, אחת עם קוד בלבד, אחת בלי קוד
LEADS = [
    {"createdTime": NOW, "fields": {"קוד הטבה": "AIM-TST1", "סטטוס": "נרשם לקורס"}},
    {"createdTime": NOW, "fields": {"קוד הטבה": "AIM-TST2", "סטטוס": "התקיימה שיחה"}},
    {"createdTime": NOW, "fields": {"סטטוס": "התקיימה שיחה"}},
]

fr.find_events_table = lambda: "tblFAKE"
fr.fetch_all = lambda t: ROWS if t == "tblFAKE" else (LEADS if t == fr.T_LEADS else [])
sys.argv = ["x", "--days", "30"]

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    fr.main()
out = buf.getvalue()
print(out)

print("── אימות מול התשובה הידועה ──")
checks = [
    ("6 ביקורים",                    "נכנסו לדף                6"),
    ("4 ראו מחיר (כולל הגיבוי v5)",  "ראו את המחיר             4"),
    ("2 לחצו על נועם (v6 פעם אחת)",  "לחצו לדבר עם נועם        2"),
    ("2 עזבו לפני המחיר",            "2 מתוך 6 עזבו לפני שראו את המחיר"),
    ("2 ראו מחיר ולא לחצו",          "ומתוך 4 שכן ראו אותו, 2 לא לחצו על נועם"),
    ("קלנדלי נספר פעם אחת",          "ביקשו שיחה ישירה עם שלהבת:          1"),
    ("פילוח לפי קוד-מקור",           "p96             2 ביקורים · 2 ראו מחיר · 2 לחצו על נועם"),
    ("3 שיחות בצד נועם",             "שיחות חדשות שנפתחו               3"),
    ("2 קיבלו קוד הטבה (67%)",       "קיבלו קוד הטבה (1,400 ₪)         2   (67% מהשיחות)"),
    ("1 נרשמה לקורס",                "נרשמו לקורס                      1"),
]
ok = True
for label, needle in checks:
    hit = needle in out
    ok &= hit
    print(("  ✅ " if hit else "  ❌ ") + label)
print("\nתוצאה:", "כל הבדיקות עברו" if ok else "יש כשל")
sys.exit(0 if ok else 1)
