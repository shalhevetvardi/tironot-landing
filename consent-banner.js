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
      if (p.indexOf('/hatzaa') !== -1) return 'hatzaa';
      return 'index';
    }
    var PAGE = detectPage();

    /* סימון "זו אני" (15-10-2026): מכשיר של הצוות לא טוען פיקסל ואנליטיקס ולא
       שולח את אירוע ההסכמה. שני מקורות: העוגייה המשותפת לכל aimprove.co.il
       (נקבעת ב-r.aimprove.co.il/optout), ו-localStorage aim_optout של האתר הזה
       (?aim_optout=1, אותו מפתח שמשפך דף הנחיתה בודק). הבאנר עצמו מופיע כרגיל. */
    var OPTOUT = false;
    try {
      var optParam = new URLSearchParams(location.search).get('aim_optout');
      if (optParam === '1') localStorage.setItem('aim_optout', '1');
      else if (optParam === '0') localStorage.removeItem('aim_optout');
      OPTOUT = localStorage.getItem('aim_optout') === '1';
    } catch (e) {}
    try {
      if (!OPTOUT && ('; ' + document.cookie + ';').indexOf('; aim_optout=1;') !== -1) OPTOUT = true;
    } catch (e) {}

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
      if (OPTOUT || loaded()) return;
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
      if (OPTOUT) return;
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
    var reopener = null;
    var reduceMotion = false;
    try { reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) {}

    /* בונים ב-JS ולא ב-HTML קבוע, כדי שלא יהיה שום הבזק (flash) של הבאנר
       למי שכבר החליט בעבר.

       24-10-2026: חזר להיות פס קטן בתחתית, בהחלטה של שלהבת. בין 07-09 ל-24-10
       זה היה חלון שמכסה את כל המסך, כי עם פס רק 161 מתוך 456 ביקורים (35%)
       בחרו משהו, והשאר גללו הלאה בלי שהפיקסל והאנליטיקס נטענו. החלון כיסה
       בטלפון את המסך הראשון בדיוק בשניות שבהן קורא חדש מחליט אם להישאר,
       והיא בחרה במסך הראשון על פני אחוז המאשרים, בידיעה שהאחוז צפוי לרדת.
       אחוז המאשרים נמדד מאירועי ההסכמה (e: 'consent') מול הכניסות במשפך.

       ⚖️ התנאים שנשמרים: הפיקסל והאנליטיקס נטענים רק אחרי אישור, הסירוב קל
       בדיוק כמו האישור (אותו גודל, לחיצה אחת), ומי שלא בחר מקבל את הדף במלואו.
       בפס יש קישור למדיניות הפרטיות, שלא היה בחלון.

       24-10-2026, מאוחר יותר: הפס הוגדל לגיליון בתחתית, שתופס כשליש מהמסך בטלפון,
       לבקשת שלהבת ("הוא צריך יותר להציק"), כדי שיותר מבקרים יבחרו. המסך הראשון
       עדיין נראה מעליו, והגלילה לא נחסמת. */
    function showBanner() {
      if (bar) return;
      bar = document.createElement('div');
      bar.setAttribute('dir', 'rtl');
      bar.setAttribute('role', 'region');
      bar.setAttribute('aria-label', 'הסכמה לעוגיות שיווקיות');
      bar.style.cssText = 'position:fixed;left:0;right:0;bottom:0;z-index:2147483000;'
        + 'background:#14093B;color:#fff;box-shadow:0 -6px 24px rgba(0,0,0,.28);'
        + 'border-radius:20px 20px 0 0;min-height:min(36vh,320px);display:flex;align-items:center;'
        + 'padding:22px 20px calc(22px + env(safe-area-inset-bottom));'
        + 'font-family:"Rubik",Arial,sans-serif;font-size:15.5px;line-height:1.55;'
        + (reduceMotion ? '' : 'transform:translateY(100%);transition:transform .3s ease-out;');

      var inner = document.createElement('div');
      inner.style.cssText = 'width:100%;max-width:640px;margin:0 auto;display:flex;flex-direction:column;gap:16px;text-align:right;';

      var title = document.createElement('div');
      title.textContent = 'רגע לפני שנתחיל';
      title.style.cssText = 'font-size:20px;font-weight:700;color:#fff;margin-bottom:-6px;';

      var text = document.createElement('div');
      text.style.cssText = 'color:rgba(255,255,255,.9);';
      text.appendChild(document.createTextNode('אנחנו משתמשים בעוגיות שיווקיות (פייסבוק, גוגל) כדי להבין מה עובד. הדף עובד גם בלי. '));
      var policy = document.createElement('a');
      policy.href = 'https://aimprove.co.il/privacy-policy/';
      policy.target = '_blank';
      policy.rel = 'noopener noreferrer';
      policy.textContent = 'מדיניות הפרטיות';
      policy.style.cssText = 'color:#fff;text-decoration:underline;text-underline-offset:2px;';
      text.appendChild(policy);

      var btnRow = document.createElement('div');
      btnRow.style.cssText = 'display:flex;gap:10px;';

      var accept = document.createElement('button');
      accept.type = 'button';
      accept.textContent = 'מאשר/ת';
      accept.style.cssText = 'flex:1;background:#FFD747;color:#14093B;border:1px solid #FFD747;border-radius:12px;'
        + 'padding:14px 16px;font-weight:700;font-size:16px;cursor:pointer;font-family:inherit;';

      var decline = document.createElement('button');
      decline.type = 'button';
      decline.textContent = 'לא תודה';
      decline.style.cssText = 'flex:1;background:transparent;color:#fff;border:1px solid rgba(255,255,255,.55);'
        + 'border-radius:12px;padding:14px 16px;font-weight:600;font-size:16px;cursor:pointer;font-family:inherit;';

      function close() {
        try { bar.remove(); } catch (e) {}
        bar = null;
        if (reopener) reopener.style.display = '';
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
      inner.appendChild(title);
      inner.appendChild(text);
      inner.appendChild(btnRow);
      bar.appendChild(inner);
      document.body.appendChild(bar);
      /* כפתור "פרטיות" יושב באותה פינה, ולכן מוסתר כל עוד הפס פתוח */
      if (reopener) reopener.style.display = 'none';

      if (!reduceMotion) {
        requestAnimationFrame(function () {
          requestAnimationFrame(function () { if (bar) bar.style.transform = 'translateY(0)'; });
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
        + 'cursor:pointer;';
      link.addEventListener('click', showBanner);
      reopener = link;
      function mount() {
        if (bar) link.style.display = 'none';
        document.body.appendChild(link);
      }
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
