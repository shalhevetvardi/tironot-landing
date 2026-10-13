#!/usr/bin/env python3
"""build_faq_quotes.py - רצועות ציטוטי הבוגרים בדף השאלות, והעיצוב והקוד שלהן בשני הדפים (12-10-2026).

    python3 scripts/build_faq_quotes.py            # כותב את faq/index.html ואת index.html
    python3 scripts/build_faq_quotes.py --check    # לא כותב; יוצא בכשל אם משהו לא מעודכן

מה הוא עושה:
  1. מתחת לתשובה של כל שאלה בדף השאלות (q07-q41) שנבחרו לה ציטוטים: רצועת ציטוטים, בין הסימנים
     <!-- tm-qm:qXX --> ... <!-- /tm-qm:qXX -->. ציטוט אחד - כרטיס אחד, בלי רצועה. אחרי הציטוט של סיגל
     (אם יש) ולפני נגן הסרטונים. הפעלה חוזרת מחליפה את מה שבין הסימנים ולא מוסיפה.
  2. העיצוב (<style id="tm-qm-css">) והקוד (<script id="tm-qm-js">) של הרצועות, זהים בשני הדפים. המקור היחיד
     שלהם הוא הקובץ הזה: לא לערוך אותם ביד בדף, אלא כאן ולהריץ.

מקורות: הבחירות של שלהבת לכל שאלה (הדגשות בסוגריים מרובעים) והשאלות, מתוך scripts/faq-quotes-data/ בריפו
(placements.json, questions.json). סבבי הבחירה עצמם נעשים בתיקיית עבודה במחשב, ו-scripts/import_faq_quotes_data.py
מביא משם לריפו את מה שמוצג בדף. אפשר לתת נתיבים אחרים ב---placements וב---items.

המבנה של כרטיס הוא חוזה עם דף המכירה: sales-automation/modules/testimonial_sales_model.py (quote_marquee)
בונה בדיוק אותו HTML ללשוניות "עדיין מתלבטים?". שינוי כאן = שינוי שם, ולהפך. הבדיקה:
scripts/test-faq-quotes.py.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "scripts" / "faq-quotes-data"          # נכתב ע"י scripts/import_faq_quotes_data.py; לא לערוך ביד
DEFAULT_PLACEMENTS = DATA / "placements.json"
DEFAULT_ITEMS = DATA / "questions.json"
FAQ_RANGE = range(7, 42)            # q07-q41: שאלות בדף השאלות. q01-q05 הן לשוניות בדף המכירה (דרך הדשבורד)
PHOTO_PREFIX = "../"                # התמונות בשורש האתר, ודף השאלות בתיקייה faq/
AVATARS = 6                         # tm-qm__av--0..5
TWO_ROWS = 4                        # מתחת לזה: רצועה אחת

# ------------------------------------------------------------------ עיצוב וקוד (מקור יחיד לשני הדפים)
CSS = r"""
/* רצועות ציטוטי הבוגרים (12-10-2026): "המשפט הבולט ככותרת" עם מירכאה צהובה. נוצר ב-scripts/build_faq_quotes.py */
.tm-qm { display: grid; gap: 14px; margin: 22px 0 6px; direction: rtl; text-align: right; }
.tm-qm__row { position: relative; direction: ltr; overflow-x: auto; overflow-y: hidden; scrollbar-width: none;
  -webkit-mask-image: linear-gradient(90deg, transparent, #000 6%, #000 94%, transparent);
  mask-image: linear-gradient(90deg, transparent, #000 6%, #000 94%, transparent); }
.tm-qm__row::-webkit-scrollbar { display: none; }
.tm-qm__row.is-on { overflow: hidden; }
.tm-qm__track { display: flex; align-items: stretch; width: max-content; padding: 5px 0; }
.tm-qm__row.is-on .tm-qm__track { animation: tmQmSlide var(--qm-dur, 60s) linear infinite; }
.tm-qm__row--rev.is-on .tm-qm__track { animation-direction: reverse; }
.tm-qm__row:hover .tm-qm__track, .tm-qm__row:focus-within .tm-qm__track { animation-play-state: paused; }
@keyframes tmQmSlide { from { transform: translateX(0); } to { transform: translateX(-50%); } }
@media (prefers-reduced-motion: reduce) {
  .tm-qm__row.is-on { overflow-x: auto; }
  .tm-qm__row.is-on .tm-qm__track { animation: none; }
}
.tm-qm__card { direction: rtl; text-align: right; flex: 0 0 auto; width: 330px; margin: 0 8px; display: flex; flex-direction: column;
  background: #F4F2FB; border: 1px solid #E6E1F5; border-radius: 18px; padding: 20px; font: inherit; color: #14093B;
  line-height: 1.5; cursor: pointer; -webkit-appearance: none; appearance: none; }
.tm-qm__card:hover { border-color: #CFC7EE; }
.tm-qm__card:focus-visible { outline: 3px solid #6762FF; outline-offset: 3px; }
.tm-qm--one .tm-qm__card { width: auto; max-width: 560px; margin: 0; }
.tm-qm__h { display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden;
  font-weight: 800; font-size: 21px; line-height: 1.35; color: #14093B; text-wrap: balance; }
.tm-qm__h::before, .tm-qm-modal__sheet::before { content: "\201D"; color: #FFD747; font: 900 1.25em/1 Georgia, serif;
  text-shadow: 0 1px 0 rgba(20,9,59,.28); margin-inline-end: 4px; vertical-align: -0.12em; }
.tm-qm__q { display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; margin-top: 10px;
  font-size: 14.5px; line-height: 1.6; color: #5A5873; font-weight: 400; }
.tm-qm__l + .tm-qm__l::before { content: " "; }
.tm-qm__note { display: none; }
.tm-qm__who { display: flex; align-items: center; gap: 10px; margin-top: auto; padding-top: 14px; }
.tm-qm__av { flex: 0 0 auto; width: 42px; height: 42px; border-radius: 50%; object-fit: cover; display: grid; place-items: center;
  font-weight: 800; font-size: 16px; line-height: 1; color: #fff; background: #6762FF; }
.tm-qm__av--1 { background: #1B5B9E; } .tm-qm__av--2 { background: #A52756; } .tm-qm__av--3 { background: #2473C8; }
.tm-qm__av--4 { background: #7A3E9D; } .tm-qm__av--5 { background: #14093B; }
.tm-qm__id { min-width: 0; }
.tm-qm__name { display: block; font-weight: 700; font-size: 15px; line-height: 1.3; color: #14093B; }
.tm-qm__role { display: block; font-size: 13px; line-height: 1.35; color: #5A5873; }
.tm-qm .tm-hl, .tm-qm-modal .tm-hl { text-decoration: underline; text-decoration-color: #E0342F; text-decoration-thickness: 2.5px;
  text-underline-offset: 5px; text-decoration-skip-ink: none; }
@media (max-width: 560px) { .tm-qm__card { width: 280px; padding: 18px; } .tm-qm__h { font-size: 19px; } }
.tm-qm-modal[hidden] { display: none; }
.tm-qm-modal { position: fixed; inset: 0; z-index: 9100; display: grid; place-items: center; padding: 16px; background: rgba(12,6,32,.62); }
.tm-qm-modal__sheet { position: relative; width: 100%; max-width: 560px; max-height: 85vh; overflow: auto; padding: 26px 24px 22px;
  background: #fff; color: #14093B; border-radius: 22px; direction: rtl; text-align: right; line-height: 1.7;
  box-shadow: 0 24px 60px rgba(12,6,32,.35); }
.tm-qm-modal__sheet::before { display: block; font-size: 52px; margin: 0 0 4px; }
.tm-qm-modal__x { position: absolute; top: 10px; left: 12px; width: 40px; height: 40px; border-radius: 50%; border: 0;
  background: #ECE9F8; color: #14093B; font: 400 24px/40px Arial, sans-serif; cursor: pointer; }
.tm-qm-modal .tm-qm__q { display: block; -webkit-line-clamp: unset; overflow: visible; margin: 0;
  font-size: 17px; line-height: 1.7; font-weight: 600; color: #14093B; }
.tm-qm-modal .tm-qm__l { display: block; margin: 0 0 8px; }
.tm-qm-modal .tm-qm__l + .tm-qm__l::before { content: none; }
.tm-qm-modal .tm-qm__note { display: block; margin-top: 12px; font-size: 13.5px; line-height: 1.5; font-weight: 400; color: #5A5873; }
.tm-qm-modal .tm-qm__who { padding-top: 16px; }
"""

JS = r"""
/* רצועות ציטוטי הבוגרים (12-10-2026). נוצר ב-scripts/build_faq_quotes.py - לערוך שם.
   כל רצועה (.tm-qm__row) מוכפלת עד שחצי ממנה ממלא את הרוחב, וזזה חצי אחורה בלולאה (CSS), כ-30 פיקסלים בשנייה.
   הבנייה קורית כשהרצועה נראית (לשונית או תשובה סגורה ברוחב 0), ושוב כשהרוחב משתנה. מעבר עכבר או מקלדת עוצר.
   "פחות תנועה" במכשיר: בלי הכפלה ובלי תנועה, והרצועה נגללת ביד. לחיצה על כרטיס פותחת את הציטוט המלא.
   window.tmQuoteMarquees() מאתחל רצועות חדשות (למשל אחרי שהעורך בדשבורד החליף תוכן), ובטוח להריץ שוב. */
(function () {
  var SPEED = 30;
  var reduce = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  var fits = [];
  function setup(row) {
    var track = row.querySelector('.tm-qm__track');
    if (!track) return;
    var orig = [].slice.call(track.children).filter(function (c) { return !c.hasAttribute('data-clone'); });
    var built = -1;
    function fit() {
      var w = row.clientWidth;
      if (!w || !orig.length || Math.abs(w - built) < 2) return;
      [].slice.call(track.querySelectorAll('[data-clone]')).forEach(function (c) { c.parentNode.removeChild(c); });
      var set = 0;
      orig.forEach(function (c) {
        var s = getComputedStyle(c);
        set += c.offsetWidth + (parseFloat(s.marginLeft) || 0) + (parseFloat(s.marginRight) || 0);
      });
      if (!set) return;
      built = w;
      var reps = Math.max(1, Math.ceil(w / set));
      for (var r = 1; r < 2 * reps; r++) {
        orig.forEach(function (c) {
          var k = c.cloneNode(true);
          k.setAttribute('data-clone', '1'); k.setAttribute('aria-hidden', 'true'); k.tabIndex = -1;
          track.appendChild(k);
        });
      }
      row.style.setProperty('--qm-dur', Math.max(20, set * reps / SPEED).toFixed(1) + 's');
      row.classList.add('is-on');
    }
    fits.push(fit);
    if ('ResizeObserver' in window) new ResizeObserver(fit).observe(row);
    fit();
  }
  window.tmQuoteMarquees = function () {
    if (reduce) return;
    [].forEach.call(document.querySelectorAll('.tm-qm__row'), function (row) {
      if (row._tmQm) return;
      row._tmQm = 1;
      setup(row);
    });
  };
  window.addEventListener('resize', function () { fits.forEach(function (f) { f(); }); });

  var modal = null, body = null, last = null, prevOverflow = '';
  function build() {
    modal = document.createElement('div');
    modal.className = 'tm-qm-modal'; modal.hidden = true;
    modal.innerHTML = '<div class="tm-qm-modal__sheet" role="dialog" aria-modal="true" aria-label="הציטוט המלא">' +
      '<button type="button" class="tm-qm-modal__x" aria-label="סגירה">×</button><div class="tm-qm-modal__body"></div></div>';
    document.body.appendChild(modal);
    body = modal.querySelector('.tm-qm-modal__body');
    modal.addEventListener('click', function (e) {
      if (e.target === modal || (e.target.closest && e.target.closest('.tm-qm-modal__x'))) close();
    });
  }
  function open(card) {
    if (!modal) build();
    last = card; body.textContent = '';
    ['.tm-qm__q', '.tm-qm__who'].forEach(function (sel) {
      var n = card.querySelector(sel);
      if (n) body.appendChild(n.cloneNode(true));
    });
    modal.hidden = false;
    prevOverflow = document.body.style.overflow; document.body.style.overflow = 'hidden';
    modal.querySelector('.tm-qm-modal__x').focus();
  }
  function close() {
    if (!modal || modal.hidden) return;
    modal.hidden = true;
    document.body.style.overflow = prevOverflow;
    if (last && last.isConnected && !last.hasAttribute('data-clone')) last.focus();
  }
  window.tmQuoteModal = { open: open, close: close };
  document.addEventListener('click', function (e) {
    var c = e.target.closest ? e.target.closest('.tm-qm__card') : null;
    if (!c || (modal && modal.contains(c))) return;
    e.preventDefault();
    open(c);
  });
  document.addEventListener('keydown', function (e) {
    if (!modal || modal.hidden) return;
    if (e.key === 'Escape') { close(); return; }
    if (e.key === 'Tab') { e.preventDefault(); modal.querySelector('.tm-qm-modal__x').focus(); }
  });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', window.tmQuoteMarquees);
  else window.tmQuoteMarquees();
})();
"""

CSS_BLOCK = f'<style id="tm-qm-css">{CSS}</style>'
JS_BLOCK = f'<script id="tm-qm-js">{JS}</script>'
CSS_RE = re.compile(r'<style id="tm-qm-css">.*?</style>', re.S)
JS_RE = re.compile(r'<script id="tm-qm-js">.*?</script>', re.S)


# ------------------------------------------------------------------ כרטיס (חוזה עם testimonial_sales_model)
def _esc(t) -> str:
    return html.escape("" if t is None else str(t), quote=True)


def avatar_index(name) -> int:
    return sum(ord(c) for c in str(name or "")) % AVATARS


def parse_brackets(raw: str) -> Tuple[str, List[Tuple[int, int]]]:
    """טקסט עם [הדגשות] ← (טקסט נקי, טווחי ההדגשות). "[...]" נשאר טקסט. "]" בלי "[" פתוח לפניו (טעות הקלדה,
    כמו "]קיבלתי את הרישיון]") נקרא כ"[". סוגר שלא נסגר - נשאר כטקסט."""
    out, ranges, i, start = "", [], 0, None
    while i < len(raw):
        if raw.startswith("[...]", i) and start is None:
            out += "[...]"
            i += 5
            continue
        ch = raw[i]
        if ch == "[" and start is None:
            start = len(out)
        elif ch == "]" and start is not None:
            if len(out) > start:
                ranges.append((start, len(out)))
            start = None
        elif ch == "]":
            start = len(out)
        else:
            out += ch
        i += 1
    if start is not None:                                  # "[" שלא נסגר: מחזירים אותו כטקסט
        out = out[:start] + "[" + out[start:]
        ranges = [(a + (a >= start), b + (b > start)) for a, b in ranges]
    return out.strip("\n"), ranges


def _hl_span(text: str, a: int, b: int, ranges) -> str:
    out, pos = "", a
    for x, y in ranges:
        x, y = max(x, a), min(y, b)
        if x >= y:
            continue
        out += f'{_esc(text[pos:x])}<span class="tm-hl">{_esc(text[x:y])}</span>'
        pos = y
    return out + _esc(text[pos:b])


def quote_lines(text: str, ranges) -> str:
    out, pos = "", 0
    for line in text.split("\n"):
        a, b = pos, pos + len(line)
        pos = b + 1
        body = line.strip()
        if not body:
            continue
        a += len(line) - len(line.lstrip())
        b = a + len(body)
        cls = "l"
        if body.startswith("*"):
            cls = "note"
            a += len(body) - len(body[1:].lstrip())
        if a < b:
            out += f'<span class="tm-qm__{cls}">{_hl_span(text, a, b, ranges)}</span>'
    return out


def headline(text: str, ranges) -> str:
    if ranges:
        a, b = ranges[0]
        return text[a:b]
    for line in text.split("\n"):
        body = line.strip()
        if body and not body.startswith("*"):
            return re.split(r"[.!?]", body)[0].strip() or body
    return ""


def card(it: dict, photo_prefix: str = PHOTO_PREFIX) -> str:
    # הכותרת: השדה "headline" של הציטוט אם יש (נכתבת ביד, לפי docs/פרומפט-כותרות-ציטוטים.md),
    # ואחרת ההדגשה הראשונה. כותרת שנגזרת מהדגשה יוצאת לעיתים קרובות שבר משפט שאינו מובן בלי הציטוט.
    text, ranges = parse_brackets(str(it.get("text") or ""))
    name = str(it.get("name") or "")
    if it.get("photo"):
        av = f'<img class="tm-qm__av" src="{_esc(photo_prefix + it["photo"])}" alt="" loading="lazy">'
    else:
        av = f'<span class="tm-qm__av tm-qm__av--{avatar_index(name)}" aria-hidden="true">{_esc(name.strip()[:1])}</span>'
    role = f'<span class="tm-qm__role">{_esc(it["role"])}</span>' if it.get("role") else ""
    return (f'<button type="button" class="tm-qm__card">'
            f'<span class="tm-qm__h">{_esc(str(it.get("headline") or "").strip() or headline(text, ranges))}</span>'
            f'<span class="tm-qm__q">{quote_lines(text, ranges)}</span>'
            f'<span class="tm-qm__who">{av}<span class="tm-qm__id">'
            f'<span class="tm-qm__name">{_esc(name)}</span>{role}</span></span></button>')


def marquee(items: List[dict], photo_prefix: str = PHOTO_PREFIX) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return f'<div class="tm-qm tm-qm--one">{card(items[0], photo_prefix)}</div>'
    rows = [items[0::2], items[1::2]] if len(items) >= TWO_ROWS else [items]
    out = ""
    for n, row in enumerate(rows):
        out += (f'<div class="tm-qm__row{" tm-qm__row--rev" if n else ""}"><div class="tm-qm__track">'
                + "".join(card(q, photo_prefix) for q in row) + "</div></div>")
    return f'<div class="tm-qm">{out}</div>'


# ------------------------------------------------------------------ דף השאלות
def _norm_q(s: str) -> str:
    s = html.unescape(re.sub(r"<[^>]+>", "", s))
    return re.sub(r"\s+", " ", re.sub(r"[\u2013\u2014-]", "-", s)).strip()


def _summary_spans(page: str) -> List[Tuple[str, int, int]]:
    """(שאלה מנורמלת, התחלת <details>, סוף </details>) לכל שאלה בדף."""
    out = []
    for m in re.finditer(r"<summary>(.*?)</summary>", page, re.S):
        q = _norm_q(re.sub(r'<span class="arrow">.*?</span>', "", m.group(1)))
        start = page.rfind("<details", 0, m.start())
        end = page.find("</details>", m.end())
        out.append((q, start, end))
    return out


def _block(qid: str, inner: str) -> str:
    return f"<!-- tm-qm:{qid} -->{inner}<!-- /tm-qm:{qid} -->"


def apply_faq(page: str, placements: Dict[str, List[dict]], items: List[dict]) -> Tuple[str, Dict[str, int]]:
    """הדף עם בלוק לכל שאלה שיש לה ציטוטים, ו{מזהה: כמה ציטוטים}. שאלה בלי ציטוטים - הבלוק שלה (אם היה) יוצא."""
    questions = {str(x["id"]).lower(): x["q"] for x in items}
    done: Dict[str, int] = {}
    for n in FAQ_RANGE:
        qid = f"q{n:02d}"
        chosen = [it for it in placements.get(qid, []) if not it.get("exclude")]
        old = re.compile(r"[ \t]*" + re.escape(f"<!-- tm-qm:{qid} -->") + r".*?" + re.escape(f"<!-- /tm-qm:{qid} -->") + r"\n?", re.S)
        page = old.sub("", page)
        if not chosen:
            continue
        if qid not in questions:
            raise ValueError(f"השאלה {qid} לא נמצאת ב-items.json")
        target = _norm_q(questions[qid])
        hits = [s for s in _summary_spans(page) if s[0] == target]
        if len(hits) != 1:
            raise ValueError(f"השאלה {qid} («{questions[qid]}») נמצאה {len(hits)} פעמים בדף השאלות")
        _q, a, b = hits[0]
        seg = page[a:b]
        gal = seg.find('<p class="gallery-label">')
        if gal != -1:                                       # לפני נגן הסרטונים (ואחרי הציטוט של סיגל, אם יש)
            at = page.rfind("\n", a, a + gal) + 1
        else:
            close = seg.rfind("</div>")
            if close == -1:
                raise ValueError(f"לשאלה {qid} אין תשובה בדף")
            at = page.rfind("\n", a, a + close) + 1
        indent = "            "
        page = page[:at] + indent + _block(qid, marquee(chosen)) + "\n" + page[at:]
        done[qid] = len(chosen)
    return page, done


def ensure_assets(page: str) -> str:
    """העיצוב לפני </head> והקוד לפני </body>, פעם אחת; הפעלה חוזרת מחליפה את הקיים."""
    if CSS_RE.search(page):
        page = CSS_RE.sub(lambda _m: CSS_BLOCK, page, count=1)
    else:
        i = page.find("</head>")
        if i == -1:
            raise ValueError("בדף אין </head>")
        page = page[:i] + CSS_BLOCK + "\n" + page[i:]
    if JS_RE.search(page):
        page = JS_RE.sub(lambda _m: JS_BLOCK, page, count=1)
    else:
        i = page.rfind("</body>")
        if i == -1:
            raise ValueError("בדף אין </body>")
        page = page[:i] + JS_BLOCK + "\n" + page[i:]
    return page


def build(root: Path, placements: Dict[str, List[dict]], items: List[dict]) -> Tuple[Dict[Path, str], Dict[str, int]]:
    faq_path, sales_path = root / "faq" / "index.html", root / "index.html"
    faq, done = apply_faq(faq_path.read_text(encoding="utf-8"), placements, items)
    return {faq_path: ensure_assets(faq), sales_path: ensure_assets(sales_path.read_text(encoding="utf-8"))}, done


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--placements", default=str(DEFAULT_PLACEMENTS))
    ap.add_argument("--items", default=str(DEFAULT_ITEMS))
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--check", action="store_true", help="לא כותב; כשל אם משהו לא מעודכן")
    args = ap.parse_args(argv)
    placements = json.loads(Path(args.placements).read_text(encoding="utf-8"))
    items = json.loads(Path(args.items).read_text(encoding="utf-8"))
    pages, done = build(Path(args.root), placements, items)
    stale = [p for p, text in pages.items() if p.read_text(encoding="utf-8") != text]
    multi = sum(1 for n in done.values() if n > 1)
    print(f"שאלות עם ציטוטים: {len(done)} (רצועה: {multi}, כרטיס אחד: {len(done) - multi}), ציטוטים: {sum(done.values())}")
    if args.check:
        for p in stale:
            print(f"לא מעודכן: {p.relative_to(Path(args.root))}")
        return 1 if stale else 0
    for p in stale:
        p.write_text(pages[p], encoding="utf-8")
        print(f"נכתב: {p.relative_to(Path(args.root))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
