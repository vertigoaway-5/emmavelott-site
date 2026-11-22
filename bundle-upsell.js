/* Bundle offer at checkout.
   When a reader clicks a single book's Gumroad buy link, show a short offer for the
   Emma Velott Collection first. Shown once per browser session.
   "No thanks, just this book" carries on to the original checkout, and only then does the
   site's tracking (InitiateCheckout / begin_checkout) fire for that book.
   The __PLACEHOLDERS__ are filled in by build.py from books.json and the BUNDLE settings. */
(function () {
  var BUNDLE = '__BUNDLE__', FULL = '__FULL__', PRICE = '__PRICE__', SAVE = '__SAVE__', COVERS = __COVERS__;
  var KEY = 'ev_bundle_offer_seen', passthrough = false;

  function seen() { try { return sessionStorage.getItem(KEY) === '1'; } catch (e) { return false; } }
  function markSeen() { try { sessionStorage.setItem(KEY, '1'); } catch (e) {} }

  function bundleUrl(fromHref) {
    var u = new URL(BUNDLE);
    try {
      new URL(fromHref).searchParams.forEach(function (v, k) { if (/^utm_/.test(k)) u.searchParams.set(k, v); });
    } catch (e) {}
    u.searchParams.set('utm_content', 'checkout_upsell');
    return u.toString();
  }

  var css =
    '.evu-back{position:fixed;inset:0;background:rgba(30,26,22,.55);display:flex;align-items:center;justify-content:center;z-index:9999;padding:18px;opacity:0;transition:opacity .2s}' +
    '.evu-back.on{opacity:1}' +
    '.evu{position:relative;background:var(--card,#fcf9f2);color:var(--ink,#2b2622);max-width:520px;width:100%;max-height:calc(100vh - 36px);overflow:auto;border-radius:12px;padding:34px 32px 26px;box-shadow:0 30px 70px -20px rgba(0,0,0,.5);text-align:center;transform:translateY(10px);transition:transform .25s}' +
    '.evu-back.on .evu{transform:none}' +
    '.evu:before{content:"";position:absolute;inset:9px;border:1px solid var(--gold-soft,#d8bd85);border-radius:7px;pointer-events:none}' +
    '.evu-x{position:absolute;top:12px;right:14px;background:none;border:0;font-size:26px;line-height:1;color:#8a8076;cursor:pointer;z-index:1}' +
    '.evu-covers{display:flex;justify-content:center;align-items:flex-end;margin:0 0 18px;height:150px}' +
    '.evu-covers img{width:82px;height:123px;max-width:none;object-fit:cover;border-radius:2px 4px 4px 2px;box-shadow:0 10px 18px -8px rgba(0,0,0,.5);margin:0 -10px}' +
    '.evu-covers img:nth-child(1){transform:rotate(-8deg)}' +
    '.evu-covers img:nth-child(2){width:96px;height:144px;z-index:2;position:relative}' +
    '.evu-covers img:nth-child(3){transform:rotate(8deg)}' +
    '.evu-k{font:600 11.5px/1 var(--body,Arial);letter-spacing:.2em;text-transform:uppercase;color:var(--claret,#7a2e33);margin:0 0 10px}' +
    '.evu h3{font-family:var(--display,Georgia);font-size:27px;line-height:1.2;margin:0 0 10px;font-weight:600}' +
    '.evu h3 em{color:var(--green,#2f4a3f)}' +
    '.evu p{font:400 16px/1.55 var(--body,Arial);color:var(--ink-soft,#544c45);margin:0 0 20px}' +
    '.evu-price{font-family:var(--display,Georgia);font-size:26px;margin:0 0 18px}' +
    '.evu-price s{font:400 15px var(--body,Arial);color:#9a9086;margin-right:6px}' +
    '.evu-price span{display:inline-block;margin-left:8px;font:700 12px/1 var(--body,Arial);letter-spacing:.08em;background:var(--claret,#7a2e33);color:#fbf0dc;padding:6px 9px;border-radius:20px;vertical-align:middle}' +
    '.evu-yes{display:block;background:var(--green,#2f4a3f);color:#fff;font:700 16px/1 var(--body,Arial);padding:17px 20px;border-radius:6px;text-decoration:none;margin:0 0 12px;transition:background .2s}' +
    '.evu-yes:hover{background:var(--green-2,#3c5c4f);color:#fff}' +
    '.evu-no{background:none;border:0;font:400 14.5px var(--body,Arial);color:#7d746b;text-decoration:underline;cursor:pointer;padding:6px}' +
    '@media (max-height:600px){.evu{padding-top:24px}.evu-covers{height:110px;margin-bottom:10px}.evu-covers img{width:62px;height:93px}.evu-covers img:nth-child(2){width:72px;height:108px}}' +
    '@media (max-width:480px){.evu{padding:30px 20px 22px}.evu h3{font-size:23px}}';

  function openOffer(link) {
    markSeen();
    if (!document.getElementById('evu-css')) {
      var st = document.createElement('style'); st.id = 'evu-css'; st.textContent = css; document.head.appendChild(st);
    }
    var back = document.createElement('div');
    back.className = 'evu-back';
    back.setAttribute('role', 'dialog');
    back.setAttribute('aria-modal', 'true');
    back.setAttribute('aria-labelledby', 'evu-title');
    back.innerHTML =
      '<div class="evu">' +
        '<button type="button" class="evu-x" aria-label="Close">&times;</button>' +
        '<div class="evu-covers" aria-hidden="true">' +
          COVERS.map(function (s) { return '<img src="/covers/' + s + '.jpg" alt="">'; }).join('') +
        '</div>' +
        '<p class="evu-k">Before you go</p>' +
        '<h3 id="evu-title">Why stop at one duke when you could have <em>all three love stories?</em></h3>' +
        '<p>Get every Emma Velott romance in one bundle, this book included.</p>' +
        '<div class="evu-price"><s>$' + FULL + '</s>$' + PRICE + '<span>SAVE ' + SAVE + '%</span></div>' +
        '<a class="evu-yes" href="' + bundleUrl(link.href) + '">Yes, I want all three</a>' +
        '<button type="button" class="evu-no">No thanks, just this book</button>' +
      '</div>';
    document.body.appendChild(back);
    requestAnimationFrame(function () { back.classList.add('on'); });
    back.querySelector('.evu-yes').focus();

    function close() { back.remove(); document.removeEventListener('keydown', esc); link.focus(); }
    function esc(e) { if (e.key === 'Escape') close(); }
    document.addEventListener('keydown', esc);
    back.querySelector('.evu-x').onclick = close;
    back.addEventListener('click', function (e) { if (e.target === back) close(); });
    back.querySelector('.evu-no').onclick = function () {
      close();
      passthrough = true;
      link.click();          // goes to the single-book checkout and fires the normal tracking
      passthrough = false;
    };
  }

  // Runs on window, before the site's own click tracking on document,
  // so a checkout is only recorded once the reader has actually chosen.
  window.addEventListener('click', function (e) {
    if (passthrough || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    var a = e.target.closest && e.target.closest('a[href*="gumroad.com/l/"]');
    if (!a || a.href.indexOf(BUNDLE) === 0 || a.closest('.evu') || seen()) return;
    e.preventDefault();
    e.stopPropagation();
    openOffer(a);
  }, true);
})();
