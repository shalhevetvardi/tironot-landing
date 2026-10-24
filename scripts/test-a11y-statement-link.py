"""Usage: python3 scripts/test-a11y-statement-link.py [repo-root]   (default: the repo this file is in)

Five real pages: exactly one footer anchor to each of privacy, terms, accessibility
(exact label, no target). Two other pages (stories.html, referral-program): exactly one
accessibility anchor and no privacy/terms anchor. Page-wide counts are also checked, so a
duplicate outside the footer is caught; faq/index.html keeps one pre-existing in-answer
terms link (target=_blank), which is the only allowed extra."""
import sys, subprocess, os
from html.parser import HTMLParser

U = {"privacy": ("https://aimprove.co.il/privacy-policy/", "מדיניות פרטיות"),
     "terms": ("https://aimprove.co.il/terms-of-use/", "תקנון"),
     "a11y": ("https://aimprove.co.il/accessibility-statement/", "הצהרת נגישות")}
FIVE = {"index.html", "hatzaa.html", "bogrim/index.html", "faq/index.html", "usa/index.html", "usa/en/index.html"}  # hatzaa: הגרסה לקהל קר, נבנית מ-index.html
OTHER = {"stories.html", "referral-program/index.html"}
PREEXISTING_EXTRA = {("faq/index.html", "terms"): 1}
VOID = {"meta", "link", "img", "br", "hr", "input", "source", "area", "base", "col", "embed", "wbr", "track", "param"}
root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class P(HTMLParser):
    def __init__(s):
        super().__init__(); s.stack = []; s.anchors = []; s.cur = None
    def handle_starttag(s, tag, attrs):
        d = dict(attrs)
        if tag not in VOID:
            foot = tag == "footer" or "footer" in (d.get("class") or "").split() or any(c.startswith("footer") or c.endswith("footer") for c in (d.get("class") or "").split())
            s.stack.append((tag, foot))
        if tag == "a":
            s.cur = {"attrs": d, "text": "", "foot": any(f for _, f in s.stack)}
    def handle_data(s, t):
        if s.cur is not None: s.cur["text"] += t
    def handle_endtag(s, tag):
        if tag == "a" and s.cur is not None:
            s.anchors.append(s.cur); s.cur = None
        for i in range(len(s.stack) - 1, -1, -1):
            if s.stack[i][0] == tag:
                del s.stack[i:]; break

out = subprocess.run(["git", "ls-files", "*.html"], cwd=root, capture_output=True, text=True).stdout.split()
files = sorted(out) if out else sorted(os.path.relpath(os.path.join(d, f), root) for d, _, fs in os.walk(root) for f in fs if f.endswith(".html"))
fail = []
if set(files) != FIVE | OTHER:
    fail.append("page set changed: %s" % sorted(set(files) ^ (FIVE | OTHER)))
for f in files:
    p = P(); p.feed(open(os.path.join(root, f), encoding="utf-8").read())
    for key, (url, label) in U.items():
        page = [a for a in p.anchors if url.rstrip("/").split("aimprove.co.il")[1] in (a["attrs"].get("href") or "")]
        good = [a for a in page if a["attrs"].get("href") == url and a["text"].strip() == label and "target" not in a["attrs"]]
        foot = [a for a in good if a["foot"]]
        if f in FIVE:
            want_page = 1 + PREEXISTING_EXTRA.get((f, key), 0)
            if len(foot) != 1 or len(page) != want_page:
                fail.append("%s %s: footer_good=%d page_wide=%d (want 1 / %d)" % (f, key, len(foot), len(page), want_page))
        elif f in OTHER:
            want = 1 if key == "a11y" else 0
            if len(good) != want or len(page) != want:
                fail.append("%s %s: good=%d page_wide=%d (want %d)" % (f, key, len(good), len(page), want))
    if not any(x.startswith(f + " ") for x in fail): print("ok  ", f)
if fail:
    print("FAIL"); [print("  ", x) for x in fail]; sys.exit(1)
print("ALL OK (%d pages)" % len(files))
