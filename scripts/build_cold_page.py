#!/usr/bin/env python3
"""בונה את hatzaa.html מתוך index.html: הדף הקיים עם שישה תיקונים ממוקדים.

גרסה קודמת של הדף, שסידרה מחדש את כל הסקשנים, נפסלה בידי שלהבת ב-24-10-2026
("הוא אפילו פחות ברור מהדף הקודם"), וקודקס הגיע לאותה מסקנה. לכן הסדר, הסיפור,
העיצוב והציטוטים נשארים כמו בדף הקיים, ומשתנים רק:
1. המסך הראשון: "תוכנית האצה של 5 שבועות", ושורת משנה קצרה בלי הבטחה מוחלטת.
2. כפתור לנועם במסך הראשון, עם שורה שאומרת שהוא סוכן AI, ו"איך זה עובד" כקישור.
3. "5 שבועות" ולא "5 מפגשים", וכמה עבודה יש בין המפגשים.
4. מועד, שעה ומקום, וההטבה במילים במקום "צפו בסרטון".
5. בלי הבטחות מוחלטות מטעם אִימפּרוּב ("כל סוכן", "לתמיד"). בציטוטים של בוגרים לא נוגעים.
6. "בעבודה" ולא "לעסק" בטקסט החדש.

הדף נגזר מ-index.html ולא נערך ביד, כי הציטוטים מגיעים מדשבורד ההמלצות שכותב רק
ל-index.html. ההחלטות: Storyteling, פרויקטים/חיפוש-SEO-GEO/06-אסטרטגיית-הדף-הקר.md.

הרצה: python3 scripts/build_cold_page.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "index.html"
OUT = ROOT / "hatzaa.html"

WA = None  # נלקח מהדף, כדי שהכפתורים החדשים יזוהו במדידה כמו שאר הכפתורים לנועם


class BuildError(Exception):
    pass


def once(text, old, new_text, label):
    n = text.count(old)
    if n != 1:
        raise BuildError(f"{label}: נמצאו {n} מופעים במקום 1. הדף המקורי השתנה, צריך לעדכן את הסקריפט")
    return text.replace(old, new_text)


def wa_link(html):
    m = re.search(r'href="(https://wa\.me/972559397247\?text=[^"]+)"', html)
    if not m:
        raise BuildError("הקישור לנועם לא נמצא")
    return m.group(1)


WA_ICON = ('<svg class="wa-ic" viewBox="0 0 24 24" fill="#25D366" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>')


def noam_button(cls, label):
    return (f'<a href="{WA}" class="btn {cls}" target="_blank" rel="noopener noreferrer">'
            f'{WA_ICON}<span>{label}</span></a>')


NEW_COPY = []  # כל טקסט חדש נאסף כאן, ונבדק בסוף לתווים אסורים


def new(s):
    NEW_COPY.append(s)
    return s


ADI_QUOTE = ('<figure class="cold-quote"><img src="bogrim/images/adidotan1.jpg" alt="עדי דותן" loading="lazy">'
             '<blockquote>"צריך להבין שיש פה השקעה, בטח בשבועיים הראשונים, לא מבוטלת. [...] '
             '<span class="tm-hl">אחרי שבועיים הצלחתי כבר לראות פירות.</span>"</blockquote>'
             '<figcaption>עדי דותן · שכירה בהייטק</figcaption></figure>')

PRICE_LIST = """<ul class="price-includes">
      <li><span><strong>5 שבועות, מפגש לייב אחד בכל שבוע</strong> - בימי רביעי, 18:30-21:30, בתל אביב או בזום. בכל מפגש לומדים ובונים יחד</span></li>
      <li><span><strong>דואגים שתגיעו מוכנים</strong> - הכנה אישית מסודרת, מקימים איתכם את סביבת העבודה ובונים את הסוכן הראשון שלכם - עוד לפני המפגש הראשון בטירונות</span></li>
      <li><span><strong>מעטפת פדגוגית שעוטפת אתכם מכל כיוון</strong> - ליווי צמוד יד ביד, חומרי למידה מעמיקים, וצוות סוכני AI של אִימפּרוּב שעוזר בלמידה, בבנייה ובהטמעה</span></li>
      <li><span><strong>לא משאירים אתכם לבד בין המפגשים</strong> - מפגשי חידוד שבועיים בזום להתייעצות, שאלות ועזרה אישית</span></li>
      <li><span><strong>העבודה האמיתית קורית בין המפגשים</strong> - בשבועיים הראשונים זה לפחות כמה שעות טובות בשבוע, כי המטרה היא שכבר אז תבנו דברים אמיתיים לעבודה שלכם</span></li>
      <li><span><strong>מה שבניתם נשאר שלכם</strong> - ההקלטות, אתר חומרי הלמידה וכל מה שבניתם נשארים אצלכם, בלי הגבלת זמן</span></li>
    </ul>
    """

# הסיפור על רקע סרטון של המשרד, על כל רוחב הסקשן (הכרעת שלהבת, 24-10-2026: "לא בתוך ריבוע",
# והטקסט על שכבה כהה). הסרטונים מתיקיית "אימפרוב - נכסי המשרד לסושיאל", בגרסה קלה ב-office-film/:
# לרוחב במחשב, לאורך בטלפון. שני קטעים ברצף: סיבוב על כל המשרד, ואז לחיצה על נועם.
STORY_FILM = """  <div class="cold-film" aria-hidden="true">
    <video class="cold-film__video" muted playsinline preload="none" poster="office-film/office-wide.webp"></video>
    <p class="cold-film__cap"></p>
  </div>
"""

WHAT_SECTION = """<section class="section section--white center" id="what">
  <div class="container">
    <h2>מה בדיוק <span class="accent-blue">קונים כאן?</span></h2>
    <p class="lead center cold-what-lead">תוכנית האצה של 5 שבועות, שבה אתם לומדים לבנות בעצמכם סוכני AI, ובונים אותם תוך כדי על העבודה שלכם.</p>
    <div class="cold-what">
      <div class="cold-what__item"><h3>5 מפגשי לייב עם שלהבת</h3><p>פעם בשבוע, 3 שעות, בתל אביב או בזום. בכל מפגש לומדים שלב ובונים אותו יחד.</p></div>
      <div class="cold-what__item"><h3>הכנה לפני שמתחילים</h3><p>מקימים איתכם את סביבת העבודה, ובונים את הסוכן הראשון עוד לפני המפגש הראשון.</p></div>
      <div class="cold-what__item"><h3>ליווי בין המפגשים</h3><p>מפגשי חידוד שבועיים בזום, צוות שעוזר כשנתקעים, וסוכני AI של אִימפּרוּב שמלווים את הבנייה.</p></div>
      <div class="cold-what__item"><h3>מה יוצאים איתו</h3><p>סוכנים ותהליכים שכבר עובדים בשבילכם, והשיטה לבנות לבד את הבאים.</p></div>
    </div>
    <p class="cold-what-more"><a href="#price">לפרטים המלאים ולמחיר</a></p>
  </div>
</section>"""

COLD_JS = """<script id="cold-js">
(function () {
  try {
    var sec = document.querySelector('.cold-film-sec');
    var video = sec && sec.querySelector('.cold-film__video');
    var cap = sec && sec.querySelector('.cold-film__cap');
    if (!video) return;
    var tall = window.matchMedia && window.matchMedia('(max-width: 899px)').matches;
    var kind = tall ? 'tall' : 'wide';
    var clips = [
      { src: 'office-film/office-' + kind + '.mp4', cap: 'זה המשרד שמריץ את אִימפּרוּב. כל קובייה בו היא סוכן AI שעושה עבודה.' },
      { src: 'office-film/noam-' + kind + '.mp4', cap: 'לוחצים על נועם, סוכן המכירות, ורואים למה הוא מחובר: הידע, הכלים והתהליכים שהוא מריץ.' }
    ];
    video.poster = 'office-film/office-' + kind + '.webp';
    cap.textContent = clips[0].cap;
    var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduce) return;
    var n = 0, loaded = false;
    function show(k) {
      n = k % clips.length;
      video.src = clips[n].src;
      cap.textContent = clips[n].cap;
      var p = video.play(); if (p && p.catch) p.catch(function () {});
    }
    video.addEventListener('ended', function () { show(n + 1); });
    function onView(inView) {
      if (inView) { if (!loaded) { loaded = true; show(0); } else { var p = video.play(); if (p && p.catch) p.catch(function () {}); } }
      else if (loaded) video.pause();
    }
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (es) { onView(es[0].isIntersecting); }, { threshold: 0.15 }).observe(sec);
    } else { onView(true); }
  } catch (e) {}
})();
</script>
"""

COLD_CSS = """<style id="cold-css">
  .nav { padding-top: 18px; }
  .nav__logo { height: 18px; opacity: .92; }
  @media (max-width: 600px) { .nav__logo { height: 16px; } }
  .cold-cta { display: inline-flex; align-items: center; gap: 10px; }
  .cold-cta .wa-ic, .cold-price-cta .wa-ic { width: 22px; height: 22px; }
  .cold-noam { font-size: 14px; opacity: .9; margin: 12px 0 0; }
  .cold-first { margin: 14px 0 0; font-size: 15px; }
  .cold-first a { color: inherit; text-decoration: underline; text-underline-offset: 4px; }
  .cold-nowrap { white-space: nowrap; }
  #story h2 { text-wrap: balance; }
  .cold-film-sec { position: relative; overflow: hidden; isolation: isolate; }
  .cold-film-sec .deco { display: none; }
  .cold-film__video { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
  .cold-film__cap { position: absolute; z-index: 1; inset-inline: 16px; bottom: 18px; margin: 0 auto; max-width: 560px; text-align: center;
    font-size: 14px; line-height: 1.5; color: #fff; background: rgba(20,9,59,.55); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
    border: 1px solid rgba(255,255,255,.22); border-radius: 14px; padding: 8px 14px; }
  /* טלפון: הטקסט על הרקע הכהה, והסרטון מתחתיו ברוחב מלא, בלי מסגרת, עם מעבר רך מהכהה */
  @media (max-width: 899px) {
    .cold-film-sec { display: flex; flex-direction: column; padding-bottom: 0; }
    .cold-film { position: relative; order: 2; width: 100%; aspect-ratio: 9 / 16; max-height: 88vh; margin-top: 28px; }
    .cold-film::after { content: ""; position: absolute; inset: 0; pointer-events: none;
      background: linear-gradient(to bottom, rgba(20,9,59,1) 0%, rgba(20,9,59,0) 22%); }
  }
  /* מחשב: הסרטון על כל הסקשן, והטקסט בצד ימין על שכבה כהה שנפתחת לסרטון בצד שמאל */
  @media (min-width: 900px) {
    .cold-film { position: absolute; inset: 0; z-index: -1; }
    .cold-film::after { content: ""; position: absolute; inset: 0; pointer-events: none;
      background: linear-gradient(to left, rgba(20,9,59,.94) 0%, rgba(20,9,59,.88) 38%, rgba(20,9,59,.35) 58%, rgba(20,9,59,0) 72%); }
    .cold-film-sec { padding-bottom: 96px; min-height: 640px; }
    .cold-film-sec .story { margin: 0; margin-inline-start: max(24px, calc((100% - var(--maxw)) / 2)); max-width: 560px; }
    .cold-film-sec .story h2, .cold-film-sec .story__payoff { text-align: right; }
    .cold-film__cap { inset-inline-start: auto; inset-inline-end: 4%; width: 34%; max-width: 440px; bottom: 28px; }
  }
  .cold-what-lead { max-width: 720px; margin-inline: auto; }
  .cold-what { display: grid; gap: 14px; max-width: 980px; margin: 28px auto 0; text-align: right; }
  @media (min-width: 760px) { .cold-what { grid-template-columns: 1fr 1fr; } }
  .cold-what__item { background: #fff; border: 1px solid rgba(20, 9, 59, .14); border-radius: 18px; padding: 20px 22px; }
  .cold-what__item h3 { margin: 0 0 6px; font-size: 19px; color: var(--navy); }
  .cold-what__item p { margin: 0; line-height: 1.65; }
  .cold-what-more { margin-top: 22px; }
  .cold-what-more a { color: var(--blue); font-weight: 700; text-decoration: underline; text-underline-offset: 4px; }
  .cold-price-cta { display: inline-flex; align-items: center; gap: 10px; margin-top: 12px; }
  .cold-quote { display: grid; grid-template-columns: 52px 1fr; gap: 4px 12px; align-items: start; max-width: 640px; margin: 8px auto 28px; text-align: right; background: #f6f7fb; border: 1px solid rgba(20, 9, 59, .1); border-radius: 18px; padding: 16px; }
  .cold-quote img { width: 52px; height: 52px; border-radius: 50%; object-fit: cover; grid-row: span 2; }
  .cold-quote blockquote { margin: 0; line-height: 1.6; }
  .cold-quote figcaption { font-size: 14px; opacity: .75; }
</style>
"""


def build():
    global WA
    h = SRC.read_text(encoding="utf-8")
    WA = wa_link(h)

    # 1. המסך הראשון
    h = once(h, '<span class="eyebrow">הופכים אתכם למי שבונה סוכני AI לבד.</span>',
             new('<span class="eyebrow">תוכנית האצה של 5 שבועות</span>'), "התווית במסך הראשון")
    h = once(h, '<p class="hero__sub">ואת השיטה והכלים לבנות כל סוכן, מערכת ותהליך שתצטרכו - לבד, בלי להיתקע.</p>',
             new('<p class="hero__sub">לומדים לבנות בעצמכם סוכנים שעושים עבודה אמיתית, עם ליווי צמוד ובלי לדעת לתכנת.</p>'),
             "שורת המשנה")
    # 2. הכפתור לנועם, ו"איך זה עובד" כקישור
    h = once(h, '<a href="#intro" class="btn btn--gold">איך זה עובד</a>',
             noam_button("btn--gold cold-cta", "לשיחה עם נועם בוואטסאפ") +
             new('\n      <p class="cold-noam">נועם הוא סוכן ה-AI של אִימפּרוּב בוואטסאפ.</p>'
                 '\n      <p class="cold-first"><a href="#what">אני רוצה להבין על מה מדובר קודם</a></p>'),
             "הכפתור במסך הראשון")

    # הסיפור ליד המשרד, וסקשן "מה בדיוק קונים כאן" אחריו
    h = once(h, '      <h2>תארו לכם שמישהו לוקח אתכם ביד ועוזר לכם לבנות את <span class="accent-gold">משרד ה-AI שלכם.</span></h2>',
             '      <h2>תארו לכם שמישהו לוקח אתכם ביד ועוזר לכם לבנות את <span class="accent-gold cold-nowrap">משרד ה-AI שלכם.</span></h2>',
             "כותרת הסיפור")
    opener = '<section class="section section--navy" id="story">'
    i = h.find(opener)
    j = h.find('</section>', i) + len('</section>')
    story = h[i:j]
    story = once(story, opener, '<section class="section section--navy cold-film-sec" id="story">\n' + new(STORY_FILM),
                 "פתיחת הסיפור")
    h = h[:i] + story + "\n\n" + new(WHAT_SECTION) + h[j:]

    # 5. בלי הבטחות מוחלטות בטקסט של אִימפּרוּב
    h = once(h, 'את השיטה השלמה - לבנות כל סוכן, כל תהליך, כל דבר שרץ אוטומטית. כל מה שתצטרכו, גם בעוד שנה, גם משהו שעוד לא קיים.',
             new('את השיטה שלפיה בונים סוכנים ותהליכים שרצים לבד, והיא ממשיכה לעבוד גם כשהכלים משתנים.'),
             "הפסקה על השיטה")
    h = once(h, '<p class="story__payoff">ופתאום אתם שוב האדם שיודע.<br>שלא תקוע, שלא תלוי באף אחד - שיכול לבנות לעצמו כל דבר.</p>',
             new('<p class="story__payoff">ופתאום אתם שוב האדם שיודע.<br>שלא תקוע ולא תלוי באף אחד, ויודע לבנות לעצמו את מה שהוא צריך.</p>'),
             "סוף הסיפור")
    h = once(h, '<p class="tm-answer__lead">קשה לא להצליח כאן. כל המעטפת בנויה כדי שלא תיתקעו לבד באף רגע. ומדד ההצלחה שלנו פשוט: שתדעו לבנות מה שתרצו.</p>',
             new('<p class="tm-answer__lead">כל המעטפת בנויה כדי שלא תיתקעו לבד באף רגע. מי שעושה את העבודה בין המפגשים, בונה כבר בשבועיים הראשונים דברים אמיתיים לעבודה שלו.</p>'),
             "התשובה על 'אצליח לבנות'")
    h = once(h, 'כי יש לי שיטה שמאפשרת לבנות כל דבר, גם מה שמעולם לא בניתי.',
             new('כי יש לי שיטה שמאפשרת לבנות גם דברים שמעולם לא בניתי.'), "השיטה של שלהבת")
    h = once(h, '<p><strong>ואחריה גם לכם יהיה הקסם הזה בידיים</strong> - היכולת לבנות כל דבר שרק תחלמו עליו: כל סוכן, כל מערכת, כל כלי.</p>',
             new('<p><strong>ואחריה גם אתם תדעו לבנות</strong> את מה שהעבודה שלכם צריכה, גם דברים שעוד לא בניתם אף פעם.</p>'),
             "הפסקה על הקסם")

    # 3 + 4. סקשן המחיר: 5 שבועות, העבודה בין המפגשים, מועד ומקום, וההטבה במילים
    i = h.find('<h2 class="price-promise">')
    old_h2 = h[i:h.find('</h2>', i) + 5]
    h = once(h, old_h2, new(
        '<h2 class="price-promise"><span class="price-promise__kicker">זה לא עוד קורס. זו תוכנית האצה של 5 שבועות.</span>'
        '5 שבועות שבהם אתם לומדים את כל מה שצריך <span class="accent-blue">כדי לבנות את מה שאתם רוצים</span>, ובונים כבר תוך כדי.</h2>'),
        "כותרת המחיר")
    i = h.find('<ul class="price-includes">')
    old_list = h[i:h.find('</ul>', i) + 5]
    h = once(h, old_list, new(PRICE_LIST) + ADI_QUOTE, "רשימת מה כלול")
    h = once(h, '<div class="price-card__offer">רוצים הטבה של <span class="nowrap">1,400&nbsp;₪</span>?</div>',
             new('<div class="price-card__offer">הטבה של <span class="nowrap">1,400&nbsp;₪</span> ניתנת בשיחה עם נועם</div>'),
             "ההטבה")
    h = once(h, '<a href="#video-noam" class="price-card__cta">צפו בסרטון למטה</a>',
             noam_button("btn--gold cold-price-cta", "לשיחה עם נועם"), "הכפתור בכרטיס המחיר")
    # 3. הלשונית בשאלות
    h = once(h, 'aria-selected="false" tabindex="-1">למה רק 5 מפגשים?</button>',
             new('aria-selected="false" tabindex="-1">רק 5 שבועות?</button>'), "הלשונית של 5 המפגשים")
    h = once(h, 'איך 5 מפגשים מספיקים כדי ללמוד את כל זה?', new('איך 5 שבועות מספיקים כדי ללמוד את כל זה?'),
             "השאלה של 5 המפגשים")

    # הדף עצמו: לא באינדקס, ונמדד בנפרד מהדף הקיים
    h = once(h, "<title>טירונות סוכנים - בונים צוות AI שעובד בשבילכם</title>",
             "<title>טירונות סוכנים - תוכנית האצה של 5 שבועות</title>\n"
             '<meta name="robots" content="noindex, nofollow">', "כותרת הדף")
    h = once(h, "</head>", COLD_CSS + "</head>", "העיצוב של התוספות")
    h = once(h, "</body>", COLD_JS + "</body>", "הסקריפט של המשרד ליד הסיפור")
    h = once(h, "var PAGE = 'index';", "var PAGE = 'hatzaa';", "שם הדף במדידה")

    for bad in ("—", "–", "→"):
        if any(bad in s for s in NEW_COPY + [COLD_CSS, ADI_QUOTE, STORY_FILM, COLD_JS]):
            raise BuildError(f"בטקסט החדש יש את התו האסור {bad!r}")
    OUT.write_text(h, encoding="utf-8")
    print(f"נכתב {OUT.name}: {len(h):,} תווים, {h.count('<section')} סקשנים")


if __name__ == "__main__":
    try:
        build()
    except BuildError as e:
        print(f"הבנייה נעצרה: {e}", file=sys.stderr)
        sys.exit(1)
