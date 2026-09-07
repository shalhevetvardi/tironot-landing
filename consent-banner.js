/* ── הסכמה לכלי-שיווק (פיקסל פייסבוק + גוגל אנליטיקס) ──────────────────
   קובץ משותף לכל דפי טירונות (הוצא מתוך index.html ב-07-09-2026 - היה
   מועתק ידנית לכל דף בנפרד, וזו הסיבה שהוא נשמט מ-usa/ ו-usa/en/).
   כל דף טוען את הקובץ הזה בתגית <script src="...consent-banner.js">
   במקום להחזיק עותק מקומי - עדכון יחיד חל על כל הדפים בבת אחת.

   ההסכמה נשמרת ב-localStorage (aim_consent: 'granted'/'denied') ותקפה
   לכל דפי האתר הסטטי הזה (נפרד מהוורדפרס של aimprove.co.il - אין ביניהם
   שום שיתוף-מצב). כפתור "פרטיות" הקבוע בפינה מאפשר לשנות החלטה בכל רגע. */
(function () {
  try {
    var CONSENT_KEY = 'aim_consent';
    var PIXEL_ID = '1249254740429699';
    var GA_ID = 'G-4VXR3V1J4N';

    /* דף נגזר מהנתיב, לא מוזרק ידנית - כך שדף חדש (usa/en/, וכל דף עתידי)
       מקבל באנר מהרגע שהוא טוען את הקובץ, בלי שום עריכה נוספת. */
    function detectPage() {
      var p = location.pathname;
      if (p.indexOf('/stories') !== -1) return 'stories';
      if (p.indexOf('/faq') !== -1) return 'faq';
      if (p.indexOf('/bogrim') !== -1) return 'bogrim';
      if (p.indexOf('/referral-program') !== -1) return 'referral';
      if (p.indexOf('/usa') !== -1) return 'usa';
      return 'index';
    }
    var PAGE = detectPage();

    function loadPixel() {
      try {
        !function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?
        n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;
        n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
        t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,
        document,'script','https://connect.facebook.net/en_US/fbevents.js');
        fbq('init', PIXEL_ID);
        fbq('track', 'PageView');
      } catch (e) {}
    }

    function loadGA() {
      try {
        var s = document.createElement('script');
        s.async = true;
        s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
        document.head.appendChild(s);
        window.dataLayer = window.dataLayer || [];
        function gtag() { dataLayer.push(arguments); }
        window.gtag = gtag;
        gtag('js', new Date());
        gtag('config', GA_ID);
      } catch (e) {}
    }

    function loaded() {
      try { return !!(window.fbq && window.fbq.loaded); } catch (e) { return false; }
    }

    function loadAll() {
      if (loaded()) return;
      loadPixel();
      loadGA();
    }

    /* רישום ההחלטה בשרת (Worker + Airtable) - אותו צינור בדיוק כמו מדידת-
       המשפך (בדפים שבהם היא רצה), כדי שתהיה רשומה מרכזית של מי הסכים
       ומתי, לא רק דגל בדפדפן של המבקר עצמו. אותו מפתח sessionStorage
       (aim_vid) כמו המשפך - אם הוא כבר קיים נעשה בו שימוש חוזר (כדי
       שאפשר יהיה לצלוב אם ירצו), ואם לא, נוצר כאן מזהה אפמרלי חדש כדי
       שהבלוק הזה יעבוד גם בדף שאין בו את סקריפט המשפך. */
    function sendConsentEvent(choice) {
      try {
        var vid = '';
        try { vid = sessionStorage.getItem('aim_vid') || ''; } catch (e) {}
        if (!vid) {
          vid = (Math.random().toString(16).slice(2) + Math.random().toString(16).slice(2)).slice(0, 16);
          try { sessionStorage.setItem('aim_vid', vid); } catch (e) {}
        }
        var payload = JSON.stringify({ v: 1, vid: vid, e: 'consent', p: PAGE, c: choice });
        var ENDPOINT = 'https://r.aimprove.co.il/e';
        if (navigator.sendBeacon) {
          navigator.sendBeacon(ENDPOINT, new Blob([payload], { type: 'text/plain;charset=UTF-8' }));
        } else {
          var x = new XMLHttpRequest();
          x.open('POST', ENDPOINT, true);
          x.setRequestHeader('Content-Type', 'text/plain;charset=UTF-8');
          x.send(payload);
        }
      } catch (e) {}
    }

    var bar = null;
    var reduceMotion = false;
    var prevOverflow = '';
    try { reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) {}

    /* בונים ב-JS ולא ב-HTML קבוע, כדי שלא יהיה שום הבזק (flash) של הבאנר
       למי שכבר החליט בעבר.

       07-09-2026: הפך מפס-תחתון לחלון חוסם. הסיבה במספרים - מתוך 456 ביקורים
       בדף הראשי, רק 161 (35%) בכלל לחצו על כפתור; 295 גללו הלאה בלי להחליט
       כלום. פס בתחתית תמיד יאפשר את זה, זו התכונה שלו.

       ⚖️ מותר, ובתנאי אחד שנשמר כאן במפורש: הסירוב קל בדיוק כמו האישור
       (אותו גודל, אותה לחיצה אחת), ומי שסירב מקבל את הדף במלואו. מה שאסור
       הוא להתנות את הגישה באישור - וזה בדיוק מה שלא עושים כאן. אין X ואין
       סגירה בלחיצה בחוץ, כי המטרה היא החלטה - לא לכידה. */
    function showBanner() {
      if (bar) return;
      bar = document.createElement('div');
      bar.setAttribute('dir', 'rtl');
      bar.setAttribute('role', 'dialog');
      bar.setAttribute('aria-modal', 'true');
      bar.setAttribute('aria-label', 'הסכמה לעוגיות שיווקיות');
      bar.style.cssText = 'position:fixed;inset:0;z-index:2147483000;'
        + 'background:rgba(9,4,26,.72);display:flex;align-items:center;justify-content:center;padding:20px;'
        + 'font-family:"Rubik",Arial,sans-serif;'
        + (reduceMotion ? '' : 'opacity:0;transition:opacity .28s ease-out;');

      var card = document.createElement('div');
      card.style.cssText = 'background:#14093B;color:#fff;border-radius:18px;padding:28px 26px;'
        + 'max-width:520px;width:100%;box-shadow:0 24px 60px rgba(0,0,0,.45);'
        + 'font-size:15.5px;line-height:1.6;text-align:right;'
        + (reduceMotion ? '' : 'transform:translateY(14px) scale(.98);transition:transform .32s cubic-bezier(.16,1,.3,1);');

      var title = document.createElement('div');
      title.textContent = 'רגע לפני שנתחיל';
      title.style.cssText = 'font-size:20px;font-weight:700;margin-bottom:10px;';

      var text = document.createElement('div');
      text.style.cssText = 'margin-bottom:22px;color:rgba(255,255,255,.88);';
      text.textContent = 'אנחנו משתמשים בעוגיות שיווקיות (פייסבוק, גוגל) כדי להבין מה עובד ולהראות לכם תוכן רלוונטי. אפשר לאשר או לסרב - הדף יעבוד בכל מקרה.';

      var btnRow = document.createElement('div');
      btnRow.style.cssText = 'display:flex;gap:10px;flex-wrap:wrap;';

      var accept = document.createElement('button');
      accept.type = 'button';
      accept.textContent = 'מאשר/ת';
      accept.style.cssText = 'flex:1;min-width:140px;background:#FFD747;color:#14093B;border:none;border-radius:10px;'
        + 'padding:13px 26px;font-weight:700;font-size:15.5px;cursor:pointer;font-family:inherit;';

      var decline = document.createElement('button');
      decline.type = 'button';
      decline.textContent = 'לא תודה';
      decline.style.cssText = 'flex:1;min-width:140px;background:transparent;color:#fff;border:1px solid rgba(255,255,255,.45);'
        + 'border-radius:10px;padding:13px 26px;font-weight:600;font-size:15.5px;cursor:pointer;font-family:inherit;';

      /* מקלדת: Tab מסתובב בין שני הכפתורים בלבד כל עוד החלון פתוח. */
      function trap(e) {
        if (e.key !== 'Tab') return;
        var focusables = [accept, decline];
        var i = focusables.indexOf(document.activeElement);
        e.preventDefault();
        var next = e.shiftKey ? (i <= 0 ? focusables.length - 1 : i - 1) : (i === focusables.length - 1 ? 0 : i + 1);
        focusables[next].focus();
      }

      function close() {
        try { document.removeEventListener('keydown', trap, true); } catch (e) {}
        try { document.body.style.overflow = prevOverflow; } catch (e) {}
        try { bar.remove(); } catch (e) {}
        bar = null;
      }

      accept.addEventListener('click', function () {
        try { localStorage.setItem(CONSENT_KEY, 'granted'); } catch (e) {}
        sendConsentEvent('granted');
        loadAll();
        close();
      });
      decline.addEventListener('click', function () {
        try { localStorage.setItem(CONSENT_KEY, 'denied'); } catch (e) {}
        sendConsentEvent('denied');
        close();
      });

      btnRow.appendChild(accept);
      btnRow.appendChild(decline);
      card.appendChild(title);
      card.appendChild(text);
      card.appendChild(btnRow);
      bar.appendChild(card);
      document.body.appendChild(bar);

      try { prevOverflow = document.body.style.overflow; document.body.style.overflow = 'hidden'; } catch (e) {}
      document.addEventListener('keydown', trap, true);
      /* מפקסים על החלון עצמו ולא על "מאשר/ת" - פוקוס על כפתור האישור הופך
         Enter לאישור בהיסח הדעת, וזו הטיה לטובת צד אחד. */
      card.setAttribute('tabindex', '-1');
      try { card.focus({ preventScroll: true }); } catch (e) {}

      if (!reduceMotion) {
        requestAnimationFrame(function () {
          requestAnimationFrame(function () {
            bar.style.opacity = '1';
            card.style.transform = 'translateY(0) scale(1)';
          });
        });
      }
    }

    /* כפתור-פינה קבוע וצנוע - מאפשר לשנות החלטה גם אחרי שכבר נבחרה. */
    function addReopener() {
      var link = document.createElement('button');
      link.type = 'button';
      link.textContent = '⚙ פרטיות';
      link.setAttribute('dir', 'rtl');
      link.style.cssText = 'position:fixed;left:14px;bottom:14px;z-index:9998;'
        + 'background:rgba(20,9,59,.85);color:#fff;border:none;border-radius:20px;'
        + 'padding:7px 14px;font-size:12.5px;font-family:"Rubik",Arial,sans-serif;'
        + 'cursor:pointer;opacity:.55;transition:opacity .15s;';
      link.addEventListener('mouseenter', function () { link.style.opacity = '1'; });
      link.addEventListener('mouseleave', function () { link.style.opacity = '.55'; });
      link.addEventListener('click', showBanner);
      function mount() { document.body.appendChild(link); }
      if (document.body) mount();
      else document.addEventListener('DOMContentLoaded', mount);
    }

    var consent = '';
    try { consent = localStorage.getItem(CONSENT_KEY) || ''; } catch (e) {}

    if (consent === 'granted') loadAll();
    else if (consent !== 'denied') {
      if (document.body) showBanner();
      else document.addEventListener('DOMContentLoaded', showBanner);
    }

    addReopener();
  } catch (e) { /* לעולם לא שובר את הדף */ }
})();
