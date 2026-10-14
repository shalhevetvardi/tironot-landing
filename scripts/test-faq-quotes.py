"""Usage: python3 scripts/test-faq-quotes.py   (בלי רשת, בלי תלויות)

רצועות ציטוטי הבוגרים (scripts/build_faq_quotes.py):
  * מבנה הכרטיס זהה בדיוק לחוזה ב-sales-automation (tests/test_testimonial_sales_model.py,
    test_card_markup_is_the_agreed_contract_exactly) - אותו קלט, אותו פלט.
  * הסוגריים המרובעים: "[...]" נשאר טקסט, "]" בלי "[" פתוח הוא פתיחה, "[" שלא נסגר נשאר טקסט.
  * הבנייה לא משנה דבר בהפעלה חוזרת, והדפים בריפו מעודכנים (--check).
  * העיצוב והקוד יושבים פעם אחת בכל דף, וזהים בשני הדפים.
"""
import html
import json
import os
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_faq_quotes as b  # noqa: E402

ROOT = Path(b.ROOT)
fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


# 1. החוזה עם דף המכירה
it = {"name": "דנה כהן", "photo": "bogrim/images/dana.jpg", "role": "מנהלת <מוצר>",
      "text": "פתיחה. [...] כאן נכנס [הקו]\n\n*הערת הקשר\n[שורה] שנייה"}
expected = (
    '<button type="button" class="tm-qm__card"><span class="tm-qm__h">הקו</span>'
    '<span class="tm-qm__q"><span class="tm-qm__l">פתיחה. [...] כאן נכנס <span class="tm-hl">הקו</span></span>'
    '<span class="tm-qm__note">הערת הקשר</span>'
    '<span class="tm-qm__l"><span class="tm-hl">שורה</span> שנייה</span></span>'
    '<span class="tm-qm__who"><img class="tm-qm__av" src="bogrim/images/dana.jpg" alt="" loading="lazy">'
    '<span class="tm-qm__id"><span class="tm-qm__name">דנה כהן</span><span class="tm-qm__role">מנהלת &lt;מוצר&gt;</span></span></span></button>')
check(b.card(it, photo_prefix="") == expected, "מבנה הכרטיס סטה מהחוזה עם דף המכירה")
check('src="../bogrim/images/dana.jpg"' in b.card(it), "בדף השאלות התמונה צריכה ../")
no_photo = b.card({"name": "  ענבר כרמלי", "text": "בלי הדגשה. ועוד"})
n = sum(map(ord, "  ענבר כרמלי")) % 6
check(f'<span class="tm-qm__av tm-qm__av--{n}" aria-hidden="true">ע</span>' in no_photo, "עיגול האות")
check('<span class="tm-qm__h">בלי הדגשה</span>' in no_photo and "tm-qm__role" not in no_photo, "כותרת בלי הדגשה / בלי תפקיד")

# 2. סוגריים
check(b.parse_brackets("א [...] ב") == ("א [...] ב", []), "[...] הוא טקסט")
txt, rng = b.parse_brackets("זהו, ]קיבלתי את הרישיון].")
check(txt == "זהו, קיבלתי את הרישיון." and [txt[a:c] for a, c in rng] == ["קיבלתי את הרישיון"], "] בלי [ פתוח")
check(b.parse_brackets("[פתוח בלי סגירה") == ("[פתוח בלי סגירה", []), "[ שלא נסגר")
txt, rng = b.parse_brackets("[א] ו[ב]")
check([txt[a:c] for a, c in rng] == ["א", "ב"], "כמה הדגשות")

# 3. רצועה / כרטיס אחד
one = b.marquee([it])
check(one.startswith('<div class="tm-qm tm-qm--one"><button') and "tm-qm__row" not in one, "ציטוט אחד = כרטיס בלי רצועה")
three = b.marquee([it] * 3)
check(three.count('class="tm-qm__row') == 1, "3 ציטוטים = רצועה אחת")
five = b.marquee([dict(it, name=str(i)) for i in range(5)])
check(five.count('class="tm-qm__row"') == 1 and five.count("tm-qm__row--rev") == 1, "5 ציטוטים = שתי רצועות")

# 4. הדפים בריפו מעודכנים, והבנייה יציבה
placements = json.loads(Path(b.DEFAULT_PLACEMENTS).read_text(encoding="utf-8")) if Path(b.DEFAULT_PLACEMENTS).exists() else None
check(placements is not None, "חסר scripts/faq-quotes-data/placements.json - הדף לא ניתן לבנייה מהריפו")
if placements is not None:
    items = json.loads(Path(b.DEFAULT_ITEMS).read_text(encoding="utf-8"))
    pages, done = b.build(ROOT, placements, items)
    for p, text in pages.items():
        check(p.read_text(encoding="utf-8") == text,
              f"{p.relative_to(ROOT)} לא תואם לנתונים שב-scripts/faq-quotes-data - ר' הסעיף על רצועות הציטוטים ב-CLAUDE.md")
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "faq").mkdir()
        for rel in ("index.html", "faq/index.html"):
            (Path(d) / rel).write_text(pages[ROOT / rel], encoding="utf-8")
        again, _ = b.build(Path(d), placements, items)
        check(all(again[Path(d) / rel] == pages[ROOT / rel] for rel in ("index.html", "faq/index.html")), "הפעלה חוזרת שינתה את הדף")
    faq = (ROOT / "faq/index.html").read_text(encoding="utf-8")
    for qid, cnt in done.items():
        check(faq.count(f"<!-- tm-qm:{qid} -->") == 1, f"{qid}: בלוק אחד")
    check("tm-answer__quote" in faq, "הציטוט של סיגל נשאר")
    # מה שנכנס לריפו הוא רק מה שמוצג בדף: בלי לשוניות דף המכירה, בלי שדות עבודה, ובלי פריטים שהוצאו
    rows = [r for v in placements.values() for r in v]
    check(all(k[0] == "q" and 7 <= int(k[1:]) <= 41 for k in placements), "בקובץ הנתונים רק שאלות q07-q41")
    check(all(set(r) == {"qid", "name", "role", "photo", "text", "headline"} for r in rows),
          "בפריט רק qid, name, role, photo, text, headline")
    # 13-10-2026: הכותרת שמעל כל ציטוט נכתבת ביד (docs/פרומפט-כותרות-ציטוטים.md) ולא נגזרת מההדגשה הראשונה. רוב
    # המבקרים קוראים רק אותה, ולכן היא חייבת להיות מובנת בלי הציטוט: כותרת שנגזרה מהדגשה יצאה שבר משפט
    # ("היום", "לא יכלתי"), או ביקורת על קורסים אחרים שנקראת כאילו היא עלינו ("יוצא מוגבל").
    heads = [str(r.get("headline") or "").strip() for r in rows]
    check(all(heads), "לכל ציטוט יש כותרת")
    check(all(2 <= len(h.split()) <= 5 for h in heads), "כותרת היא שתיים עד חמש מילים")
    check(not any(re.search(r"[\u2013\u2014]", h) or re.match(r"[A-Za-z]", h) for h in heads),
          "בכותרת אין מקף ארוך, והיא לא מתחילה באנגלית")
    for qid, items in placements.items():
        seen = {}
        for r in items:
            seen.setdefault(str(r.get("headline") or ""), set()).add(r["text"])
        twice = sorted(h for h, texts in seen.items() if len(texts) > 1)
        check(not twice, f"באותה רצועה ({qid}) אין שני ציטוטים שונים עם אותה כותרת: {twice}")
    check(all(html.escape(h) in faq for h in set(heads)), "כל כותרת מופיעה בדף")
    check(sum(done.values()) == len(rows), "כל פריט בקובץ הנתונים מוצג בדף")
    # 13-10-2026: הערת עריכה של שלהבת נכנסה לנוסח של ציטוט ועלתה לאוויר (אילנה וייס, שאלה 8). כשהיא מכתיבה נוסח היא
    # מסיימת אותו ב"סוף ציטוט", ומה שבא אחריו הוא הערה פנימית ולא חלק מהציטוט.
    notes = sorted({r["qid"] for r in rows if "סוף ציטוט" in r["text"]})
    check(not notes, f"הערת עריכה בתוך נוסח של ציטוט ('סוף ציטוט'): {notes}")

# 4ב. הייבוא מקובץ העבודה מדפיס מה ישתנה בנתונים שבריפו, כרטיס אחר כרטיס
import import_faq_quotes_data as imp  # noqa: E402

row = lambda qid, **kw: dict({"qid": qid, "name": "דנה", "role": "", "photo": "", "text": "טקסט"}, **kw)
old_p = {"q07": [row("Q-1"), row("Q-2")], "q08": [row("Q-3"), row("Q-4")]}
check(imp.changes(old_p, old_p) == [], "ייבוא בלי שינוי לא מדווח על שינוי")
got = imp.changes(old_p, {"q07": [row("Q-1", text="אחר", role="תפקיד"), row("Q-5")], "q08": [row("Q-4"), row("Q-3")]})
check(got == ["q07 Q-1 דנה: השתנה role, text", "q07 Q-2 דנה: הוסר", "q07 Q-5 דנה: נוסף", "q08: סדר הכרטיסים השתנה"],
      f"ייבוא מדווח על כל שינוי בנפרד: {got}")

# 5. עיצוב וקוד: פעם אחת בכל דף, זהים
blocks = []
for rel in ("index.html", "faq/index.html"):
    t = (ROOT / rel).read_text(encoding="utf-8")
    check(t.count('<style id="tm-qm-css">') == 1 and t.count('<script id="tm-qm-js">') == 1, f"{rel}: עיצוב וקוד פעם אחת")
    blocks.append((b.CSS_RE.search(t).group(0), b.JS_RE.search(t).group(0)))
check(blocks[0] == blocks[1] == (b.CSS_BLOCK, b.JS_BLOCK), "העיצוב או הקוד שונים בין הדפים")
sales = (ROOT / "index.html").read_text(encoding="utf-8")
check(".tm-qm__card, .tm-review" in sales, "לשונית שיש בה רק רצועת ציטוטים חייבת להיחשב כלשונית עם תוכן")
check("window.tmQuoteMarquees()" in sales, "tmStrips מאתחל רצועות ציטוטים חדשות (העורך בדשבורד)")

if fails:
    print("נכשל:\n  " + "\n  ".join(fails))
    sys.exit(1)
print("כל הבדיקות עברו")
