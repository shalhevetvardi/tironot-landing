#!/usr/bin/env python3
"""בונה את hatzaa.html מתוך index.html: הדף הקיים עם שישה תיקונים ממוקדים.

גרסה קודמת של הדף, שסידרה מחדש את כל הסקשנים, נפסלה בידי שלהבת ב-24-10-2026
("הוא אפילו פחות ברור מהדף הקודם"), וקודקס הגיע לאותה מסקנה. לכן הסדר, הסיפור,
העיצוב והציטוטים נשארים כמו בדף הקיים, ומשתנים רק:
1. המסך הראשון: "תוכנית האצה של 5 שבועות", ושורת משנה קצרה בלי הבטחה מוחלטת.
2. כפתור לנועם במסך הראשון, עם שורה שאומרת שהוא סוכן AI, ו"איך זה עובד" כקישור.
3. "5 שבועות" ולא "5 מפגשים", וכמה עבודה יש בין המפגשים.
4. מועד, שעה ומקום, וההטבה במילים במקום "צפו בסרטון".
5. ההבטחות של אִימפּרוּב נשארות, ואחרי חלקן נוספה הוכחה מהדף (ר' ההערה בשלב 5 למטה).
6. "בעבודה" ולא "לעסק" בטקסט החדש.

סבב ההערות של שלהבת (24-10-2026, בדף ההערות שב-Storyteling): התיקונים שלה לטקסט נכנסו כמו שכתבה,
"זה לא עוד קורס. זו תוכנית האצה" עבר מכרטיס המחיר לכותרת "מה בדיוק קונים כאן", הליווי האנושי הודגש,
ליד המחיר דניאל מראד במקום סיגל יער, לפני הסרטונים של "שווה את הכסף?" התגובה של נועם זרז'בסקי,
ב"נעים להכיר" האינסטגרם לפני הוואטסאפ, ושני הסקשנים הלבנים שבראש הדף קיבלו רקע בהיר.
מאז שהסבב הזה עלה לאוויר, ההשוואה של חצי מול חצי נספרת מיום העלייה (funnel-report.py --ab --since).

הדף נגזר מ-index.html ולא נערך ביד, כי הציטוטים מגיעים מדשבורד ההמלצות שכותב רק
ל-index.html. ההחלטות: Storyteling, פרויקטים/חיפוש-SEO-GEO/06-אסטרטגיית-הדף-הקר.md.

הרצה: python3 scripts/build_cold_page.py
"""
import html
import json
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


# "למי זה מתאים": הכאב לפני ההצעה, במילים שתלמידים אמרו בשיחות האונבורדינג (מיפוי-קהל-ומסרים/1-אונבורדינג.md,
# חלקים ב ו-ה): "בלאגן", "טלאי על טלאי", "מיליון צ'אטים פתוחים", "הגעתי לתקרה", "לחבר את הדבר הזה למשהו אחד",
# "העבודה היא רק כשאני נמצאת", "יותר מדי מידע". שלהבת: לא משנה אם ניסו לבד או לא, הם רוצים מאוד
FIT_SECTION = """<section class="section section--white center cold-fit cold-tint" id="fit">
  <div class="container">
    <h2>למי זה <span class="accent-blue">מתאים?</span></h2>
    <p class="lead center cold-fit__lead">לבעלי עסקים, לעצמאים ולשכירים שממש רוצים <span class="nowrap">שה-AI</span> יעבוד במקומם.<br>בין אם כבר ניסיתם לבד, ובין אם עוד לא.</p>
    <div class="cold-fit__cards">
      <div class="cold-fit__card"><h3>כבר ניסיתם לבד, והגעתם לתקרה</h3><p>מיליון צ'אטים פתוחים, פרומפטים וסקילים שעובדים חצי. הכול טלאי על טלאי, ולא ברור איך מחברים את זה למשהו אחד שעובד.</p></div>
      <div class="cold-fit__card"><h3>עוד לא התחלתם, אבל ממש בא לכם</h3><p>אתם חולמים ש-AI ירוץ גם כשאתם לא שם. אבל יש כל כך הרבה מידע וכלים, שלא ברור מאיפה מתחילים, ואם בכלל תצליחו.</p></div>
    </div>
    <p class="cold-fit__pain">ובשני המקרים, הבלגן נשאר בראש שלכם, והעבודה עדיין קורית רק כשאתם נמצאים.</p>
    <p class="cold-fit__emp">וגם שכירים בונים כאן סוכנים לעבודה שלהם בארגון. בת חן, סמנכ"לית פיתוח עסקי, בנתה סוכן שמנתח דוחות רווחיות, מוצא טעויות בעצמו וחוסך משרה של אנליסט בכיר.</p>
    <p class="cold-fit__not">השיטה שלי הופכת אתכם למי שיודע לבנות פתרון AI מקצה לקצה לכל בעיה עסקית -<br>מהר, בלי לרדוף אחרי הזנב של עצמכם.</p>
  </div>
</section>"""

# "שווה את הכסף?": שני הסרטונים גלויים, ושאר העדויות נפתחות למי שרוצה לקרוא עוד
WORTH_MORE_OPEN = '<div class="cold-more" id="cold-worth-more" inert>\n      '
WORTH_MORE_CLOSE = ('</div>\n      <p class="cold-more__btn"><button type="button" class="btn btn--outline" '
                    'aria-controls="cold-worth-more" aria-expanded="false">מה עוד בוגרים אומרים על המחיר?</button></p>'
                    "<script>(function () { var b = document.querySelector('.cold-more__btn button'), m = document.getElementById('cold-worth-more');"
                    " if (!b || !m) return; b.addEventListener('click', function () { m.classList.add('is-open'); m.inert = false;"
                    " b.setAttribute('aria-expanded', 'true'); b.parentNode.hidden = true; }); })();</script>")

# ביקורת בגוגל (אותה ביקורת שברצועת "מה כתבו עלינו בגוגל"): ליד המחיר, כי יש בה זמן ותוצאה מול "5 שבועות".
# קודם היה כאן הציטוט של סיגל יער, ושלהבת החליפה אותו (24-10-2026): "גג העולם" כללי ולא מראה יכולת
ADI_QUOTE = ('<figure class="cold-quote"><img src="bogrim/images/dmarad.jpg" alt="דניאל מראד" loading="lazy">'
             '<blockquote>"אחרי ארבעה שבועות יש לי שלושה סוכנים שבניתי. '
             'לראשונה אני מרגיש שאני <span class="tm-hl">על הגל ולא רודף</span>."</blockquote>'
             '<figcaption>דניאל מראד, בעל סוכנות שיווק דיגיטלי · ביקורת בגוגל</figcaption></figure>')

# "שווה את הכסף?": לפני הסרטונים, תגובה שמדברת על הכסף עצמו (שלהבת, 24-10-2026). שמו המלא ותפקידו כתובים,
# כי באותו סקשן יש גם את נועם סוכן ה-AI
WORTH_IG = ('<figure class="cold-igshot"><img src="students/ig/ig-noam_zarzevsky.png" width="1040" height="280" loading="lazy" '
            'alt="נועם זרז\'בסקי: לדעתי מעל שנה חיפשתי לאן ללכת, המוני קורסים ומדריכים במחירים מצחיקים. כבוגר הקורס כבר אחרי שני מפגשים היה תהליך באוויר, היום יש משרד וירטואלי שלם שעובד">'
            '<figcaption>נועם זרז\'בסקי, בוגר הטירונות · תגובה באינסטגרם</figcaption></figure>')

# רצועת תגובות האינסטגרם ב"נעים להכיר" נמצאת ב-index.html עצמו (scripts/build_ig_strip.py), ולכן היא מגיעה לכאן משם


PRICE_LIST = """<ul class="price-includes">
      <li><span><strong>5 שבועות של שיעורים חיים עם שלהבת, וליווי שוטף</strong> - בתל אביב או בזום. בכל שבוע לומדים שלב חדש ובונים אותו יחד, על העבודה שלכם</span></li>
      <li><span><strong>דואגים שתגיעו מוכנים</strong> - הכנה אישית מסודרת, מקימים איתכם את סביבת העבודה ובונים את הסוכן הראשון שלכם - עוד לפני המפגש הראשון בטירונות</span></li>
      <li><span><strong>מעטפת פדגוגית שעוטפת אתכם מכל כיוון</strong> - ליווי צמוד יד ביד של שלהבת וצוות אנושי שעונה על שאלות, חומרי למידה מעמיקים, וצוות סוכני AI של אִימפּרוּב שעוזר בלמידה, בבנייה ובהטמעה</span></li>
      <li><span><strong>לא משאירים אתכם לבד בין המפגשים</strong> - מפגשי חידוד שבועיים בזום להתייעצות, שאלות ועזרה אישית</span></li>
      <li><span><strong>העבודה האמיתית קורית בין המפגשים</strong> - בשבועיים הראשונים זה לפחות כמה שעות טובות בשבוע, כי המטרה היא שכבר אז תבנו דברים אמיתיים לעבודה שלכם</span></li>
      <li><span><strong>מה שבניתם נשאר שלכם</strong> - ההקלטות, אתר חומרי הלמידה וכל מה שבניתם נשארים אצלכם, בלי הגבלת זמן</span></li>
    </ul>
    """

# סקשן הסיפור בנוי כמו סקשן המשרד בדף המפתח (הכרעת שלהבת, 24-10-2026: "כל החלק הזה הייתי
# עושה אותו כמו במפתח"). במחשב: המשרד התלת-ממדי החי ברקע של כל הסקשן, מסתובב לבד, והקישור
# "להיכנס למשרד ולשחק בו" פותח אותו על כל המסך. אם הוא לא עולה, נשארת התמונה. בטלפון: הסרטון של
# הלחיצות על סוכנים בכרטיס בראש הטקסט, כמו בדף המפתח (סצנה תלת-ממדית כבדה מדי לטלפון).
OFFICE_BG = """  <div class="cold-office" id="cold-office">
    <picture><source srcset="office-hero-desktop.webp" type="image/webp"><img src="office-hero-desktop.png" width="1920" height="1080" alt="" loading="lazy"></picture>
    <div class="cold-office__bar">
      <p class="cold-office__bar-hint"><b>זה המשרד האמיתי של שלהבת - וכזה אתם הולכים לבנות.</b>
        <span>גררו כדי לסובב · גלגלו כדי להתקרב · לחצו על כל סוכן כדי לראות למה הוא מחובר</span></p>
      <button type="button" class="cold-office__close">יציאה מהמשרד (Esc)</button>
    </div>
  </div>
  <div class="cold-office__scrim" aria-hidden="true"></div>
"""

OFFICE_ANIM = """
      <figure class="cold-office__anim">
        <video src="office-film/clicks.mp4" poster="office-film/clicks.webp" muted loop playsinline preload="metadata" aria-label="סיבוב במשרד, עם לחיצות על כמה סוכנים"></video>
        <figcaption>לוחצים על כל סוכן ורואים למה הוא מחובר: הידע, הכלים והתהליכים שהוא מריץ.</figcaption>
      </figure>"""

OFFICE_LEGEND = """
      <div class="cold-legend">
        <h3>כל קובייה במשרד היא סוכן, ואפשר לראות לאיזה ידע ויכולות היא מחוברת</h3>
        <div class="cold-legend__grid">
          <div class="cold-legend__item"><span class="cold-legend__shape cold-legend__shape--cube" aria-hidden="true"></span><span><b>קובייה</b> - סוכן. עובד עם תפקיד מוגדר, שיושב במחלקה שלו</span></div>
          <div class="cold-legend__item"><span class="cold-legend__shape cold-legend__shape--capsule" aria-hidden="true"></span><span><b>גלולה</b> - מסמך ידע. מה שהסוכן יודע על העבודה שלכם</span></div>
          <div class="cold-legend__item"><span class="cold-legend__shape cold-legend__shape--cone" aria-hidden="true"></span><span><b>חרוט</b> - סקיל. מה שהסוכן יודע לעשות</span></div>
          <div class="cold-legend__item"><span class="cold-legend__shape cold-legend__shape--ring" aria-hidden="true"></span><span><b>טבעת</b> - תהליך אוטומטי. סדר פעולות שהסוכן מריץ לבד</span></div>
        </div>
      </div>"""

OFFICE_HINT = """
      <p class="cold-office__enter"><button type="button" class="cold-office__hint">להיכנס למשרד של אִימפּרוּב ולשחק בו</button></p>
      <p class="cold-office__hint-sub">זה המשרד האמיתי של שלהבת. מסתובבים בו, לוחצים על כל סוכן ורואים מה הוא עושה ולמה הוא מחובר.</p>"""

WA_FLOAT = ('<a class="cold-wa-float" href="{wa}" target="_blank" rel="noopener noreferrer" aria-label="שאלות? לשיחה עם נועם בוואטסאפ">'
            '<span class="cold-wa-float__ic">{icon}</span><span class="cold-wa-float__txt">שאלות?</span></a>\n')

WHAT_SECTION = """<section class="section section--white center" id="what">
  <div class="container">
    <h2>זה לא עוד קורס. זו <span class="accent-blue">תוכנית האצה</span> של <span class="cold-nowrap">5 שבועות.</span></h2>
    <p class="lead center cold-what-lead">בתוכנית בונים <strong>צוות של סוכני AI שמחוברים זה לזה ועובדים יחד</strong>, כמו מחלקות במשרד. לא עוד סוכן בודד, אלא מערכת שלמה.</p>
    <p class="cold-what-example">למשל, ירדן, ד״ר לחקר המוח ויזמת, בנתה משרד וירטואלי שלם: 6 מחלקות של סוכנים שמריצות את העסק שלה מקצה לקצה.</p>
    <div class="cold-what">
      <div class="cold-what__item"><h3>שיטה, לא עוד כלי</h3><p>לומדים איך בונים מערכת: מה כל סוכן עושה, מה הוא יודע, ואיך הוא מתחבר לשאר. זה מה שנשאר איתכם גם כשהכלים מתחלפים.</p></div>
      <div class="cold-what__item"><h3>בונים סוכנים לעבודה שלכם, מהשבוע הראשון</h3><p>וכל שבוע נוסיף עוד סוכנים אמיתיים לצוות שלכם. כבר בשבועיים הראשונים יהיו לכם דברים שרצים ועושים עבודה במקומכם. ובסוף התוכנית - צוות שלם.</p></div>
      <div class="cold-what__item"><h3>לא נשארים לבד בשום שלב - ליווי עוטף, יד ביד</h3><p>את השיעורים מעבירה שלהבת בעצמה, בלייב. ולצדם: הכנה מסודרת לפני שמתחילים, מפגשי תגבור בין השיעורים, צוות אנושי שעונה על שאלות וזמין 24/7, סוכני AI של אִימפּרוּב שמלווים אתכם בכל שלבי בניית הסוכנים.</p></div>
      <div class="cold-what__item"><h3>עם מה אתם יוצאים?</h3><p>עם צוות סוכנים שבניתם בעצמכם, ואת השיטה והכלים לבנות כל סוכן, מערכת ותהליך שתצטרכו בעתיד - לבד, בלי להיתקע.</p></div>
    </div>
    <p class="cold-what-more"><a href="#price">לפרטים המלאים ולמחיר</a></p>
  </div>
</section>"""

COLD_JS = """<script id="cold-js">
(function () {
  try {
    var sec = document.querySelector('.cold-office-sec');
    var host = document.getElementById('cold-office');
    if (!sec || !host) return;
    var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* טלפון: הסרטון בכרטיס מתנגן רק כשהוא במסך */
    var vid = sec.querySelector('.cold-office__anim video');
    if (vid) {
      if (reduce) { vid.controls = true; }
      else if ('IntersectionObserver' in window) {
        new IntersectionObserver(function (es) {
          if (es[0].isIntersecting) { var p = vid.play(); if (p && p.catch) p.catch(function () {}); } else vid.pause();
        }, { threshold: 0.3 }).observe(vid);
      }
    }

    /* מחשב: המשרד החי ברקע, כמו בדף המפתח */
    if (reduce || !window.matchMedia('(min-width: 900px) and (pointer: fine)').matches) return;
    var started = false, dead = false, lastBeat = 0, f = null, watch = null, scrollY = 0;
    var hint = sec.querySelector('.cold-office__hint');
    var closeBtn = host.querySelector('.cold-office__close');
    function open() {
      if (dead || host.classList.contains('is-full')) return;
      scrollY = window.scrollY;
      host.classList.add('is-full'); sec.classList.add('is-full');
      document.body.style.overflow = 'hidden';
      if (closeBtn) closeBtn.focus();
    }
    function close() {
      if (!host.classList.contains('is-full')) return;
      host.classList.remove('is-full'); sec.classList.remove('is-full');
      document.body.style.overflow = '';
      window.scrollTo(0, scrollY);
      if (hint) hint.focus();
    }
    function fail() {
      if (dead) return; dead = true;
      if (watch) clearInterval(watch);
      close();
      if (f) f.remove();
      sec.classList.remove('is-live');
    }
    function mount() {
      if (started) return; started = true;
      f = document.createElement('iframe');
      f.src = 'https://virtualoffice.aimprove.co.il/scene-embed';
      f.title = 'המשרד הווירטואלי - סצנה תלת-ממדית';
      f.setAttribute('tabindex', '-1');
      host.appendChild(f);
      addEventListener('message', function (e) {
        if (!e.data || dead) return;
        if (e.data.type === 'vo-scene-ready') { lastBeat = Date.now(); sec.classList.add('is-live'); }
        else if (e.data.type === 'vo-scene-alive') lastBeat = Date.now();
        else if (e.data.type === 'vo-scene-failed') fail();
      });
      var t0 = Date.now();
      watch = setInterval(function () {
        if (dead) return;
        if (!lastBeat && Date.now() - t0 > 22000) return fail();
        if (lastBeat && Date.now() - lastBeat > 15000) return fail();
      }, 3000);
    }
    if (hint) hint.addEventListener('click', function (e) { e.preventDefault(); open(); });
    if (closeBtn) closeBtn.addEventListener('click', function (e) { e.preventDefault(); close(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
    function near() {
      var r = sec.getBoundingClientRect();
      return r.top < (window.innerHeight || 0) + 400 && r.bottom > -400;
    }
    if (near()) mount();
    addEventListener('scroll', function onScroll() {
      if (started) return removeEventListener('scroll', onScroll);
      if (near()) { removeEventListener('scroll', onScroll); mount(); }
    }, { passive: true });
  } catch (e) {}
})();
</script>
"""

COLD_CSS = """<style id="cold-css">
  .nav { padding-top: 18px; }
  .nav__logo { height: 14px; opacity: .9; }
  @media (max-width: 600px) { .nav__logo { height: 13px; } }
  .cold-cta { display: inline-flex; align-items: center; gap: 10px; }
  .cold-cta .wa-ic, .cold-price-cta .wa-ic { width: 22px; height: 22px; }
  .cold-noam { font-size: 14px; opacity: .9; margin: 12px 0 0; }
  .cold-first { margin: 14px 0 0; font-size: 15px; }
  .cold-first a { color: inherit; text-decoration: underline; text-underline-offset: 4px; }
  .cold-nowrap { white-space: nowrap; }
  #story h2 { text-wrap: balance; }
  .cold-office-sec { position: relative; overflow: hidden; }
  .cold-office-sec .deco { display: none; }
  .cold-office-sec > .container { position: relative; z-index: 2; }
  .cold-office { position: absolute; inset: 0; z-index: 0; }
  .cold-office picture, .cold-office img { display: block; width: 100%; height: 100%; object-fit: cover; }
  .cold-office__scrim { position: absolute; inset: 0; z-index: 1; pointer-events: none; background: rgba(20,9,59,.86); }
  .cold-office__bar, .cold-office__enter, .cold-office__hint-sub { display: none; }
  .cold-office__anim { margin: 6px 0 22px; }
  .cold-office__anim video { display: block; width: 100%; height: auto; aspect-ratio: 16 / 9; border-radius: 14px; background: #1a1450; object-fit: cover; }
  .cold-office__anim figcaption { margin-top: 8px; font-size: 14px; line-height: 1.5; color: rgba(255,255,255,.8); }
  @media (min-width: 900px) {
    .cold-office-sec { min-height: min(92vh, 900px); display: flex; align-items: center; padding-block: 80px; }
    .cold-office-sec > .container { width: 100%; }
    .cold-office-sec .story { margin: 0; max-width: 560px; }
    .cold-office-sec .story h2, .cold-office-sec .story__payoff { text-align: right; }
    .cold-office__scrim { background: linear-gradient(to left, rgba(20,9,59,.95) 0%, rgba(20,9,59,.9) 36%, rgba(20,9,59,.4) 58%, rgba(20,9,59,0) 74%); }
    .cold-office__anim { display: none; }
    .cold-office iframe { position: absolute; inset: 0; width: 100%; height: 100%; border: 0; opacity: 0; transition: opacity .5s; pointer-events: none; }
    .cold-office-sec.is-live .cold-office iframe { opacity: 1; }
    .cold-office-sec.is-live .cold-office picture { opacity: 0; }
    .cold-office-sec.is-live .cold-office__enter, .cold-office-sec.is-live .cold-office__hint-sub { display: block; }
    .cold-office__enter { margin: 26px 0 4px; }
    .cold-office__hint { font: inherit; font-size: 18px; font-weight: 700; color: var(--gold); background: none; border: 0; padding: 0;
      cursor: pointer; text-decoration: underline; text-underline-offset: 5px; white-space: nowrap; }
    .cold-office__hint:focus-visible { outline: 3px solid #fff; outline-offset: 4px; border-radius: 6px; }
    .cold-office__hint-sub { font-size: 14px; color: rgba(255,255,255,.72); margin: 0; }
    .cold-office.is-full { position: fixed; inset: 0; z-index: 9999; background: var(--navy); }
    .cold-office.is-full iframe { pointer-events: auto; }
    .cold-office.is-full .cold-office__bar { display: flex; position: absolute; z-index: 3; inset-block-start: 0; inset-inline: 0; align-items: center;
      justify-content: space-between; gap: 16px; padding: 16px 22px; background: linear-gradient(to bottom, rgba(20,9,59,.88), rgba(20,9,59,0)); }
    .cold-office__bar-hint { margin: 0; color: #fff; font-weight: 600; font-size: 16px; line-height: 1.5; }
    .cold-office__bar-hint b { color: var(--gold); }
    .cold-office__bar-hint span { display: block; font-weight: 400; color: rgba(255,255,255,.78); font-size: .92em; margin-top: 3px; }
    .cold-office__close { flex: 0 0 auto; font: inherit; font-weight: 700; font-size: 15px; color: var(--navy); background: var(--gold);
      border: 0; border-radius: 50px; padding: 10px 20px; cursor: pointer; }
  }
  .cold-wa-float { position: fixed; z-index: 800; left: max(16px, env(safe-area-inset-left, 0px)); bottom: calc(58px + env(safe-area-inset-bottom, 0px));
    display: flex; flex-direction: column; align-items: center; gap: 4px; text-decoration: none; font-family: inherit; transition: transform .15s ease; }
  .cold-wa-float:hover { transform: translateY(-2px); }
  .cold-wa-float:focus-visible { outline: 3px solid var(--gold); outline-offset: 3px; border-radius: 12px; }
  .cold-wa-float__ic { display: grid; place-items: center; width: 52px; height: 52px; border-radius: 50%; background: #25D366;
    box-shadow: 0 0 0 2px #fff, 0 10px 24px -8px rgba(20,9,59,.55); }
  .cold-wa-float__ic svg { width: 28px; height: 28px; }
  .cold-wa-float__ic svg path { fill: #fff; }
  .cold-wa-float__txt { padding: 2px 9px; border-radius: 50px; background: #fff; color: var(--navy); font-weight: 700; font-size: 13px; line-height: 1.4;
    box-shadow: 0 4px 12px -6px rgba(20,9,59,.45); }
  @media (max-width: 520px) { .cold-wa-float__ic { width: 46px; height: 46px; } .cold-wa-float__ic svg { width: 25px; height: 25px; } .cold-wa-float__txt { font-size: 12px; } }
  @media (prefers-reduced-motion: reduce) { .cold-wa-float { transition: none; } .cold-wa-float:hover { transform: none; } }
  @media print { .cold-wa-float { display: none; } }
  .cold-what-lead { max-width: 760px; margin-inline: auto; }
  .cold-what-example { max-width: 680px; margin: 10px auto 0; font-size: 16px; color: var(--navy); opacity: .85; }
  .cold-what-proof { margin: 24px auto 0; font-weight: 700; color: var(--navy); }
  .cold-brand { display: flex; flex-direction: column; gap: 8px; }
  .cold-brand__sub { color: rgba(255,255,255,.88); font-weight: 700; font-size: clamp(16px, 2vw, 20px); line-height: 1.2; }
  .cold-fit__lead { max-width: 720px; margin-inline: auto; }
  .cold-fit__cards { display: grid; gap: 14px; margin: 28px auto 0; max-width: 860px; text-align: right; }
  @media (min-width: 760px) { .cold-fit__cards { grid-template-columns: 1fr 1fr; } }
  .cold-fit__card { background: #f6f7fb; border: 1px solid rgba(20, 9, 59, .1); border-radius: 18px; padding: 18px 20px; }
  .cold-fit__card h3 { margin: 0 0 8px; font-size: 19px; line-height: 1.35; color: var(--navy); }
  .cold-fit__card p { margin: 0; line-height: 1.65; color: var(--navy); opacity: .85; }
  @media (min-width: 760px) { .cold-fit__card h3 { font-size: 21px; } .cold-fit__card p { font-size: 17px; } .cold-fit__not { font-size: 16.5px; } }
  .cold-fit__pain { max-width: 720px; margin: 26px auto 0; font-size: clamp(19px, 2.3vw, 23px); font-weight: 800; line-height: 1.45; color: var(--navy); text-wrap: balance; }
  .cold-more { max-height: 0; overflow: hidden; }
  .cold-more.is-open { max-height: none; overflow: visible; }
  .cold-more__btn { margin: 26px 0 0; text-align: center; }
  .cold-more__btn .btn { background: #fff; color: var(--navy); border: 1.5px solid rgba(20, 9, 59, .25); }
  .price-card__after { font-size: 14px; color: rgba(255,255,255,.75); margin: -6px 0 14px; position: relative; z-index: 1; }
  .cold-fit__not { max-width: 720px; margin: 22px auto 0; font-size: 15.5px; color: var(--navy); opacity: .75; }
  .cold-underline { white-space: nowrap; text-decoration: underline; text-decoration-color: var(--gold); text-decoration-thickness: 3px; text-underline-offset: 6px; }
  .price-promise { text-wrap: balance; }
  .price-card__offer { text-wrap: balance; }
  .tm-sec--inside { padding-top: 72px; }
  .cold-legend { margin: 6px 0 26px; }
  .cold-legend h3 { margin: 0 0 14px; font-size: 18px; line-height: 1.45; color: #fff; }
  .cold-legend__grid { display: grid; gap: 12px; }
  @media (min-width: 700px) { .cold-legend__grid { grid-template-columns: 1fr 1fr; } }
  .cold-legend__item { display: flex; align-items: center; gap: 12px; color: rgba(255,255,255,.85); font-size: 15px; line-height: 1.45; }
  .cold-legend__item b { color: #fff; }
  .cold-legend__shape { flex: 0 0 auto; width: 24px; height: 24px; background: var(--gold); }
  .cold-legend__shape--cube { border-radius: 5px; }
  .cold-legend__shape--ring { background: none; box-sizing: border-box; border: 4px solid var(--gold); border-radius: 50%; }
  .cold-legend__shape--cone { clip-path: polygon(50% 0, 100% 100%, 0 100%); }
  .cold-legend__shape--capsule { border-radius: 9999px; width: 14px; margin-inline: 5px; }
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
  /* שני סקשנים לבנים ברצף בראש הדף (שלהבת, 24-10-2026): "למי זה מתאים" ו"בוגרים מספרים" בגוון הבהיר של "וזה כבר קורה" */
  .cold-tint, #tm-quick { background: #EDF2F9; }
  .cold-tint .cold-fit__card { background: #fff; }
  .cold-fit__emp { max-width: 720px; margin: 22px auto 0; font-size: 16.5px; line-height: 1.6; color: var(--navy); }
  .price-card__who { font-size: 14px; color: rgba(255,255,255,.85); margin: 2px 0 10px; position: relative; z-index: 1; }
  .cold-igshot { max-width: 520px; margin: 22px auto 0; }
  .cold-igshot img { display: block; width: 100%; height: auto; border-radius: 14px; box-shadow: 0 8px 24px -12px rgba(20,9,59,.35); }
  .cold-igshot figcaption { margin-top: 8px; font-size: 14px; opacity: .75; }
</style>
"""


def build():
    global WA
    h = SRC.read_text(encoding="utf-8")
    WA = wa_link(h)

    # 1. המסך הראשון
    # בלי תוויות מעל הכותרת: יותר מדי טקסט במסך הראשון (שלהבת, 24-10-2026)
    h = once(h, '<span class="eyebrow">הופכים אתכם למי שבונה סוכני AI לבד.</span>', '', "התווית במסך הראשון")
    # "תוכנית האצה" היא תת-כותרת של השם, לא תג באותה שורה עם ההוכחות
    h = once(h, '<span class="hero__brandname">טירונות סוכנים</span></div>',
             new('<span class="cold-brand"><span class="hero__brandname">טירונות סוכנים</span>'
                 '<span class="cold-brand__sub">תוכנית האצה של 5 שבועות</span></span></div>'), "השם במסך הראשון")
    h = once(h, '<p class="hero__sub">ואת השיטה והכלים לבנות כל סוכן, מערכת ותהליך שתצטרכו - לבד, בלי להיתקע.</p>',
             new('<p class="hero__sub">תקבלו שיטה לבנות סוכני AI שמחוברים זה לזה ועובדים יחד.<br>והכל עם ליווי צמוד ובלי לדעת לתכנת.</p>'),
             "שורת המשנה")
    h = once(h, '<p class="hero-office__cap">זה משרד ה-AI שמריץ את אימפרוב בלי עובדים. כזה תבנו גם אתם.</p>',
             new('<p class="hero-office__cap">זה משרד ה-AI שמריץ את אימפרוב.<br>כזה תבנו גם אתם.</p>'), "הכיתוב מתחת למשרד")
    # 2. הכפתור לנועם, ו"איך זה עובד" כקישור
    h = once(h, '<a href="#intro" class="btn btn--gold">איך זה עובד</a>',
             noam_button("btn--gold cold-cta", "לשיחה עם נועם בוואטסאפ") +
             new('\n      <p class="cold-noam">נועם הוא סוכן ה-AI של אִימפּרוּב בוואטסאפ.</p>'
                 '\n      <p class="cold-first"><a href="#fit">אני רוצה להבין על מה מדובר קודם</a></p>'),
             "הכפתור במסך הראשון")

    # הסיפור ליד המשרד, וסקשן "מה בדיוק קונים כאן" אחריו
    h = once(h, '      <h2>תארו לכם שמישהו לוקח אתכם ביד ועוזר לכם לבנות את <span class="accent-gold">משרד ה-AI שלכם.</span></h2>',
             '      <h2>תארו לכם שמישהו לוקח אתכם ביד ועוזר לכם לבנות את <span class="accent-gold cold-nowrap">משרד ה-AI שלכם.</span></h2>',
             "כותרת הסיפור")
    opener = '<section class="section section--navy" id="story">'
    i = h.find(opener)
    j = h.find('</section>', i) + len('</section>')
    story = h[i:j]
    story = once(story, opener, '<section class="section section--navy cold-office-sec" id="story">\n' + OFFICE_BG, "פתיחת הסיפור")
    story = once(story, '<span class="accent-gold cold-nowrap">משרד ה-AI שלכם.</span></h2>',
                 '<span class="accent-gold cold-nowrap">משרד ה-AI שלכם.</span></h2>' + new(OFFICE_ANIM), "הסרטון בטלפון")
    k = story.find('<p class="story__payoff">')
    story = story[:k] + new(OFFICE_LEGEND).strip() + "\n      " + story[k:]
    k = story.find('</p>', story.find('<p class="story__payoff">')) + len('</p>')
    story = story[:k] + new(OFFICE_HINT) + story[k:]
    h = h[:i] + story + h[j:]

    # אחרי המסך הראשון: קודם "למי זה מתאים" (הכאב), ואז "מה בדיוק קונים כאן" (ההצעה)
    hero_end = h.find('</section>', h.find('<section class="hero">')) + len('</section>')
    h = h[:hero_end] + "\n\n" + new(FIT_SECTION) + "\n\n" + new(WHAT_SECTION) + h[hero_end:]


    # "שווה את הכסף?": מה שאחרי שני הסרטונים נפתח רק למי שרוצה לקרוא עוד
    s = h.find('<div class="tm-worth" id="tm-worth">')
    sec_end = h.find('</section>', s)
    a = h.find('<div class="tm-shots">', s)
    z = h.rfind('\n    </div>\n  </div>\n', s, sec_end)
    if s < 0 or not (s < a < z < sec_end):
        raise BuildError("המבנה של 'שווה את הכסף?' השתנה, צריך לעדכן את הסקריפט")
    h = h[:a] + WORTH_MORE_OPEN + h[a:z] + "\n      " + new(WORTH_MORE_CLOSE) + h[z:]
    h = once(h, '<p class="tm-lead">הבוגרים עונים על זה בעצמם.</p>',
             '<p class="tm-lead">הבוגרים עונים על זה בעצמם.</p>\n      ' + WORTH_IG, "התגובה לפני הסרטונים")

    # "נעים להכיר": קודם התגובות מאינסטגרם, קצרות ופומביות, ואחריהן הודעות הוואטסאפ (שלהבת, 24-10-2026)
    a = h.index('<!-- ig-strip -->')
    z = h.index('<!-- /ig-strip -->') + len('<!-- /ig-strip -->')
    ig = once(h[a:z], '<p class="tm-strip-cap">ומה בוגרים כותבים עליי באינסטגרם</p>',
              new('<p class="tm-strip-cap">מה בוגרים כתבו באינסטגרם</p>'), "הכותרת של רצועת האינסטגרם")
    h = h[:a] + h[z:]
    wa_cap = '<p class="tm-strip-cap">ככה תלמידים מרגישים בטירונות</p>'
    h = once(h, wa_cap, ig + "\n    " + wa_cap, "הסדר ב'נעים להכיר'")

    # 5. ההבטחות נשארות כמו בדף הקיים, ואחריהן הוכחה מהדף עצמו (שלהבת, 24-10-2026: "זה נכון... לתת את ההבטחה,
    #    ואחרי זה להמשיך את המשפט עם משהו שמוכיח את זה"). קודם רוככו לפי המלצה של קודקס, והיא לא הסכימה.
    #    משפט שההוכחה שלו כבר באה מיד אחריו בדף (הכרטיס של רון, הרשימה של הליווי, הציטוטים) לא משתנה.
    h = once(h, 'את השיטה השלמה - לבנות כל סוכן, כל תהליך, כל דבר שרץ אוטומטית. כל מה שתצטרכו, גם בעוד שנה, גם משהו שעוד לא קיים.',
             new('את השיטה השלמה - לבנות כל סוכן, כל תהליך, כל דבר שרץ אוטומטית. כל מה שתצטרכו, גם בעוד שנה, גם משהו שעוד לא קיים. '
                 'ככה בנו הבוגרים דברים מכל תחום: חנות אינטרנטית שרצה מקצה לקצה, סוכן שמנתח מכרזים בתוך דקות, עוזר משפטי למשרד עורכי דין.'),
             "הפסקה על השיטה")
    h = once(h, 'קשה לא להצליח כאן. כל המעטפת בנויה כדי שלא תיתקעו לבד באף רגע. ומדד ההצלחה שלנו פשוט: שתדעו לבנות מה שתרצו.',
             new('קשה לא להצליח כאן. כל המעטפת בנויה כדי שלא תיתקעו לבד באף רגע, ומי שעושה את העבודה בין המפגשים בונה כבר בשבועיים הראשונים '
                 'דברים אמיתיים לעבודה שלו. ומדד ההצלחה שלנו פשוט: שתדעו לבנות מה שתרצו.'),
             "התשובה על 'אצליח לבנות'")
    h = once(h, 'נועם יודע הכל על הטירונות - בודק התאמה, עונה על כל שאלה, ופותח לכם את הדרך פנימה.',
             new('נועם יודע הכל על הטירונות - בודק התאמה, עונה על כל שאלה, ופותח לכם את הדרך פנימה. '
                 'ותוך כדי השיחה תראו בעצמכם מה אפשר לבנות בשיטה הזאת.'), "נועם בסוף הדף")
    # המשפט הזה תוקן בעובדה ולא בסגנון: על בת חן כתוב מיד אחריו "ומאז? עוד צוות סוכנים", כלומר חלק נבנה אחרי הטירונות
    h = once(h, 'וכל מה שתקראו כאן - נבנה תוך כדי הטירונות, כבר בשבועות הראשונים.',
             new('וכל אחד מהם התחיל לבנות את זה בטירונות, כבר בשבועות הראשונים.'), "התשובה על המחיר")
    h = once(h, 'היא תעבוד לכם בכל גרסה של קלוד, ובכל כלי חדש שיבוא אחריו.',
             new('היא תעבוד לכם בכל גרסה של קלוד, ובכל כלי חדש שיבוא אחריו. ככה זה אצל הבוגרים:'), "התשובה על שינויים ב-AI")
    h = once(h, 'לא תישארו לבד לרגע. הטירונות נבנתה עם מעטפת ליווי שלא תמצאו בשום מקום אחר.',
             new('לא תישארו לבד לרגע. הטירונות נבנתה עם מעטפת ליווי שלא תמצאו בשום מקום אחר. ככה זה נראה בפועל:'), "התשובה על הליווי")
    h = once(h, '<p><strong>ואחריה גם לכם יהיה הקסם הזה בידיים</strong> - היכולת לבנות כל דבר שרק תחלמו עליו: כל סוכן, כל מערכת, כל כלי.</p>',
             new('<p><strong>ואחריה גם לכם יהיה הקסם הזה בידיים</strong> - היכולת לבנות כל דבר שרק תחלמו עליו: כל סוכן, כל מערכת, כל כלי. '
                 'כמו רון, שבנה צוות סוכנים שמנהל לו סטארטאפ שלם.</p>'),
             "הפסקה על הקסם")

    # 3 + 4. סקשן המחיר: 5 שבועות, העבודה בין המפגשים, מועד ומקום, וההטבה במילים
    i = h.find('<h2 class="price-promise">')
    old_h2 = h[i:h.find('</h2>', i) + 5]
    h = once(h, old_h2, new(
        '<h2 class="price-promise">'
        '5 שבועות שבהם בונים <span class="accent-blue">צוות סוכני AI שעובד בשבילכם</span>, ויוצאים עם שיטה לבנות לבד את מה שתצטרכו אחר כך.</h2>'),
        "כותרת המחיר")
    i = h.find('<ul class="price-includes">')
    old_list = h[i:h.find('</ul>', i) + 5]
    h = once(h, old_list, new(PRICE_LIST) + ADI_QUOTE, "רשימת מה כלול")
    h = once(h, '<div class="price-card__offer">רוצים הטבה של <span class="nowrap">1,400&nbsp;₪</span>?</div>',
             new('<div class="price-card__offer">הטבה של <span class="nowrap">1,400&nbsp;₪</span> <span class="nowrap">ניתנת בשיחה עם נועם</span></div>'
                 '\n      <p class="price-card__who">נועם הוא סוכן ה-AI של אִימפּרוּב בוואטסאפ.</p>'
                 '\n      <p class="price-card__after">כלומר <span class="nowrap">7,900&nbsp;₪</span> אחרי ההטבה</p>'),
             "ההטבה")
    h = once(h, '<a href="#video-noam" class="price-card__cta">צפו בסרטון למטה</a>',
             noam_button("btn--gold cold-price-cta", "לשיחה עם נועם"), "הכפתור בכרטיס המחיר")
    # 3. הלשונית בשאלות
    h = once(h, 'aria-selected="false" tabindex="-1">למה רק 5 מפגשים?</button>',
             new('aria-selected="false" tabindex="-1">רק 5 שבועות?</button>'), "הלשונית של 5 המפגשים")
    h = once(h, 'איך 5 מפגשים מספיקים כדי ללמוד את כל זה?', new('איך 5 שבועות מספיקים כדי ללמוד את כל זה?'),
             "השאלה של 5 המפגשים")

    # חצי מול חצי: index.html מעביר לכאן את מי שהוגרל ל-b. כאן אסור להעביר שוב (לולאה), ורק נשמרת הגרסה
    # למי שהגיע ישר לדף הזה, כדי שבביקור הבא בדף הראשי יגיע שוב לכאן
    a = h.index('<!-- ab-split -->')
    z = h.index('<!-- /ab-split -->') + len('<!-- /ab-split -->')
    h = h[:a] + ('<!-- ab-split -->\n<script>\n/* חצי מול חצי: הגרסה b. ההגרלה וההסבר ב-index.html. */\n'
                 "(function () { try { var v = localStorage.getItem('aim_ab'); if (v !== 'a' && v !== 'b') localStorage.setItem('aim_ab', 'b'); } catch (e) {} })();\n"
                 '</script>\n<!-- /ab-split -->') + h[z:]

    # הדף עצמו: לא באינדקס, ונמדד בנפרד מהדף הקיים
    h = once(h, "<title>טירונות סוכנים - בונים צוות AI שעובד בשבילכם</title>",
             "<title>טירונות סוכנים - תוכנית האצה של 5 שבועות</title>\n"
             '<meta name="robots" content="noindex, nofollow">', "כותרת הדף")
    h = once(h, "</head>", COLD_CSS + "</head>", "העיצוב של התוספות")
    h = once(h, "</body>", WA_FLOAT.format(wa=WA, icon=WA_ICON) + COLD_JS + "</body>", "הכפתור הצף והסקריפט")
    h = once(h, "var PAGE = 'index';", "var PAGE = 'hatzaa';", "שם הדף במדידה")

    for bad in ("—", "–", "→"):
        if any(bad in s for s in NEW_COPY + [COLD_CSS, ADI_QUOTE, WORTH_IG, OFFICE_BG, COLD_JS, WA_FLOAT, OFFICE_LEGEND]):
            raise BuildError(f"בטקסט החדש יש את התו האסור {bad!r}")
    OUT.write_text(h, encoding="utf-8")
    print(f"נכתב {OUT.name}: {len(h):,} תווים, {h.count('<section')} סקשנים")


if __name__ == "__main__":
    try:
        build()
    except BuildError as e:
        print(f"הבנייה נעצרה: {e}", file=sys.stderr)
        sys.exit(1)
