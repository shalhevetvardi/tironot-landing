"""בדיקה שכל כפתור לנועם ב-index וב-hatzaa נושא את מספר הביקור (#v-) בסוף ההודעה, בסדר הנכון (25-10-2026),
וגם את הקוד האישי (#w-) כשהגיעו מקישור אישי (?who=), ומ-12-11-2026 גם בביקור חוזר מאותו דפדפן עד 30 יום.

מגיש את הריפו מקומית, פותח כל דף בדפדפן שמרנדר באמת (playwright), ובודק את ההודעה בכל כפתור לנועם ואת האירועים
שהמדידה שולחת. שום בקשה לא יוצאת מהמחשב: האוסף, הפיקסל והאנליטיקס חסומים, וגוף האירועים נלכד.

    <python עם playwright> scripts/check-noam-visit-id.py            # מתיקיית הריפו
    <python עם playwright> scripts/check-noam-visit-id.py <תיקייה>  # עותק אחר של הדף

ב-shalhevet2: ~/קוד/sales-automation/venv/bin/python, או python3 שמותקן בו playwright. ר' docs/מדידת-משפך-דף-הנחיתה.md, סעיף 12."""
import http.server, json, re, socketserver, sys, threading, urllib.parse
from functools import partial
from playwright.sync_api import sync_playwright

ROOT = sys.argv[1] if len(sys.argv) > 1 else str(__import__("pathlib").Path(__file__).resolve().parent.parent)


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


handler = partial(Quiet, directory=ROOT)
srv = socketserver.TCPServer(("127.0.0.1", 0), handler); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{port}"
V = r"#v-[a-f0-9]{16}"
# (כתובת, תבנית ההודעה בכל כפתור, הקוד האישי שצפוי באירועים, כתובת לטעינה שנייה באותה לשונית או None)
SCEN = [("index.html?src=test-vidcheck&ab=a", r"כמו שהיא כדי להתחיל לדבר עם נועם #test-vidcheck #ab-a " + V + "$", "", None),
        ("index.html?ab=a", r"שלחו את ההודעה הזו כדי להתחיל לדבר עם נועם #ab-a " + V + "$", "", None),
        ("hatzaa.html?src=test-vidcheck&ab=b", r"כמו שהיא כדי להתחיל לדבר עם נועם #test-vidcheck #ab-b " + V + "$", "", None),
        # קוד אישי: אחרון בהודעה, נשלח עם כל אירוע, ושורד טעינה נוספת באותה לשונית (sessionStorage)
        ("index.html?src=test-vidcheck&ab=a&who=test-who1", r"כמו שהיא כדי להתחיל לדבר עם נועם #test-vidcheck #ab-a " + V + " #w-test-who1$", "test-who1",
         "index.html?ab=a"),
        ("hatzaa.html?src=test-vidcheck&ab=b&who=test-who2", r"כמו שהיא כדי להתחיל לדבר עם נועם #test-vidcheck #ab-b " + V + " #w-test-who2$", "test-who2", None),
        # תווים שאינם a-z0-9_- נמחקים, גם בהודעה וגם באירוע
        ("index.html?ab=a&who=test-w%3Cb%3E%22.3", r"להתחיל לדבר עם נועם #ab-a " + V + " #w-test-wb3$", "test-wb3", None)]
fails = 0


def visit(pg, url, pat, who, events):
    pg.goto(url, wait_until="domcontentloaded"); pg.wait_for_timeout(1500)
    vid = pg.evaluate("sessionStorage.getItem('aim_vid')")
    texts = pg.evaluate("Array.from(document.querySelectorAll('a[href*=\"wa.me/972559397247\"]')).map(a => new URL(a.href).searchParams.get('text'))")
    tail = "#v-" + str(vid) + (" #w-" + who if who else "")
    bad = [t for t in texts if not re.search(pat, t or "") or not (t or "").endswith(tail)]
    ev_vids = {e.get("vid") for e in events}
    ev_who = {e.get("who", "") for e in events}
    # הקוד האישי יוצא מהכתובת (שיתוף הקישור לא מעביר אותו), ושאר הפרמטרים נשארים
    query = pg.evaluate("location.search")
    kept = all(f"{k}={v}" in query for k, v in urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query) if k != "who")
    clean_url = "who=" not in query and kept
    ok = bool(texts) and not bad and ev_vids <= {vid} and bool(events) and ev_who == {who} and clean_url
    return ok, (f"links={len(texts)} bad={len(bad)} vid_len={len(vid or '')} events={len(events)} event_vids_match={ev_vids <= {vid}} "
                f"event_who={sorted(ev_who)} url_without_who={clean_url}"), bad


with sync_playwright() as p:
    b = p.chromium.launch()
    for path, pat, who, again in SCEN:
        ctx = b.new_context(viewport={"width": 390, "height": 844})
        events = []
        def route(r):
            u = r.request.url
            if u.startswith(base):
                return r.continue_()
            if "r.aimprove.co.il/e" in u and r.request.post_data:
                events.append(json.loads(r.request.post_data))
            return r.abort()
        ctx.route("**/*", route)
        pg = ctx.new_page()
        steps = [(path, pat)] + ([(again, pat.replace("#test-vidcheck ", "").replace("כמו שהיא כדי", ""))] if again else [])
        for i, (url, pt) in enumerate(steps):
            events.clear()
            # בטעינה השנייה הקוד המקורי נשמר ב-localStorage, ולכן ההודעה נשארת עם הקוד; בודקים רק את הסוף
            ok, info, bad = visit(pg, f"{base}/{url}", pat if i == 0 else r"#w-" + who + "$", who, events)
            fails += not ok
            print(("OK  " if ok else "FAIL"), url, info)
            if bad: print("   example:", bad[0][-80:])
        ctx.close()
    # ביקור חוזר (12-11-2026): הדפדפן זוכר את הקוד 30 יום אחרי כניסה מקישור. כל תרחיש בדפדפן נקי משלו.
    def fresh():
        c = b.new_context(viewport={"width": 390, "height": 844})
        ev = []
        def rt(r):
            u = r.request.url
            if u.startswith(base):
                return r.continue_()
            if "r.aimprove.co.il/e" in u and r.request.post_data:
                ev.append(json.loads(r.request.post_data))
            return r.abort()
        c.route("**/*", rt)
        return c, ev

    def check(name, ok, info=""):
        global fails
        fails += not ok
        print(("OK  " if ok else "FAIL"), name, info)

    DAY = 86400000
    # 1. לשונית חדשה בלי ?who=, בתוך 30 יום: הקוד חוזר, בהודעה ובאירועים
    ctx, events = fresh(); pg = ctx.new_page()
    pg.goto(f"{base}/index.html?ab=a&who=test-who9", wait_until="domcontentloaded"); pg.wait_for_timeout(800)
    pg2 = ctx.new_page(); events.clear()
    ok, info, bad = visit(pg2, f"{base}/index.html?ab=a", r"#ab-a " + V + " #w-test-who9$", "test-who9", events)
    check("return visit within 30 days keeps the code", ok, info)
    # 2. קישור של אדם אחר מחליף את מה שנזכר
    pg3 = ctx.new_page(); events.clear()
    ok, info, bad = visit(pg3, f"{base}/hatzaa.html?ab=b&who=test-whoB", r"#ab-b " + V + " #w-test-whoB$", "test-whoB", events)
    kept = pg3.evaluate("JSON.parse(localStorage.getItem('aim_who_kept')||'null')")
    check("a link of another person replaces it", ok and kept and kept.get("w") == "test-whoB", info)
    # 3. "זו אני" מוחק את מה שנזכר
    pg3.goto(f"{base}/index.html?aim_optout=1", wait_until="domcontentloaded"); pg3.wait_for_timeout(500)
    gone = pg3.evaluate("localStorage.getItem('aim_who_kept')") is None
    check("this-is-me device forgets it", gone)
    ctx.close()
    # 4. אחרי 30 יום: לא חוזר, ונמחק. 5. תאריך עתידי (זיוף או שעון שגוי): לא חוזר.
    for label, shift in (("older than 30 days", -31 * DAY), ("timestamp in the future", 1 * DAY)):
        ctx, events = fresh(); pg = ctx.new_page()
        pg.goto(f"{base}/index.html?ab=a", wait_until="domcontentloaded"); pg.wait_for_timeout(300)
        pg.evaluate(f"localStorage.setItem('aim_who_kept', JSON.stringify({{w: 'test-whoOld', t: Date.now() + ({shift})}}))")
        pg2 = ctx.new_page(); events.clear()
        ok, info, bad = visit(pg2, f"{base}/index.html?ab=a", r"#ab-a " + V + "$", "", events)
        removed = pg2.evaluate("localStorage.getItem('aim_who_kept')") is None
        check(label + ": not used, and removed", ok and removed, info)
        ctx.close()
    # 6. בקרה: דפדפן אחר (בלי שום כניסה מקישור) לא מקבל קוד
    ctx, events = fresh(); pg = ctx.new_page(); events.clear()
    ok, info, bad = visit(pg, f"{base}/index.html?ab=a", r"#ab-a " + V + "$", "", events)
    check("another browser gets no code", ok, info)
    ctx.close()
    b.close()
srv.shutdown()
sys.exit(1 if fails else 0)
