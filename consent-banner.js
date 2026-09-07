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
    try { reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) {}

    /* בונים ב-JS ולא ב-HTML קבוע, כדי שלא יהיה שום הבזק (flash) של הבאנר
       למי שכבר החליט בעבר.

       שדרוג-בולטות 07-09-2026: מתוך 456 ביקורים בדף הראשי, רק 161 (35%)
       בכלל לחצו על כפתור - 295 גללו הלאה בלי לגעת בבאנר. הפס גדול ובולט
       יותר, ונכנס באנימציה במקום לקפוץ לעמדה שלו - כדי שיירשם כמשהו
       שקורה על המסך, לא רק כרצועה קבועה שהעין מתרגלת אליה. עדיין לא-חוסם:
       אפשר לגלול ולהתעלם, בכוונה - לא הפכנו אותו לחלון-מודאלי. */
    function showBanner() {
      if (bar) return;
      bar = document.createElement('div');
      bar.setAttribute('dir', 'rtl');
      bar.style.cssText = 'position:fixed;left:0;right:0;bottom:0;z-index:9999;'
        + 'background:#14093B;color:#fff;padding:20px 24px;'
        + 'display:flex;flex-wrap:wrap;gap:16px;align-items:center;justify-content:center;'
        + 'font-family:"Rubik",Arial,sans-serif;font-size:15.5px;line-height:1.5;'
        + 'box-shadow:0 -10px 32px rgba(0,0,0,.35);'
        + (reduceMotion
            ? ''
            : 'transform:translateY(100%);opacity:0;transition:transform .45s cubic-bezier(.16,1,.3,1),opacity .35s ease-out;');

      var text = document.createElement('span');
      text.style.cssText = 'flex:1;min-width:240px;max-width:640px;';
      text.textContent = 'אנחנו משתמשים בעוגיות שיווקיות (פייסבוק, גוגל) כדי להבין מה עובד ולהראות לכם תוכן רלוונטי. אפשר לאשר או לסרב - הדף יעבוד בכל מקרה.';

      var btnRow = document.createElement('div');
      btnRow.style.cssText = 'display:flex;gap:10px;flex-shrink:0;';

      var accept = document.createElement('button');
      accept.type = 'button';
      accept.textContent = 'מאשר/ת';
      accept.style.cssText = 'background:#FFD747;color:#14093B;border:none;border-radius:10px;'
        + 'padding:12px 26px;font-weight:700;font-size:15.5px;cursor:pointer;font-family:inherit;';

      var decline = document.createElement('button');
      decline.type = 'button';
      decline.textContent = 'לא תודה';
      decline.style.cssText = 'background:transparent;color:#fff;border:1px solid rgba(255,255,255,.4);'
        + 'border-radius:10px;padding:12px 26px;font-weight:600;font-size:15.5px;cursor:pointer;font-family:inherit;';

      function close() {
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
      bar.appendChild(text);
      bar.appendChild(btnRow);
      document.body.appendChild(bar);

      if (!reduceMotion) {
        requestAnimationFrame(function () {
          requestAnimationFrame(function () {
            bar.style.transform = 'translateY(0)';
            bar.style.opacity = '1';
          });
        });
        /* פעימה עדינה חד-פעמית על כפתור האישור, אחרי שהפס כבר נכנס -
           לא לפני, כדי לא להתחרות עם אנימציית-הכניסה עצמה. */
        window.setTimeout(function () {
          if (!accept.isConnected) return;
          accept.style.transition = 'transform .35s ease-in-out';
          var n = 0;
          function pulse() {
            if (!accept.isConnected || n >= 2) { accept.style.transform = ''; return; }
            accept.style.transform = n % 2 === 0 ? 'scale(1.06)' : 'scale(1)';
            n++;
            window.setTimeout(pulse, 350);
          }
          pulse();
        }, 900);
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
