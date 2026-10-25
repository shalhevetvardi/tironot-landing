"""בדיקה שכל כפתור לנועם ב-index וב-hatzaa נושא את מספר הביקור (#v-) בסוף ההודעה, בסדר הנכון (25-10-2026),
וגם את הקוד האישי (#w-) כשהגיעו מקישור אישי (?who=), רק לביקור הזה.

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
    # בקרה: לשונית חדשה בלי ?who= לא יורשת קוד אישי
    ctx = b.new_context(viewport={"width": 390, "height": 844})
    events = []
    def route2(r):
        u = r.request.url
        if u.startswith(base):
            return r.continue_()
        if "r.aimprove.co.il/e" in u and r.request.post_data:
            events.append(json.loads(r.request.post_data))
        return r.abort()
    ctx.route("**/*", route2)
    pg = ctx.new_page()
    pg.goto(f"{base}/index.html?ab=a&who=test-who9", wait_until="domcontentloaded"); pg.wait_for_timeout(800)
    pg2 = ctx.new_page(); events.clear()
    ok, info, bad = visit(pg2, f"{base}/index.html?ab=a", r"#ab-a " + V + "$", "", events)
    fails += not ok
    print(("OK  " if ok else "FAIL"), "new tab without who", info)
    ctx.close()
    b.close()
srv.shutdown()
sys.exit(1 if fails else 0)
