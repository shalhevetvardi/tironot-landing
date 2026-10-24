#!/usr/bin/env python3
"""בונה את hatzaa.html, הגרסה לקהל קר של דף הטירונות, מתוך index.html.

הגרסה נגזרת מהדף הקיים ולא נערכת ביד: הציטוטים בדף מגיעים מדשבורד ההמלצות,
שכותב רק ל-index.html, ועותק שנערך ביד היה מפגר אחריו. כל שינוי ב-index.html
נכנס לגרסה בהרצה חוזרת של הסקריפט.

ההחלטות שמאחורי הגרסה: Storyteling, פרויקטים/חיפוש-SEO-GEO/06-אסטרטגיית-הדף-הקר.md.

הרצה: python3 scripts/build_cold_page.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "index.html"
OUT = ROOT / "hatzaa.html"

SECTION_OPENERS = {
    "hero": '<section class="hero">',
    "quick": '<section class="tm-sec tm-sec--quick center" id="tm-quick">',
    "intro": '<section class="section section--white center" id="intro">',
    "story": '<section class="section section--navy" id="story">',
    "proofs": '<section class="section section--white section--proofs center">',
    "google": '<section class="tm-sec tm-sec--google center" id="tm-google">',
    "roadmap": '<section class="section section--roadmap center">',
    "inside": '<section class="tm-sec tm-sec--inside center" id="tm-inside">',
    "price": '<section class="section section--white center" id="price">',
    "video": '<section class="section section--blue center" id="video-noam">',
    "final": '<section class="section section--gold center final">',
    "doubts": '<section class="tm-sec tm-sec--doubts center" id="tm-doubts">',
}

# הסדר לקורא קר. story ו-quick לא נכנסים: סיפור הכאב הארוך והרצועה העליונה
# כתובים למי שכבר מכיר את שלהבת, והתוצרים של הבוגרים עולים במקומם.
ORDER = ["hero", "proofs", "fit", "map", "doubts", "intro", "inside", "price", "google", "video", "final"]

WA = None  # נלקח מהדף, כדי שהכפתור החדש יזוהה כמו שאר הכפתורים לנועם


class BuildError(Exception):
    pass


def once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        raise BuildError(f"{label}: נמצאו {n} מופעים במקום 1. הדף המקורי השתנה, צריך לעדכן את הסקריפט")
    return text.replace(old, new)


def cut_sections(html):
    sections = {}
    for name, opener in SECTION_OPENERS.items():
        start = html.find(opener)
        if start == -1 or html.count(opener) != 1:
            raise BuildError(f"הסקשן {name} לא נמצא פעם אחת בדיוק")
        end = html.find("</section>", start)
        if html.find("<section", start + 1, end) != -1:
            raise BuildError(f"בתוך הסקשן {name} נפתח סקשן נוסף")
        sections[name] = (start, end + len("</section>"))
    return sections


def wa_link(html):
    m = re.search(r'href="(https://wa\.me/972559397247\?text=[^"]+)"', html)
    if not m:
        raise BuildError("הקישור לנועם לא נמצא")
    return m.group(1)


WA_ICON = ('<svg class="wa-ic" viewBox="0 0 24 24" fill="#25D366" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>')


def noam_button(cls, label):
    return (f'<a href="{WA}" class="btn {cls}" target="_blank" rel="noopener noreferrer">'
            f'{WA_ICON}<span>{label}</span></a>')


def hero(block):
    old_text = block[block.find('<span class="eyebrow">'):block.find('<a href="#intro" class="btn btn--gold">')]
    block = once(block, old_text, (
        '<span class="eyebrow">תוכנית האצה של 5 שבועות</span>\n'
        '      <h1>5 שבועות, ואתם בונים בעצמכם<br><span class="accent">סוכני AI</span> שעובדים בשבילכם.</h1>\n'
        '      <p class="hero__sub">כבר בשבועיים הראשונים אתם בונים דברים אמיתיים לעסק, שחוסכים לכם זמן ועובדים. לא צריך לדעת לתכנת.</p>\n'
        '      <p class="cold-fit">למי שכבר משתמש ב-AI ורוצה שהוא יעשה עבודה אמיתית במקומו.</p>\n      '
    ), "פתיחת המסך הראשון")
    block = once(block, '<a href="#intro" class="btn btn--gold">איך זה עובד</a>', (
        noam_button("btn--gold cold-cta", "לבדיקת התאמה עם נועם") +
        '\n      <p class="cold-noam">נועם הוא סוכן ה-AI של אִימפּרוּב בוואטסאפ. הוא עונה על שאלות ובודק איתכם אם זה מתאים לכם.</p>'
        '\n      <a href="#price" class="cold-more">מה לומדים, מתי ובכמה</a>'
    ), "הכפתור במסך הראשון")
    block = once(block,
                 '<p class="hero-office__cap">זה משרד ה-AI שמריץ את אימפרוב בלי עובדים. כזה תבנו גם אתם.</p>',
                 '<p class="hero-office__cap">זה משרד ה-AI שמריץ את אִימפּרוּב בלי עובדים. כזה תבנו גם אתם.</p>\n'
                 '        <p class="cold-legend"><span>קובייה: סוכן</span><span>גלולה: מסמך ידע</span>'
                 '<span>חרוט: סקיל</span><span>טבעת: תהליך אוטומטי</span></p>',
                 "הכיתוב מתחת למשרד")
    return block


def proofs(block):
    block = once(block, '<h2>וזה כבר קורה.<br>אנשים כמוכם <span class="accent-blue">כבר בנו את זה.</span></h2>',
                 '<h2>אנשים כמוכם <span class="accent-blue">כבר בנו את זה.</span></h2>', "כותרת הבוגרים")
    block = once(block, 'אלה <span class="now-underline">בוגרים</span> של המחזורים האחרונים - וזה מה שהם כבר בנו.',
                 'הם <span class="now-underline">בוגרים</span> של המחזורים האחרונים, וזה מה שהם בנו.', "פתיח הבוגרים")
    block = once(block, 'בניית <span class="accent-blue">משרד AI שלם</span> זה בדיוק לאן שכולכם הולכים. ויש מי שכבר לקח את זה צעד אחד רחוק יותר -',
                 'ויש מי שלקח את זה עוד צעד קדימה -', "המעבר לרון")
    return block


FIT = '''<section class="section section--white center cold-fit-sec" id="fit">
  <div class="container">
    <h2>למי זה מתאים, <span class="accent-blue">ומה זה דורש</span></h2>
    <p class="lead center">עברו אצלנו עורכות דין, מטפלות, בעלי סוכנויות פרסום, סמנכ"לית בחברה בינלאומית, רואה חשבון ומפתח אפליקציות. מה שצריך כאן הוא לא רקע טכני, אלא כיוון: משהו אחד בעבודה שאתם רוצים שירוץ בלעדיכם.</p>
    <div class="cold-cards">
      <div class="cold-card">
        <h3>זה בשבילכם אם</h3>
        <ul>
          <li>יש לכם עבודה שחוזרת על עצמה, ואתם רוצים שמשהו יעשה אותה במקומכם.</li>
          <li>אתם כבר עובדים עם ChatGPT, Claude או כלי דומה, ומרגישים שהוא יכול הרבה יותר.</li>
          <li>אתם רוצים לבנות בעצמכם, ולא לחכות שמישהו יבנה לכם.</li>
          <li>לא צריך לדעת לתכנת. רוב הבוגרים לא הגיעו מרקע טכני.</li>
        </ul>
      </div>
      <div class="cold-card">
        <h3>זה פחות בשבילכם אם</h3>
        <ul>
          <li>אתם מחפשים מישהו שיבנה לכם את הסוכנים. כאן אתם בונים, ואנחנו לוקחים אתכם יד ביד.</li>
          <li>אין לכם בשבועות הקרובים זמן לעבוד בין המפגשים.</li>
        </ul>
      </div>
    </div>
    <div class="cold-time">
      <h3>וכמה זמן זה לוקח?</h3>
      <p>נפגשים פעם בשבוע ל-3 שעות. אבל העבודה האמיתית קורית בין המפגשים.</p>
      <p>בשבועיים הראשונים זה לפחות כמה שעות טובות בשבוע, כי המטרה היא שכבר אז תבנו דברים אמיתיים לעסק. זו תוכנית קצרה, והיא בנויה כדי להביא אתכם להצלחה מהירה.</p>
      <figure class="cold-quote">
        <img src="bogrim/images/adidotan1.jpg" alt="עדי דותן" loading="lazy">
        <blockquote>"צריך להבין שיש פה השקעה, בטח בשבועיים הראשונים, לא מבוטלת. [...] <span class="tm-hl">אחרי שבועיים הצלחתי כבר לראות פירות.</span> הצלחתי לייצר דברים שלא דמיינתי בכלל שאני אצליח לעשות."</blockquote>
        <figcaption>עדי דותן · שכירה בהייטק</figcaption>
      </figure>
    </div>
  </div>
</section>'''


MAP_HEAD = '''<section class="section section--white center cold-map-sec" id="map">
  <div class="container">
    <h2>מה תבנו, <span class="accent-blue">שלב אחרי שלב</span></h2>
    <p class="lead center">לא לומדים תיאוריה על סוכנים. בונים אחד, ואז עוד אחד, וכל שלב נשען על מה שכבר עובד.</p>
    <ol class="cold-steps">
      <li><span class="cold-steps__n">1</span><div><h3>הדבר הראשון שרץ בלעדיכם</h3><p>תהליך אוטומטי שעושה במקומכם את העבודה הכי שחורה. משהו שקורה מעצמו, כל יום, בלי שנגעתם בו.</p><p class="cold-eg">לדוגמה: איסוף חשבוניות ושליחה לרואה החשבון · מעבר על המיילים והכנת טיוטות מענה · מענה ללקוחות בוואטסאפ</p></div></li>
      <li><span class="cold-steps__n">2</span><div><h3>סוכן שחושב כמוכם</h3><p>לא בוט עם תשובות מוכנות. סוכן שמכיר את הידע שלכם ועובד לפי ההיגיון שלכם.</p><p class="cold-eg">לדוגמה: הצעות מחיר מורכבות · תוכן לרשתות · ניתוח וסיכום של מכרזים</p></div></li>
      <li><span class="cold-steps__n">3</span><div><h3>הסוכנים עובדים יחד</h3><p>במקום כמה סוכנים נפרדים, שרשרת שעובדת מקצה לקצה.</p><p class="cold-eg">לדוגמה: מסכם שיחת מכירה ← מוציא ממנה הצעת מחיר ← שולח אותה ללקוח במייל</p></div></li>
      <li><span class="cold-steps__n">4</span><div><h3>משרד שלם שעובד</h3><p>מחלקות, תפקידים וידע משותף. אתם מנהלים מלמעלה, במקום לעשות הכול בעצמכם.</p></div></li>
    </ol>
    <p class="lead center cold-map-weeks">בטירונות זה קורה במשך 5 שבועות, אחרי הכנה שמתחילה עוד לפני המפגש הראשון. ככה זה נראה, שבוע אחרי שבוע:</p>
  </div>
'''


def map_section(roadmap_block):
    images = roadmap_block[roadmap_block.find('<img class="roadmap-img'):roadmap_block.rfind("</section>")]
    if images.count('<img class="roadmap-img') != 2:
        raise BuildError("תמונות מפת המסע לא נמצאו")
    return MAP_HEAD + "  " + images.strip() + "\n</section>"


VIDEOS_PANEL = ('<div class="tm-panel" role="tabpanel" id="tm-panel-videos" aria-labelledby="tm-tab-videos">'
                '<p class="tm-panel__title">יש על זה מלא סרטונים ברשת. למה לשלם?</p><div class="tm-answer">'
                '<p class="tm-answer__lead">סרטונים יש בשפע. אבל כדי להגיע ממה שאתם עושים היום למערכת שעובדת בשבילכם, '
                'צריך שיטה, ומישהו שייקח אתכם צעד אחרי צעד. ואם הגעתם עד לכאן, כנראה שגם אתם הגעתם לתקרה של מה שאפשר לבד.</p>'
                '<ul class="tm-results">'
                '<li><b>חני:</b> "הקורס הזה נתן לי את הקפיצה. <strong>אין מה להשוות</strong> לפודקאסטים או לסרטונים שיש ביוטיוב."</li>'
                '<li><b>ספיר:</b> "ניסיתי לפתח סוכנים בעצמי עם מה שראיתי ביוטיוב, והצלחתי באופן חלקי. '
                'אבל ברגע שאת דיברת על שיטה, <strong>הבנתי שזה מה שחסר לי</strong>."</li>'
                '</ul></div></div>')


def doubts(block):
    block = once(block, '<h2 class="tm-title">עדיין מתלבטים?</h2>',
                 '<h2 class="tm-title">מה שאתם בטח שואלים עכשיו</h2>', "כותרת השאלות")
    block = once(block, 'aria-selected="false" tabindex="-1">למה רק 5 מפגשים?</button>',
                 'aria-selected="false" tabindex="-1">רק 5 שבועות?</button>', "הלשונית של 5 המפגשים")
    block = once(block, 'איך 5 מפגשים מספיקים כדי ללמוד את כל זה?', 'איך 5 שבועות מספיקים כדי ללמוד את כל זה?',
                 "השאלה של 5 המפגשים")
    tried = 'aria-selected="false" tabindex="-1">מה שונה כאן מקורסים אחרים?</button>'
    block = once(block, tried, tried + '<button type="button" class="tm-chip" role="tab" id="tm-tab-videos" '
                 'aria-controls="tm-panel-videos" aria-selected="false" tabindex="-1">יש על זה סרטונים ברשת</button>',
                 "הלשונית החדשה")
    panel_start = block.find('<div class="tm-panel" role="tabpanel" id="tm-panel-change"')
    if panel_start == -1:
        raise BuildError("הפאנל של 'ומה אם ה-AI ישתנה' לא נמצא")
    return block[:panel_start] + VIDEOS_PANEL + block[panel_start:]


def price(block):
    old_h2 = block[block.find('<h2 class="price-promise">'):block.find('</h2>', block.find('<h2 class="price-promise">')) + 5]
    block = once(block, old_h2,
                 '<h2 class="price-promise"><span class="price-promise__kicker">זה לא עוד קורס. זו תוכנית האצה של 5 שבועות.</span>'
                 '5 שבועות שבהם אתם לומדים את כל מה שצריך <span class="accent-blue">כדי לבנות את מה שאתם רוצים</span>, ובונים כבר תוך כדי.</h2>',
                 "כותרת המחיר")
    old_list = block[block.find('<ul class="price-includes">'):block.find('</ul>', block.find('<ul class="price-includes">')) + 5]
    block = once(block, old_list, '''<ul class="price-includes">
      <li><span><strong>5 מפגשי לייב, פעם בשבוע</strong> - בימי רביעי, 18:30-21:30, בתל אביב או בזום. בכל מפגש לומדים ובונים יחד</span></li>
      <li><span><strong>דואגים שתגיעו מוכנים</strong> - הכנה אישית מסודרת, מקימים איתכם את סביבת העבודה ובונים את הסוכן הראשון שלכם עוד לפני המפגש הראשון</span></li>
      <li><span><strong>לא משאירים אתכם לבד בין המפגשים</strong> - מפגשי חידוד שבועיים בזום, צוות שעוזר בזמן אמת, וסוכני AI של אִימפּרוּב שמלווים אתכם בלמידה ובבנייה</span></li>
      <li><span><strong>מה שבניתם נשאר שלכם</strong> - ההקלטות, אתר חומרי הלמידה וכל מה שבניתם נשארים אצלכם, בלי הגבלת זמן</span></li>
      <li><span><strong>שיטה ולא כלי</strong> - לומדים דרך עבודה שממשיכה לעבוד גם כשהכלים משתנים</span></li>
    </ul>''', "רשימת מה כלול")
    block = once(block, '<div class="price-card__offer">רוצים הטבה של <span class="nowrap">1,400&nbsp;₪</span>?</div>',
                 '<div class="price-card__offer">הטבה של <span class="nowrap">1,400&nbsp;₪</span> ניתנת בשיחה עם נועם</div>',
                 "ההטבה")
    block = once(block, '<a href="#video-noam" class="price-card__cta">צפו בסרטון למטה</a>',
                 noam_button("btn--navy cold-price-cta", "לשיחה עם נועם"), "הכפתור בכרטיס המחיר")
    return block


def final(block):
    block = once(block, 'כי יש לי שיטה שמאפשרת לבנות כל דבר, גם מה שמעולם לא בניתי.',
                 'כי יש לי שיטה שמאפשרת לבנות גם דברים שמעולם לא בניתי.', "השיטה של שלהבת")
    block = once(block, '<p><strong>ואחריה גם לכם יהיה הקסם הזה בידיים</strong> - היכולת לבנות כל דבר שרק תחלמו עליו: כל סוכן, כל מערכת, כל כלי.</p>',
                 '<p><strong>ואחריה גם אתם תדעו לבנות</strong> את מה שהעבודה שלכם צריכה, גם דברים שעוד לא בניתם אף פעם.</p>',
                 "הפסקה על הקסם")
    return block


COLD_CSS = '''<style id="cold-css">
  .cold-fit { font-size: 16px; opacity: .9; margin: 6px 0 18px; }
  .cold-cta { display: inline-flex; align-items: center; gap: 10px; }
  .cold-cta .wa-ic, .cold-price-cta .wa-ic { width: 22px; height: 22px; }
  .cold-noam { font-size: 14px; opacity: .85; margin: 10px 0 6px; max-width: 34em; }
  .cold-more { display: inline-block; font-size: 15px; color: #fff; text-decoration: underline; text-underline-offset: 3px; margin-top: 4px; }
  .cold-legend { display: flex; flex-wrap: wrap; justify-content: center; gap: 6px 14px; font-size: 13px; opacity: .85; margin: 8px 0 0; }
  .cold-cards { display: grid; gap: 16px; margin: 28px auto 0; max-width: 900px; text-align: right; }
  @media (min-width: 760px) { .cold-cards { grid-template-columns: 1fr 1fr; } }
  .cold-card { background: #fff; border: 1px solid rgba(20, 9, 59, .14); border-radius: 18px; padding: 22px 22px 10px; }
  .cold-card h3 { margin: 0 0 10px; font-size: 20px; color: var(--navy); }
  .cold-card ul { margin: 0; padding: 0 18px 0 0; }
  .cold-card li { margin: 0 0 12px; line-height: 1.6; }
  .cold-time { max-width: 760px; margin: 36px auto 0; text-align: right; }
  .cold-time h3 { font-size: 22px; color: var(--navy); margin: 0 0 8px; }
  .cold-time p { line-height: 1.7; margin: 0 0 10px; }
  .cold-quote { display: grid; grid-template-columns: 56px 1fr; gap: 6px 14px; align-items: start; background: #f6f7fb; border: 1px solid rgba(20, 9, 59, .1); border-radius: 18px; padding: 18px; margin: 18px 0 0; }
  .cold-quote img { width: 56px; height: 56px; border-radius: 50%; object-fit: cover; grid-row: span 2; }
  .cold-quote blockquote { margin: 0; line-height: 1.65; }
  .cold-quote figcaption { font-size: 14px; opacity: .75; }
  .cold-steps { list-style: none; margin: 30px auto 0; padding: 0; max-width: 820px; text-align: right; display: grid; gap: 14px; }
  .cold-steps li { display: grid; grid-template-columns: 44px 1fr; gap: 14px; background: #fff; border: 1px solid rgba(20, 9, 59, .12); border-radius: 18px; padding: 18px; }
  .cold-steps__n { width: 44px; height: 44px; border-radius: 50%; background: var(--navy); color: #fff; font-weight: 700; font-size: 20px; display: flex; align-items: center; justify-content: center; }
  .cold-steps h3 { margin: 0 0 6px; font-size: 19px; color: var(--navy); }
  .cold-steps p { margin: 0 0 6px; line-height: 1.6; }
  .cold-eg { font-size: 14px; opacity: .8; }
  .cold-map-weeks { margin-top: 34px; }
  .cold-price-cta { display: inline-flex; align-items: center; gap: 10px; margin-top: 12px; }
</style>
'''


def build():
    global WA
    html = SRC.read_text(encoding="utf-8")
    WA = wa_link(html)
    spans = cut_sections(html)
    first = min(s for s, _ in spans.values())
    last = max(e for _, e in spans.values())
    blocks = {name: html[s:e] for name, (s, e) in spans.items()}

    built = {
        "hero": hero(blocks["hero"]),
        "proofs": proofs(blocks["proofs"]),
        "fit": FIT,
        "map": map_section(blocks["roadmap"]),
        "doubts": doubts(blocks["doubts"]),
        "intro": blocks["intro"],
        "inside": blocks["inside"],
        "price": price(blocks["price"]),
        "google": blocks["google"],
        "video": blocks["video"],
        "final": final(blocks["final"]),
    }
    body = "\n\n".join(built[name] for name in ORDER)
    out = html[:first] + body + html[last:]

    out = once(out, "<title>טירונות סוכנים - בונים צוות AI שעובד בשבילכם</title>",
               "<title>טירונות סוכנים - תוכנית האצה של 5 שבועות</title>\n"
               '<meta name="robots" content="noindex, nofollow">', "כותרת הדף")
    out = once(out, "</head>", COLD_CSS + "</head>", "העיצוב של הגרסה")
    # המדידה: שם דף נפרד, והסקשנים לפי הסדר החדש, כדי שהגרסה לא תתערבב בנתונים של הדף הקיים
    out = once(out, "var PAGE = 'index';", "var PAGE = 'hatzaa';", "שם הדף במדידה")
    old_sections = out[out.find("var SECTIONS = ["):out.find("];", out.find("var SECTIONS = [")) + 2]
    out = once(out, old_sections, """var SECTIONS = [
      ['hero',    '.hero'],
      ['proofs',  '.section--proofs'],
      ['fit',     '#fit'],
      ['map',     '#map'],
      ['doubts',  '#tm-doubts'],
      ['intro',   '#intro'],
      ['price',   '#price'],
      ['video',   '#video-noam'],
      ['final',   '.final']
    ];""", "רשימת הסקשנים במדידה")

    # רק הטקסט שנכתב כאן נבדק; טקסט שהגיע מ-index.html נשאר כמו שהוא
    new_text = FIT + MAP_HEAD + VIDEOS_PANEL + COLD_CSS
    for bad in ("—", "–", "→"):
        if bad in new_text:
            raise BuildError(f"בטקסט החדש יש את התו האסור {bad!r}")

    OUT.write_text(out, encoding="utf-8")
    print(f"נכתב {OUT.name}: {len(out):,} תווים, {out.count('<section')} סקשנים")


if __name__ == "__main__":
    try:
        build()
    except BuildError as e:
        print(f"הבנייה נעצרה: {e}", file=sys.stderr)
        sys.exit(1)
