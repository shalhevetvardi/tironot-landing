"""בדיקת התנהגות של דף המכירה בטלפון, בדפדפן שמרנדר באמת (Chrome דרך Playwright, 375x812, מגע).
בודקת: סדר החלקים, שכל רצועה זזה בכל פריים ובקצב הנכון, שהחלקה באצבע מזיזה רצועה בלי לגלול את הדף ובלי לפתוח
כרטיס, שהקשה פותחת הודעה ו"חזרה" סוגרת, שה-X של סרטון מעל הסרטון וסוגר, ושהתווית "אתם כאן" גלויה.

    python3 -m http.server 8791 --bind 127.0.0.1     # מתיקיית הריפו, בחלון אחר
    <python עם playwright> scripts/check-sales-page-phone.py http://localhost:8791/ /tmp/shots

צריך Playwright ו-Google Chrome (ב-shalhevet2: ~/קוד/sales-automation/venv/bin/python). חלון דפדפן מוסתר לא מצייר,
ולכן מדידה של תנועה שם חסרת משמעות - הבדיקה הזו מריצה דפדפן משלה.
לא נספר במדידת המשפך (aim_optout) ובלי חלון העוגיות (aim_consent=denied). שגיאת "Failed to fetch" אחת קיימת גם
בדף החי מ-15-10-2026 ואינה מהרצועות."""
import json, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

URL, OUT = sys.argv[1], Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
INIT = "try{localStorage.setItem('aim_optout','1');localStorage.setItem('aim_consent','denied')}catch(e){}"
results, errors = {}, []


def ok(name, cond, detail=""):
    results[name] = (bool(cond), detail)


with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True, args=["--autoplay-policy=no-user-gesture-required"])
    ctx = b.new_context(viewport={"width": 375, "height": 812}, device_scale_factor=2, is_mobile=True, has_touch=True)
    ctx.add_init_script(INIT)
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append(str(e)))
    console_errors = []
    page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
    page.goto(URL, wait_until="load")
    page.wait_for_timeout(2500)

    # 1. סדר החלקים: גוגל מיד אחרי "וזה כבר קורה", והסרטון של שלהבת מיד לפני הכפתור של נועם
    order = page.evaluate("[...document.querySelectorAll('body > section')].map(s => s.id || s.className.split(' ').slice(-2).join(' '))")
    ok("order: google after proofs", order.index("tm-google") == order.index("section--proofs center") + 1, order)
    ok("order: noam video right before final CTA", order.index("video-noam") + 1 == order.index("center final"), order)

    # 2. התנועה: כל רצועה גלויה זזה, ובכל פריים (לא בקפיצות של פיקסל שלם)
    def sample(sel):
        return page.evaluate("""async (sel) => {
          const el = document.querySelector(sel);
          // שוב אחרי רגע: תמונות שנטענות מעל דוחפות את הרצועה למטה
          for (const w of [500, 500]) { el.scrollIntoView({block:'center', behavior:'instant'}); await new Promise(r => setTimeout(r, w)); }
          const tr = el.querySelector('.tm-track, .tm-qm__track'), xs = [];
          // הדף החדש זז ב-transform; הישן בגלילה (scrollLeft) - קוראים את מה שזז בפועל
          const read = () => { const m = new DOMMatrix(getComputedStyle(tr).transform).m41; return m || -el.scrollLeft; };
          let t0, t1;
          await new Promise(res => { t0 = performance.now(); (function f(){
            xs.push(read()); t1 = performance.now();
            if (t1 - t0 < 2000) requestAnimationFrame(f); else res(); })(); });
          const d = xs.slice(1).map((x, i) => x - xs[i]);
          const still = d.filter(v => Math.abs(v) < 0.01).length;
          const frac = xs.filter(x => Math.abs(x - Math.round(x)) > 0.01).length;
          return { frames: d.length, speed: +Math.abs((xs[xs.length-1] - xs[0]) / ((t1 - t0) / 1000)).toFixed(1), still, wholePixelsOnly: frac === 0, maxStep: +Math.max(...d.map(Math.abs)).toFixed(2) };
        }""", sel)

    for name, sel in [("quick (בוגרים מספרים)", "#tm-quick .tm-band"), ("intro (מרגישים בטירונות)", "#intro .tm-band"),
                      ("inside (מה תלמידים בונים)", "#tm-inside .tm-band"), ("google", "#tm-google .tm-band"),
                      ("worth quotes", "#price .tm-qm__row.is-on")]:
        s = sample(sel)
        # קצב 42-45 פיקסלים בשנייה; "still" = פריימים בלי תזוזה, wholePixelsOnly = קפיצות של פיקסל שלם (הרעידה הישנה)
        ok(f"moves smoothly: {name}", 35 < s["speed"] < 55 and s["still"] <= s["frames"] * 0.1 and not s["wholePixelsOnly"], s)

    # 3. החלקה באצבע ברצועת הציטוטים ובוואטסאפ: הרצועה זזה עם האצבע, והדף לא נגלל
    cdp = ctx.new_cdp_session(page)

    def swipe(sel, dx):
        box = page.evaluate("""(sel) => { const el = document.querySelector(sel); el.scrollIntoView({block:'center', behavior:'instant'});
            const r = el.getBoundingClientRect(); return {x: r.left + r.width/2, y: r.top + r.height/2}; }""", sel)
        page.wait_for_timeout(300)
        before = page.evaluate("(sel) => [document.querySelector(sel)._tmMq.pos, scrollY, document.querySelector(sel)._tmMq.half]", sel)
        x, y = box["x"], box["y"]
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]})
        for i in range(1, 11):
            cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x + dx * i / 10, "y": y + 2}]})
            page.wait_for_timeout(16)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        page.wait_for_timeout(50)
        after = page.evaluate("(sel) => [document.querySelector(sel)._tmMq.pos, scrollY, !!document.querySelector('.tm-qm-modal:not([hidden]), .tm-ilb:not([hidden])')]", sel)
        return before, after

    for name, sel in [("worth quotes", "#price .tm-qm__row.is-on"), ("inside shots", "#tm-inside .tm-band")]:
        before, after = swipe(sel, -160)
        moved = (after[0] - before[0]) % before[2]   # הלולאה עוטפת; אצבע שמאלה = התקדמות קדימה
        ok(f"finger swipe moves strip: {name}", 120 < moved < 450 and after[1] == before[1],
           {"moved": round(moved, 1), "pageScroll": after[1] - before[1], "openedSomething": after[2]})
        ok(f"swipe does not open a card: {name}", not after[2])
        page.keyboard.press("Escape")

    # 4. הקשה (בלי החלקה) על הודעה פותחת אותה, ו"חזרה" סוגרת ונשארת בדף
    for _ in range(2):
        page.evaluate("document.querySelector('#tm-inside .tm-band').scrollIntoView({block:'center', behavior:'instant'})")
        page.wait_for_timeout(500)
    # הודעה שנמצאת עכשיו באמצע המסך (הרצועה זזה, ולכן לא הראשונה ברשימה)
    bb = page.evaluate("""() => { const bs = [...document.querySelectorAll('#tm-inside .tm-band .tm-shot button')];
        const r = bs.map(b => b.getBoundingClientRect()).find(r => r.left + r.width/2 > 60 && r.left + r.width/2 < innerWidth - 60);
        return r && {x: r.left, y: r.top, width: r.width, height: r.height}; }""")
    page.touchscreen.tap(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
    page.wait_for_timeout(300)
    opened = page.evaluate("!!document.querySelector('.tm-ilb:not([hidden])')")
    print("tap target:", page.evaluate("(b) => { const h = document.elementFromPoint(b.x + b.width/2, b.y + b.height/2); return h && h.outerHTML.slice(0, 80); }", bb), "opened:", opened)
    if opened:
        page.go_back(); page.wait_for_timeout(300)
    ok("tap opens message; back closes it and stays on page",
       opened and not page.evaluate("!!document.querySelector('.tm-ilb:not([hidden])')") and page.url.rstrip('/') == URL.rstrip('/'),
       {"opened": opened, "url": page.url})

    # 5. סרטון בכרטיס: ה-X למעלה הוא ה-X, לחיצה עליו סוגרת; "חזרה" סוגרת ונשארת בדף
    page.set_viewport_size({"width": 390, "height": 660})
    page.wait_for_timeout(200)
    card = page.locator(".proof__more[data-v]").first
    card.scroll_into_view_if_needed(); card.click()
    page.wait_for_timeout(1200)
    top = page.evaluate("""() => { const x = document.querySelector('.cf-lb-close').getBoundingClientRect();
        const h = document.elementFromPoint(x.left + x.width/2, x.top + x.height/2); return h && h.className; }""")
    page.screenshot(path=str(OUT / "video-open.png"))
    page.locator(".cf-lb-close").click(); page.wait_for_timeout(400)
    closed = page.evaluate("document.querySelector('.cf-lb').hidden")
    ok("video X is on top and closes", top == "cf-lb-close" and closed, {"topElement": top, "closed": closed})
    card.click(); page.wait_for_timeout(800)
    page.go_back(); page.wait_for_timeout(400)
    ok("video: back closes and stays on page", page.evaluate("document.querySelector('.cf-lb').hidden") and page.url.rstrip('/') == URL.rstrip('/'), page.url)
    page.set_viewport_size({"width": 375, "height": 812})

    # 6. "אתם כאן" לא מכוסה
    page.evaluate("document.getElementById('jrnCard').scrollIntoView({block:'center', behavior:'instant'})")
    page.wait_for_timeout(3000)
    here = page.evaluate("""() => { const b = document.querySelector('.jrn-here').getBoundingClientRect();
        const c = document.querySelector('#jrn1 .jrn-active').getBoundingClientRect();
        const pts = [[b.left+6,b.top+b.height/2],[b.left+b.width/2,b.top+b.height/2],[b.right-6,b.top+b.height/2]];
        const hits = pts.map(p => { const h = document.elementFromPoint(p[0], p[1]); return h && h.classList.contains('jrn-here'); });
        return { hits, overlap: !(b.bottom <= c.top || b.top >= c.bottom || b.right <= c.left || b.left >= c.right),
                 badge: [b.top, b.bottom].map(Math.round), circle: [c.top, c.bottom].map(Math.round) }; }""")
    ok("'you are here' badge fully visible", all(here["hits"]) and not here["overlap"], here)
    page.locator("#jrnCard").screenshot(path=str(OUT / "jrn.png"))

    for sel, name in [("#tm-google", "google"), ("#tm-worth", "worth"), ("#tm-inside", "inside")]:
        page.evaluate(f"document.querySelector('{sel}').scrollIntoView({{block:'start', behavior:'instant'}})")
        page.wait_for_timeout(500)
        page.screenshot(path=str(OUT / f"{name}.png"))

    # "Failed to fetch" אחד קיים גם בדף החי מ-15-10-2026, לפני הרצועות - מוצג, לא נכשל. כל שגיאה אחרת נכשלת
    known = [e for e in errors if e == "Failed to fetch"]
    ok("no script errors on the page", not [e for e in errors if e != "Failed to fetch"], errors[:5])
    if known:
        print("known script error (also on the live page before this change):", known[0])
    print("console errors (info, network on localhost):", [e[:90] for e in console_errors][:6])
    b.close()

for k, (v, d) in results.items():
    print(("PASS " if v else "FAIL ") + k + ("" if v else f"  -> {json.dumps(d, ensure_ascii=False)[:300]}"))
print("all:", all(v for v, _ in results.values()))
