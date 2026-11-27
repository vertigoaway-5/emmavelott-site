/* Bundle offer at checkout.
   When a reader clicks a single book's Gumroad buy link, show a short offer first with two
   choices: all six books (the Complete Emma Velott Collection) or the matching three-book
   bundle (the Emma Velott Collection, or the Hollybourne Christmas set for a Hollybourne
   novella). Shown once per browser session, and shown again when a
   reader who already picked a different book (it is sitting in their Gumroad cart) picks
   another, because by then the bundle costs about the same or less than the singles.
   "No thanks, just this book" carries on to the original checkout, and only then does the
   site's tracking (InitiateCheckout / begin_checkout) fire for that book.
   The __PLACEHOLDERS__ are filled in by build.py from books.json and the BUNDLE settings. */
(function () {
  // One entry per bundle: the Emma Velott Collection and the Hollybourne Christmas set.
  // A single book is only ever offered the bundle it belongs to.
  var SETS = __SETS__;
  var ALL = __ALL__;   // the six-book set, offered beside every three-book bundle
  var BUNDLE, FULL, PRICE, SAVE, COVERS, BOOKS, COPY, NAME;
  var KEY, PICKS, DAY = 864e5, passthrough = false;
  function use(set) {
    BUNDLE = set.bundle; FULL = set.full; PRICE = set.price; SAVE = set.save; COVERS = set.covers; BOOKS = set.books; COPY = set.copy; NAME = set.name;
    KEY = 'ev_bundle_offer_seen' + set.key; PICKS = 'ev_picked_books' + set.key;
  }
  use(SETS[0]);

  // Books this reader has already sent to Gumroad's cart (kept 30 days, like Gumroad's cart).
  function picks() {
    try {
      var p = JSON.parse(localStorage.getItem(PICKS) || '{}'), now = Date.now(), out = {};
      Object.keys(p).forEach(function (k) { if (now - p[k] < 30 * DAY && BOOKS[k]) out[k] = p[k]; });
      return out;
    } catch (e) { return {}; }
  }
  function remember(perm) { try { var p = picks(); p[perm] = Date.now(); localStorage.setItem(PICKS, JSON.stringify(p)); } catch (e) {} }
  function forget() { try { localStorage.removeItem(PICKS); } catch (e) {} }
  function perm(href) { var m = href.match(/gumroad\.com\/l\/([^/?#]+)/); return m ? m[1] : null; }
  function money(n) { return '$' + n.toFixed(2); }

  function seen() { try { return sessionStorage.getItem(KEY) === '1'; } catch (e) { return false; } }
  function markSeen() { try { sessionStorage.setItem(KEY, '1'); } catch (e) {} }

  // Keeps the ad's own utm_content (so a sale still shows which ad brought the reader)
  // and adds which offer was taken on the end: "--upsell-all6" or "--upsell-set3".
  function bundleUrl(fromHref, base, mark) {
    var u = new URL(base), ad = '';
    try {
      new URL(fromHref).searchParams.forEach(function (v, k) { if (/^utm_/.test(k)) u.searchParams.set(k, v); });
      ad = u.searchParams.get('utm_content') || '';
    } catch (e) {}
    u.searchParams.set('utm_content', (ad ? ad.slice(0, 80) + '--' : '') + mark);
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
    '.evu-covers:not(.evu-six) img:nth-child(1){transform:rotate(-8deg)}' +
    '.evu-covers:not(.evu-six) img:nth-child(2){width:96px;height:144px;z-index:2;position:relative}' +
    '.evu-covers:not(.evu-six) img:nth-child(3){transform:rotate(8deg)}' +
    '.evu-six{height:118px;margin-bottom:16px}' +
    '.evu-six img{width:70px;height:105px;margin:0 -7px}' +
    '.evu-six img:nth-child(odd){transform:translateY(-8px)}' +
    '.evu-k{font:600 11.5px/1 var(--body,Arial);letter-spacing:.2em;text-transform:uppercase;color:var(--claret,#7a2e33);margin:0 0 10px}' +
    '.evu h3{font-family:var(--display,Georgia);font-size:27px;line-height:1.2;margin:0 0 10px;font-weight:600}' +
    '.evu h3 em{color:var(--green,#2f4a3f)}' +
    '.evu p{font:400 16px/1.55 var(--body,Arial);color:var(--ink-soft,#544c45);margin:0 0 20px}' +
    '.evu-price{font-family:var(--display,Georgia);font-size:26px;margin:0 0 18px}' +
    '.evu-price s{font:400 15px var(--body,Arial);color:#9a9086;margin-right:6px}' +
    '.evu-price span{display:inline-block;margin-left:8px;font:700 12px/1 var(--body,Arial);letter-spacing:.08em;background:var(--claret,#7a2e33);color:#fbf0dc;padding:6px 9px;border-radius:20px;vertical-align:middle}' +
    '.evu-opts{display:grid;gap:10px;margin:0 0 12px;text-align:left}' +
    '.evu-opt{position:relative;display:grid;grid-template-columns:1fr auto;align-items:center;gap:4px 14px;padding:15px 16px;border:1.5px solid var(--gold-soft,#d8bd85);border-radius:8px;text-decoration:none;color:var(--ink,#2b2622);background:#fff;transition:border-color .2s,background .2s}' +
    '.evu-opt:hover{border-color:var(--green,#2f4a3f);color:var(--ink,#2b2622)}' +
    '.evu-opt b{font:600 18px/1.25 var(--display,Georgia)}' +
    '.evu-opt i{grid-column:1;font:400 13.5px/1.4 var(--body,Arial);color:var(--ink-soft,#544c45)}' +
    '.evu-opt u{grid-column:2;grid-row:1/span 2;text-decoration:none;text-align:right;font:600 19px/1.2 var(--display,Georgia);white-space:nowrap}' +
    '.evu-opt u s{display:block;font:400 13px var(--body,Arial);color:#9a9086}' +
    '.evu-opt u em{display:block;font:700 11px/1 var(--body,Arial);letter-spacing:.06em;font-style:normal;color:var(--claret,#7a2e33);margin-top:4px}' +
    '.evu-best{background:var(--green,#2f4a3f);border-color:var(--green,#2f4a3f);color:#fff;padding-top:22px}' +
    '.evu-best:hover{background:var(--green-2,#3c5c4f);color:#fff}' +
    '.evu-best i{color:#e3ebe6}.evu-best u s{color:#b9c9c0}.evu-best u em{color:#f1d9a4}' +
    '.evu-tag{position:absolute;top:-9px;left:14px;background:var(--claret,#7a2e33);color:#fbf0dc;font:700 10.5px/1 var(--body,Arial);letter-spacing:.1em;text-transform:uppercase;padding:5px 9px;border-radius:20px}' +
    '.evu-yes{display:block;background:var(--green,#2f4a3f);color:#fff;font:700 16px/1 var(--body,Arial);padding:17px 20px;border-radius:6px;text-decoration:none;margin:0 0 12px;transition:background .2s}' +
    '.evu-yes:hover{background:var(--green-2,#3c5c4f);color:#fff}' +
    '.evu-note{font-size:13px!important;margin:12px 0 0!important;color:#8a8076!important}' +
    '.evu-no{background:none;border:0;font:400 14.5px var(--body,Arial);color:#7d746b;text-decoration:underline;cursor:pointer;padding:6px}' +
    '@media (max-height:600px){.evu{padding-top:24px}.evu-covers{height:110px;margin-bottom:10px}.evu-covers img{width:62px;height:93px}.evu-covers:not(.evu-six) img:nth-child(2){width:72px;height:108px}.evu-six{height:84px}.evu-six img{width:50px;height:75px}.evu p{margin-bottom:12px}}' +
    '@media (max-width:480px){.evu{padding:30px 20px 22px}.evu h3{font-size:23px}.evu-six img{width:54px;height:81px;margin:0 -6px}.evu-opt{padding:14px 13px}.evu-best{padding-top:21px}.evu-opt b{font-size:16.5px}.evu-opt u{font-size:17px}}';

  function openOffer(link, others) {
    markSeen();
    var here = perm(link.href), chosen = others.concat([here]).filter(function (k) { return BOOKS[k]; });
    var singles = chosen.reduce(function (t, k) { return t + BOOKS[k].price; }, 0), bundle = parseFloat(PRICE);
    var kicker = 'Before you go',
        title = ALL ? COPY.titleAll : COPY.title,
        body = ALL ? COPY.bodyAll : COPY.body,
        note = '';
    if (others.length) {
      var names = others.map(function (k) { return '<em>' + BOOKS[k].title + '</em>'; }).join(' and ');
      kicker = 'A better deal';
      if (singles >= bundle) {
        title = 'The bundle is <em>' + money(singles - bundle) + ' cheaper</em> than buying these separately.';
        body = 'You already picked ' + names + '. Get all three together for ' + money(bundle) + ' instead.';
      } else {
        title = 'Add the third book for <em>just ' + money(bundle - singles) + ' more.</em>';
        body = 'You already picked ' + names + '. For ' + money(bundle) + ' you get all three, this one included.';
      }
      note = '<p class="evu-note">Switching? Remove the single books from your Gumroad cart so you only pay for the bundle.</p>';
    }
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
        '<div class="evu-covers' + (ALL ? ' evu-six' : '') + '" aria-hidden="true">' +
          (ALL ? ALL.covers : COVERS).map(function (s) { return '<img src="/covers/' + s + '.jpg" alt="">'; }).join('') +
        '</div>' +
        '<p class="evu-k">' + kicker + '</p>' +
        '<h3 id="evu-title">' + title + '</h3>' +
        '<p>' + body + '</p>' +
        (ALL ?
        '<div class="evu-opts">' +
          '<a class="evu-opt evu-best evu-yes-all" href="' + bundleUrl(link.href, ALL.bundle, 'upsell-all6') + '"><span class="evu-tag">Best value</span>' +
            '<b>All six books</b><i>' + ALL.line + '</i>' +
            '<u><s>$' + ALL.full + '</s>$' + ALL.price + '<em>SAVE ' + ALL.save + '%</em></u></a>' +
          '<a class="evu-opt evu-yes-set" href="' + bundleUrl(link.href, BUNDLE, 'upsell-set3') + '">' +
            '<b>' + COPY.three + '</b><i>' + NAME + '</i>' +
            '<u><s>$' + FULL + '</s>$' + PRICE + '<em>SAVE ' + SAVE + '%</em></u></a>' +
        '</div>'
        :
        '<div class="evu-price"><s>$' + FULL + '</s>$' + PRICE + '<span>SAVE ' + SAVE + '%</span></div>' +
        '<a class="evu-yes" href="' + bundleUrl(link.href, BUNDLE, 'upsell-set3') + '">Yes, I want all three</a>') +
        '<button type="button" class="evu-no">No thanks, just this book</button>' + note +
      '</div>';
    document.body.appendChild(back);
    requestAnimationFrame(function () { back.classList.add('on'); });
    back.querySelector('.evu-opt,.evu-yes').focus();

    function close() { back.remove(); document.removeEventListener('keydown', esc); link.focus(); }
    function esc(e) { if (e.key === 'Escape') close(); }
    document.addEventListener('keydown', esc);
    back.querySelector('.evu-x').onclick = close;
    back.addEventListener('click', function (e) { if (e.target === back) close(); });
    Array.prototype.forEach.call(back.querySelectorAll('.evu-opt,.evu-yes'), function (y) { y.addEventListener('click', forget); });
    back.querySelector('.evu-no').onclick = function () {
      close();
      if (others.length) markOffered(here);
      passthrough = true;
      link.click();          // goes to the single-book checkout and fires the normal tracking
      passthrough = false;
    };
  }

  // Runs on window, before the site's own click tracking on document,
  // so a checkout is only recorded once the reader has actually chosen.
  // Books the reader already said "just this book" to on this visit, so we don't ask twice.
  function wasOffered(k) { try { return (sessionStorage.getItem('ev_reoffered') || '').split(',').indexOf(k) > -1; } catch (e) { return false; } }
  function markOffered(k) { try { var v = sessionStorage.getItem('ev_reoffered'); sessionStorage.setItem('ev_reoffered', (v ? v + ',' : '') + k); } catch (e) {} }
  window.addEventListener('click', function (e) {
    if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    var a = e.target.closest && e.target.closest('a[href*="gumroad.com/l/"]');
    if (!a || a.closest('.evu')) return;
    var here = perm(a.href), set = null, i;
    if (ALL && a.href.indexOf(ALL.bundle) === 0) { for (i = 0; i < SETS.length; i++) { use(SETS[i]); forget(); } return; }
    for (i = 0; i < SETS.length; i++) { if (a.href.indexOf(SETS[i].bundle) === 0) { use(SETS[i]); forget(); return; } }
    for (i = 0; i < SETS.length; i++) { if (here && SETS[i].books[here]) set = SETS[i]; }
    if (!set) return;   // not one of our single books: no offer
    use(set);
    if (passthrough || e.defaultPrevented) { if (here) remember(here); return; }
    var others = Object.keys(picks()).filter(function (k) { return k !== here; });
    var show = others.length ? !wasOffered(here) : !seen();
    if (!show) { if (here) remember(here); return; }
    e.preventDefault();
    e.stopPropagation();
    openOffer(a, others);
  }, true);
})();
