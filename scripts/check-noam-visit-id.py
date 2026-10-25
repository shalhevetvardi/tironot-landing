"""בדיקה שכל כפתור לנועם ב-index וב-hatzaa נושא את מספר הביקור (#v-) בסוף ההודעה, בסדר הנכון (25-10-2026).

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
SCEN = [("index.html?src=test-vidcheck&ab=a", r"כמו שהיא כדי להתחיל לדבר עם נועם #test-vidcheck #ab-a #v-[a-f0-9]{16}$"),
        ("index.html?ab=a", r"שלחו את ההודעה הזו כדי להתחיל לדבר עם נועם #ab-a #v-[a-f0-9]{16}$"),
        ("hatzaa.html?src=test-vidcheck&ab=b", r"כמו שהיא כדי להתחיל לדבר עם נועם #test-vidcheck #ab-b #v-[a-f0-9]{16}$")]
fails = 0
with sync_playwright() as p:
    b = p.chromium.launch()
    for path, pat in SCEN:
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
        pg = ctx.new_page(); pg.goto(f"{base}/{path}", wait_until="domcontentloaded"); pg.wait_for_timeout(1500)
        vid = pg.evaluate("sessionStorage.getItem('aim_vid')")
        texts = pg.evaluate("Array.from(document.querySelectorAll('a[href*=\"wa.me/972559397247\"]')).map(a => new URL(a.href).searchParams.get('text'))")
        bad = [t for t in texts if not re.search(pat, t or "") or not (t or "").endswith("#v-" + str(vid))]
        ev_vids = {e.get("vid") for e in events}
        ok = texts and not bad and ev_vids <= {vid}
        fails += not ok
        print(("OK  " if ok else "FAIL"), path, f"links={len(texts)} bad={len(bad)} vid_len={len(vid or '')} events={len(events)} event_vids_match={ev_vids <= {vid}}")
        if bad: print("   example:", bad[0][-70:])
        ctx.close()
    b.close()
srv.shutdown()
sys.exit(1 if fails else 0)
