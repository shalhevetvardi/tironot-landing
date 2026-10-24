"""בודק את דוח החצי מול חצי (funnel-report.py --ab) על נתונים בנויים, שהתשובה עליהם ידועה מראש.

    AIRTABLE_API_KEY=x python3 scripts/test-funnel-report-ab.py

לא נוגע ב-Airtable. התרחיש:
  a (index):  a1 נטש בהירו · a2 ראה מחיר · a3 ראה מחיר ולחץ לנועם · a0 ביקור לפני תחילת ההשוואה (לא נספר)
  b (hatzaa): b1 ראה מחיר ולחץ · b2 הגיע עד final בלי שורת price (נספר כמי שראה) · b3 קוד-בדיקה (לא נספר)
  לידים: אחד עם #ab-a, שניים עם #ab-b (אחד מהם עם קוד ונרשם), אחד בלי סימון (לא נספר),
         ואחד עם #ab-b בשורה שנייה ולא בראשונה (לא נספר: הסימון נבדק רק בהודעה הראשונה)
"""
import datetime as dt, importlib.util, sys, io, contextlib

spec = importlib.util.spec_from_file_location("fr", "scripts/funnel-report.py")
fr = importlib.util.module_from_spec(spec); spec.loader.exec_module(fr)

START = "2026-10-25T08:00:00+00:00"
BEFORE = "2026-10-20T08:00:00+00:00"
AFTER = "2026-10-26T08:00:00+00:00"

def ev(vid, event, page, ts=AFTER, **kw):
    f = {"ts": ts, "vid": vid, "event": event, "page": page}
    f.update(kw)
    return {"fields": f, "createdTime": ts}

ROWS = [
    ev("a0", "view", "index", ts=BEFORE), ev("a0", "price", "index", ts=BEFORE),
    ev("a1", "view", "index"), ev("a1", "end", "index", depth="hero"),
    ev("a2", "view", "index"), ev("a2", "price", "index"),
    ev("a3", "view", "index"), ev("a3", "price", "index"), ev("a3", "cta", "index", cta_kind="noam"),
    ev("b1", "view", "hatzaa", ts=START), ev("b1", "price", "hatzaa"), ev("b1", "cta", "hatzaa", cta_kind="noam"),
    ev("b2", "view", "hatzaa"), ev("b2", "end", "hatzaa", depth="final"),
    ev("b3", "view", "hatzaa", src="test-ab"), ev("b3", "cta", "hatzaa", cta_kind="noam", src="test-ab"),
    ev("g1", "view", "gallery"),
]
L = "[2026-10-26T09:00:00.000Z] ליד: "
LEADS = [
    {"createdTime": AFTER, "fields": {"noam_chat_log": L + "שלחו הודעה זו בדיוק כמו שהיא כדי להתחיל לדבר עם נועם #p99 #ab-a"}},
    {"createdTime": AFTER, "fields": {"noam_chat_log": L + "שלחו את ההודעה הזו כדי להתחיל לדבר עם נועם #ab-b"}},
    {"createdTime": AFTER, "fields": {"noam_chat_log": L + "שלחו את ההודעה הזו כדי להתחיל לדבר עם נועם #ab-b",
                                      "קוד הטבה": "AIM-T1", "סטטוס": "נרשם לקורס"}},
    {"createdTime": AFTER, "fields": {"noam_chat_log": L + "היי"}},
    {"createdTime": AFTER, "fields": {"noam_chat_log": L + "היי\n\n[2026-10-26T09:01:00.000Z] ליד: #ab-b"}},
]

fr.find_events_table = lambda: "tblFAKE"
fr.fetch_all = lambda t: ROWS if t == "tblFAKE" else (LEADS if t == fr.T_LEADS else [])
sys.argv = ["x", "--ab"]
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    fr.main()
out = buf.getvalue()
print(out)

def row(label, a, b):
    return f"  {label:<26}{a:>14}{b:>18}"

checks = [
    ("ההשוואה מתחילה בביקור הראשון ב-b", "חצי מול חצי - מ-2026-10-25"),
    ("3 ב-a (בלי a0 שלפני), 2 ב-b (בלי קוד-הבדיקה)", row("נכנסו לדף", "3", "2")),
    ("ראו מחיר: 2 מול 2 (b2 לפי העומק)", row("ראו את המחיר", "2 (67%)", "2 (100%)")),
    ("לחצו לנועם: 1 מול 1", row("לחצו לדבר עם נועם", "1 (33%)", "1 (50%)")),
    ("שיחות לפי הסימון בהודעה הראשונה", row("שיחות שנפתחו אצל נועם", "1", "2")),
    ("קוד הטבה", row("קיבלו קוד הטבה", "0", "1")),
    ("הרשמות", row("נרשמו לקורס", "0", "1")),
    ("מדגם קטן = לא מובהק", "עדיין יכול להיות מקרי"),
]
ok = True
for label, needle in checks:
    hit = needle in out
    ok &= hit
    print(("  ✅ " if hit else "  ❌ ") + label)
print("\nתוצאה:", "כל הבדיקות עברו" if ok else "יש כשל")
sys.exit(0 if ok else 1)
