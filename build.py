"""Builds the Emma Velott site into _site/.

Content lives in two files:
  books.json    one entry per book (title, prices, Gumroad link, blurb...)
  reviews.json  reader reviews, e.g.
                {"book": "a-fiery-widow-for-the-cold-duke",
                 "quote": "I couldn't put it down.",
                 "name": "Sarah", "source": "Instagram",
                 "url": "https://www.instagram.com/...", "stars": 5}
                ("url" and "stars" are optional)

To add a book, add it to books.json. Its cover, page, home-page card and
sitemap entry are all created automatically from that entry.

Run locally with SKIP_COVERS=1 to skip downloading covers.
"""
import datetime
import html
import json
import os
import shutil
import subprocess

SITE = "https://emmavelott.com"
OUT = "_site"
TODAY = datetime.date.today().isoformat()
PRIORITY = 'fetchpriority="high" '
FONTS = "https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,500;0,600;1,500&family=Open+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap"

BOOKS = json.load(open("books.json", encoding="utf-8"))
# First-chapter samples: {slug: {"heading": "...", "paras": ["...", ...]}}
SAMPLES = json.load(open("samples.json", encoding="utf-8")) if os.path.exists("samples.json") else {}
REVIEWS = json.load(open("reviews.json", encoding="utf-8"))
# Reading guides (trope/search landing pages): one entry per page, see build_guide()
GUIDES = json.load(open("guides.json", encoding="utf-8")) if os.path.exists("guides.json") else []
GUIDES_SLUG = "reading-guides"
SLUGS = {b["slug"] for b in BOOKS}
for r in REVIEWS:
    assert r.get("book") in SLUGS, f"review for unknown book: {r.get('book')}"


def esc(s):
    return html.escape(s, quote=True)


def cover_alt(b):
    return f"Cover of {esc(b['title'])}, {esc(b['subtitle'].lower())} by Emma Velott"


def page_title(b):
    return f"{b['title']}: {b['subtitle']} | Emma Velott"


# ---------- shared pieces ----------

META_PIXEL_ID = "1181112837681717"
FACEBOOK = "https://www.facebook.com/profile.php?id=61596411127455"
PINTEREST = "https://www.pinterest.com/emmavelott/"
BUNDLE = "https://emaanspark835.gumroad.com/l/emma-velott-collection"
BUNDLE_PRICE = 8.99
# Order of the fanned covers in the bundle feature and checkout offer (middle one is the big one).
BUNDLE_COVER_ORDER = ["the-rakish-viscounts-pretend-wife", "a-fiery-widow-for-the-cold-duke",
                      "a-jilted-bride-for-the-battle-scarred-duke"]

GOOGLE_TAG_ID = "GTM-MC72GXTC"  # Google tag for GA4 property emmavelott.com (measurement ID G-BKEVHFKZTW)
GOOGLE_TAG = f"""<script async src="https://www.googletagmanager.com/gtag/js?id={GOOGLE_TAG_ID}"></script>
<script>
window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}
gtag('js',new Date());
</script>"""

# Meta Pixel: PageView on every page, Lead on newsletter signup, InitiateCheckout on any Gumroad buy link.
PIXEL = f"""<script>
!function(f,b,e,v,n,t,s){{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)}};if(!f._fbq)f._fbq=n;
n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}}(window,
document,'script','https://connect.facebook.net/en_US/fbevents.js');
fbq('init','{META_PIXEL_ID}');fbq('track','PageView');
document.addEventListener('submit',function(e){{if(e.target.classList&&e.target.classList.contains('signup'))fbq('track','Lead');}});
</script>
<noscript><img height="1" width="1" style="display:none" alt="" src="https://www.facebook.com/tr?id={META_PIXEL_ID}&ev=PageView&noscript=1"></noscript>
{{TRACKING}}"""

# Which book each Gumroad link sells, keyed by its /l/ permalink.
# Used to put the book's ID on the InitiateCheckout event.
GUMROAD_PRODUCTS = {b["buy"].rstrip("/").rsplit("/l/", 1)[1]: {"id": b["slug"], "name": b["title"], "value": float(b["price"])} for b in BOOKS}
GUMROAD_PRODUCTS[BUNDLE.rsplit("/l/", 1)[1]] = {"id": "emma-velott-collection", "name": "The Emma Velott Collection", "value": BUNDLE_PRICE}

# Sale attribution.
# 1. When a visitor arrives with UTM tags (or a Meta/Bing/Pinterest click ID),
#    remember where they came from for 7 days, matching Meta's 7-day click window.
#    The latest ad click wins.
# 2. Every Gumroad link on the page gets those UTM tags added, plus
#    utm_term = the page the buy button was on, so each Gumroad sale shows
#    the ad/campaign that brought the reader and the page they bought from.
# 3. Buy links get wanted=true, which skips Gumroad's product page and opens
#    the payment form straight away (one less click before paying).
# 4. InitiateCheckout carries the book's ID, name and price.
TRACKING = """<script>
(function(){
var P=__PRODUCTS__,K=['utm_source','utm_medium','utm_campaign','utm_content'],S='ev_utm',DAY=864e5,t=null;
try{t=JSON.parse(localStorage.getItem(S)||'null');if(t&&Date.now()-t.at>7*DAY)t=null;}catch(e){}
var q=new URLSearchParams(location.search),n=null;
if(K.some(function(k){return q.get(k);})){n={};K.forEach(function(k){if(q.get(k))n[k]=q.get(k).slice(0,100);});}
else if(q.get('fbclid')){n={utm_source:'facebook',utm_medium:'paid_social',utm_campaign:'untagged_meta_ad'};}
else if(q.get('msclkid')){n={utm_source:'bing',utm_medium:'cpc',utm_campaign:'untagged_bing_ad'};}
else if(q.get('epik')){n={utm_source:'pinterest',utm_medium:'paid_social',utm_campaign:'untagged_pinterest_ad'};}
else if(!t&&document.referrer){var r='';try{r=new URL(document.referrer).hostname.replace(/^www\\./,'');}catch(e){}
if(r&&r!==location.hostname){var s=/facebook|fb\\.|instagram|pinterest|pin\\.it/.test(r);n={utm_source:r,utm_medium:s?'social':'referral'};}}
if(n){n.at=Date.now();t=n;try{localStorage.setItem(S,JSON.stringify(t));}catch(e){}}
if(!t)t={utm_source:'emmavelott.com',utm_medium:'website'};
var page=location.pathname.replace(/^\\/|\\/$|\\.html$/g,'')||'home';
function prod(a){var m=a.href.match(/gumroad\\.com\\/l\\/([^/?#]+)/);return m?P[m[1]]:null;}
function tag(a){try{var u=new URL(a.href);K.forEach(function(k){if(t[k]&&!u.searchParams.get(k))u.searchParams.set(k,t[k]);});
u.searchParams.set('utm_term',page.slice(0,100));if(/\\/l\\//.test(u.pathname))u.searchParams.set('wanted','true');a.href=u.toString();}catch(e){}}
function tagAll(){document.querySelectorAll('a[href*="gumroad.com"]').forEach(tag);}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',tagAll);else tagAll();
document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[href*="gumroad.com"]');if(!a)return;tag(a);
var p=prod(a);if(window.fbq)fbq('track','InitiateCheckout',p?{content_ids:[p.id],content_type:'product',content_name:p.name,value:p.value,currency:'USD',num_items:1}:{content_name:'gumroad_store'});
if(window.gtag)gtag('event','begin_checkout',p?{currency:'USD',value:p.value,items:[{item_id:p.id,item_name:p.name,price:p.value}]}:{});},true);
})();
</script>""".replace("__PRODUCTS__", json.dumps(GUMROAD_PRODUCTS, separators=(",", ":")))
PIXEL = PIXEL.replace("{TRACKING}", TRACKING)


def _ver(path):
    """Short content hash, so browsers fetch a file again whenever it changes."""
    import hashlib
    return hashlib.md5(open(path, "rb").read()).hexdigest()[:8]


CSS_VER = _ver("styles.css")
JS_VER = _ver("bundle-upsell.js")


def head_assets(prefix):
    return f"""<link rel="icon" href="{prefix}favicon.svg" type="image/svg+xml">
<link rel="icon" href="{prefix}favicon.ico" sizes="32x32">
<link rel="apple-touch-icon" href="{prefix}apple-touch-icon.png">
<meta name="theme-color" content="#7a2e33">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{prefix}styles.css?v={CSS_VER}">
<script src="/bundle-upsell.js?v={JS_VER}" defer></script>
<meta name="p:domain_verify" content="dcd450609e6fd7a415d088125b18bd74">
{GOOGLE_TAG}
{PIXEL}"""


KIT_FORM_ID = "10194085"
KIT_ACTION = f"https://app.kit.com/forms/{KIT_FORM_ID}/subscriptions"


def signup_form(uid):
    """Plain HTML Kit form. Kit redirects to /thanks/ after submit, /welcome/ after confirming."""
    return f"""<form class="signup" action="{KIT_ACTION}" method="post">
          <label class="sr" for="fn-{uid}">First name</label>
          <input id="fn-{uid}" name="fields[first_name]" type="text" autocomplete="given-name" placeholder="First name">
          <label class="sr" for="em-{uid}">Email address</label>
          <input id="em-{uid}" name="email_address" type="email" autocomplete="email" placeholder="Email address" required>
          <button class="btn btn-primary" type="submit">Get my free epilogue</button>
        </form>
        <p class="signup-note">Free. No spam, and you can unsubscribe with one click.</p>"""


def signup_box(uid, home, heading="Get free bonus epilogues and reader gifts", extra_class=""):
    return f"""<div class="newsletter is-live {extra_class}" id="newsletter{'' if uid == 'home' else '-' + uid}">
        <span class="kicker">Free for Emma's readers</span>
        <h3>{heading}</h3>
        <p>Join the reader list for bonus epilogues, free reader gifts, new releases and sales. Already read <a href="{home}a-jilted-bride-for-the-battle-scarred-duke/"><em>A Jilted Bride for the Battle-Scarred Duke</em></a>? Your free Christmas epilogue, <em>Twelfth Night at Penwythe</em>, is waiting the moment you confirm.</p>
        {signup_form(uid)}
      </div>"""


BUNDLE_FULL = round(sum(float(x["price"]) for x in BOOKS), 2)
BUNDLE_SAVE = round(100 * (1 - BUNDLE_PRICE / BUNDLE_FULL))


def bundle_feature():
    """Home-page bundle feature, placed straight under the hero."""
    covers = "\n".join(f'      <img src="covers/{s}.jpg" width="500" height="800" alt="">' for s in BUNDLE_COVER_ORDER)
    by_slug = {x["slug"]: x for x in BOOKS}
    items = "\n".join(
        f'        <li>{esc(by_slug[s]["title"])} <i>&#183; {esc(", ".join(t.lower() for t in by_slug[s]["tropes"][:2]))}</i></li>'
        for s in [BUNDLE_COVER_ORDER[1], BUNDLE_COVER_ORDER[0], BUNDLE_COVER_ORDER[2]] if s in by_slug)  # centre book listed first
    return f"""  <section class="evb" id="bundle" aria-labelledby="bundle-title">
  <div class="wrap"><div class="evb-card">
    <div class="evb-stack" aria-hidden="true">
{covers}
      <div class="evb-seal"><small>Save</small><strong>{BUNDLE_SAVE}%</strong></div>
    </div>
    <div>
      <p class="evb-kicker">The Emma Velott Collection</p>
      <h2 id="bundle-title">Two brooding dukes, one rakish viscount, <em>and every happily-ever-after</em> in one bundle.</h2>
      <p class="evb-lead">Every Emma Velott romance so far, delivered together, so you can binge from the first sigh to the last kiss.</p>
      <ul class="evb-list">
{items}
      </ul>
      <div class="evb-buy"><span class="evb-price"><s>${BUNDLE_FULL:.2f}</s>${BUNDLE_PRICE:.2f}</span><a class="btn-gold" href="{BUNDLE}">Get all three books</a></div>
      <p class="evb-fine">EPUB &amp; PDF &#183; DRM free &#183; emailed to you instantly</p>
    </div>
  </div></div>
  </section>"""


def site_header(home):
    return f"""<div class="ev-ribbon"><a href="{BUNDLE}"><span class="long"><b>New</b> The Emma Velott Collection, all three novels in one bundle, {BUNDLE_SAVE}% off</span><span class="short"><b>New</b> All three novels, {BUNDLE_SAVE}% off</span><span class="go">Get the bundle &#8594;</span></a></div>
<div class="strip"><a href="{home or './'}#newsletter">Get free bonus epilogues and reader gifts</a><span>&#183;</span>Ebooks delivered in moments<span>&#183;</span>Read on any device</div>
<header class="masthead">
  <div class="wrap">
    <p class="tag">Clean Regency Romance</p>
    <a class="name" href="{home or './'}">Emma Velott</a>
  </div>
  <nav class="mainnav" aria-label="Main">
    <ul>
      <li><a href="{home}#books">The Books</a></li>
      <li><a href="{home}#how">How It Works</a></li>
      <li><a href="{home}#indie">A Note from Emma</a></li>
      <li><a href="{home}#follow">Follow</a></li>
    </ul>
  </nav>
</header>"""


def site_footer(home):
    return f"""<footer>
  <div class="wrap">
    <a class="name" href="{home or './'}">Emma Velott</a>
    <ul>
      <li><a href="{home}#books">The Books</a></li>
      <li><a href="{home}clean-duke-romance-books/">Clean Duke Romances</a></li>
      <li><a href="{home}clean-christmas-regency-romance/">Christmas Romances</a></li>
      <li><a href="{home}reading-guides/">Reading Guides</a></li>
      <li><a href="{home}#how">How It Works</a></li>
      <li><a href="https://www.instagram.com/emmavelott/" target="_blank" rel="noopener">Instagram</a></li>
      <li><a href="{FACEBOOK}" target="_blank" rel="noopener">Facebook</a></li>
      <li><a href="{PINTEREST}" target="_blank" rel="noopener">Pinterest</a></li>
      <li><a href="https://emaanspark835.gumroad.com/" target="_blank" rel="noopener">Shop</a></li>
    </ul>
    <small>&#169; {datetime.date.today().year} Emma Velott. Payments are handled securely by Gumroad, and your ebook is emailed to you right after purchase.</small>
  </div>
</footer>"""


def tropes_html(tropes):
    return "<span>&#183;</span>".join(esc(t) for t in tropes)


def buy_row(b, extra=""):
    kobo = ""
    if b.get("kobo"):
        kobo = f'\n            <a class="store-link" href="{b["kobo"]}" target="_blank" rel="noopener">Also on Kobo</a>'
    return f"""<div class="buy-row">
            <span class="price">${b['price']}</span>
            <a class="btn btn-primary" href="{b['buy']}">Buy the ebook</a>
            <span class="format">EPUB &amp; PDF</span>{kobo}{extra}
          </div>"""


def sample_link(b, prefix=""):
    if b["slug"] not in SAMPLES:
        return ""
    return f'<p class="sample-link"><a href="{prefix}sample/">Read the first chapter free</a></p>'


def build_sample(b):
    s = SAMPLES[b["slug"]]
    url = f"{SITE}/{b['slug']}/sample/"
    title = f"Read the first chapter of {b['title']} free | Emma Velott"
    desc = f"Read the opening of {b['title']}, {b['subtitle'].lower()} by Emma Velott, free online."
    paras = "\n".join(f"      <p>{esc(p)}</p>" for p in s["paras"])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Emma Velott">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/covers/{b['slug']}.jpg">
{head_assets('../../')}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{site_header('../../')}
<main id="main">
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="../../">Home</a><span>&#8250;</span><a href="../">{esc(b['title'])}</a><span>&#8250;</span>Free sample</nav>
  </div>
  <article class="section sample">
    <div class="wrap narrow">
      <span class="kicker">Free sample</span>
      <h1>{esc(b['title'])}</h1>
      <p class="subtitle">{esc(b['subtitle'])} by Emma Velott</p>
      <h2 class="sample-heading">{esc(s['heading'])}</h2>
{paras}
      <div class="sample-end">
        <p class="hook">Want to know what happens next?</p>
        {buy_row(b)}
        <p class="small">Or get all three books together for $8.99 in <a href="{BUNDLE}">the Emma Velott Collection</a>.</p>
      </div>
    </div>
  </article>
</main>
{site_footer('../../')}
</body>
</html>
"""


def review_cards(reviews, show_book):
    out = []
    by_slug = {b["slug"]: b for b in BOOKS}
    for r in reviews:
        who = esc(r["name"])
        if r.get("url"):
            who = f'<a href="{esc(r["url"])}" target="_blank" rel="noopener nofollow">{who}</a>'
        src = f", on {esc(r['source'])}" if r.get("source") else ""
        book = ""
        if show_book:
            b = by_slug[r["book"]]
            book = f' about <a href="{b["slug"]}/"><em>{esc(b["title"])}</em></a>'
        stars = f'<div class="stars" aria-label="{int(r["stars"])} out of 5 stars">{"&#9733;" * int(r["stars"])}</div>' if r.get("stars") else ""
        out.append(f"""<figure class="review">
  {stars}<blockquote>&#8220;{esc(r['quote'])}&#8221;</blockquote>
  <figcaption>{who}{src}{book}</figcaption>
</figure>""")
    return "\n".join(out)


# ---------- home page ----------

def build_home():
    s = open("index.html", encoding="utf-8").read()
    covers = "\n".join(
        f'        <a href="{b["slug"]}/"><img src="covers/{b["slug"]}.jpg" width="500" height="800" '
        f'{PRIORITY if i == 0 else ""}alt="{cover_alt(b)}"></a>'
        for i, b in enumerate(BOOKS)
    )
    cards = "\n".join(
        f"""      <article class="book" id="{b['slug']}">
        <div class="frame"><a href="{b['slug']}/"><img src="covers/{b['slug']}.jpg" width="500" height="800" loading="lazy" alt="{cover_alt(b)}"></a></div>
        <div>
          <span class="kicker">{esc(b['kicker'])}</span>
          <h3><a href="{b['slug']}/">{esc(b['title'])}</a></h3>
          <p class="subtitle">{esc(b['subtitle'])}</p>
          <p class="tropes">{tropes_html(b['tropes'][:3])}</p>
          <p class="blurb">{esc(b['short'])}</p>
          {buy_row(b, chr(10) + '            <a class="more-link" href="' + b['slug'] + '/">Read more about this book</a>')}
        </div>
      </article>"""
        for b in BOOKS
    )
    reviews = ""
    if REVIEWS:
        reviews = f"""  <section class="section" id="reviews" aria-labelledby="reviews-title">
    <div class="wrap">
      <div class="section-head">
        <h2 id="reviews-title">What readers are saying</h2>
        <p>Kind words from readers on Instagram and beyond.</p>
      </div>
      <div class="reviews">
{review_cards(REVIEWS[:6], show_book=True)}
      </div>
    </div>
  </section>"""
    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebSite", "@id": SITE + "/#site", "name": "Emma Velott", "url": SITE + "/"},
            {"@type": "Person", "@id": SITE + "/#emma", "name": "Emma Velott", "url": SITE + "/",
             "jobTitle": "Author", "knowsAbout": ["Regency romance", "Clean romance", "Historical romance"],
             "sameAs": ["https://www.instagram.com/emmavelott/", FACEBOOK, PINTEREST]},
            {"@type": "ItemList", "name": "Books by Emma Velott", "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "url": f"{SITE}/{b['slug']}/", "name": b["title"]}
                for i, b in enumerate(BOOKS)]},
            {"@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": "Can I read it on my Kindle?",
                 "acceptedAnswer": {"@type": "Answer", "text": "Yes. Use Amazon's free Send to Kindle service to add the EPUB to your Kindle library."}},
                {"@type": "Question", "name": "Can I buy from the UK?",
                 "acceptedAnswer": {"@type": "Answer", "text": "Yes. Prices are in US dollars and your bank or card converts them automatically."}},
                {"@type": "Question", "name": "The email hasn't arrived. What now?",
                 "acceptedAnswer": {"@type": "Answer", "text": "Check your spam or promotions folder, or use the 'Already bought this? Get your download link' option on the book's Gumroad page."}}]},
        ],
    }
    for marker, value in {
        "<!-- HEAD_ASSETS -->": head_assets(""),
        "<!-- HOME_SCHEMA -->": f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>',
        "<!-- HEADER -->": site_header(""),
        "<!-- FOOTER -->": site_footer(""),
        "<!-- HERO_COVERS -->": covers,
        "<!-- BOOK_CARDS -->": cards,
        "<!-- REVIEWS -->": reviews,
        "<!-- BUNDLE -->": bundle_feature(),
        "<!-- NEWSLETTER -->": signup_box("home", "", extra_class="band"),
    }.items():
        assert marker in s, marker
        s = s.replace(marker, value)
    return s


# ---------- book pages ----------

def build_book(b):
    url = f"{SITE}/{b['slug']}/"
    img = f"{SITE}/covers/{b['slug']}.jpg"
    others = [o for o in BOOKS if o["slug"] != b["slug"]]
    length = "Novella" if b["kind"] == "novella" else "Full-length novel"
    reviews = [r for r in REVIEWS if r["book"] == b["slug"]]
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Book",
                "@id": url + "#book",
                "name": b["title"],
                "alternativeHeadline": b["subtitle"],
                "url": url,
                "image": img,
                "description": " ".join(b["blurb"]),
                "author": {"@type": "Person", "@id": SITE + "/#emma", "name": "Emma Velott", "url": SITE + "/"},
                "genre": ["Regency romance", "Historical romance", "Clean romance"],
                "keywords": ", ".join(["clean Regency romance", "closed-door romance"] + [t.lower() for t in b["tropes"]]),
                "inLanguage": "en",
                "datePublished": "2026-08",
                "publisher": {"@type": "Person", "name": "Emma Velott"},
                "bookFormat": "https://schema.org/EBook",
                "sameAs": [b["kobo"]] if b.get("kobo") else [],
                "offers": {"@type": "Offer", "price": b["price"], "priceCurrency": "USD",
                           "availability": "https://schema.org/InStock", "url": b["buy"]},
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Books", "item": SITE + "/#books"},
                    {"@type": "ListItem", "position": 3, "name": b["title"], "item": url},
                ],
            },
        ],
    }
    blurb = "\n".join(f"          <p>{esc(p)}</p>" for p in b["blurb"])
    review_block = ""
    if reviews:
        review_block = f"""  <section class="section" aria-labelledby="rev-title">
    <div class="wrap">
      <div class="section-head"><h2 id="rev-title">What readers are saying</h2></div>
      <div class="reviews">
{review_cards(reviews, show_book=False)}
      </div>
    </div>
  </section>"""
    more = "\n".join(
        f"""        <article class="mini">
          <a href="../{o['slug']}/"><img src="../covers/{o['slug']}.jpg" width="500" height="800" loading="lazy" alt="{cover_alt(o)}"></a>
          <div>
            <h3><a href="../{o['slug']}/">{esc(o['title'])}</a></h3>
            <p>{esc(o['hook'])}</p>
            <a class="more-link" href="../{o['slug']}/">See the book</a>
          </div>
        </article>"""
        for o in others
    )
    t = esc(page_title(b))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t}</title>
<meta name="description" content="{esc(b['meta'])}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="book">
<meta property="og:site_name" content="Emma Velott">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{esc(b['meta'])}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{img}">
<meta property="og:image:alt" content="{cover_alt(b)}">
<meta property="book:author" content="Emma Velott">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{t}">
<meta name="twitter:description" content="{esc(b['meta'])}">
<meta name="twitter:image" content="{img}">
{head_assets('../')}
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{site_header('../')}
<main id="main">
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="../">Home</a><span>&#8250;</span><a href="../#books">Books</a><span>&#8250;</span>{esc(b['title'])}</nav>
  </div>
  <article class="bp">
    <div class="wrap bp-grid">
      <div class="bp-cover"><img src="../covers/{b['slug']}.jpg" width="500" height="800" fetchpriority="high" alt="{cover_alt(b)}"></div>
      <div>
        <span class="kicker">{esc(b['kicker'])}</span>
        <h1>{esc(b['title'])}</h1>
        <p class="subtitle">{esc(b['subtitle'])} by Emma Velott</p>
        <p class="tropes">{tropes_html(b['tropes'])}</p>
        {buy_row(b)}
        {sample_link(b)}
        <p class="small">Secure checkout through Gumroad. Your download link is emailed to you straight away.</p>
        <p class="hook">{esc(b['hook'])}</p>
        <div class="bp-blurb">
{blurb}
        </div>
        <ul class="facts">
          <li><strong>Length</strong>{esc(b.get('length') or length)}</li>
          <li><strong>Published</strong>{esc(b.get('published', ''))}, ebook, published by Emma Velott</li>
          <li><strong>Heat level</strong>Clean and closed-door</li>
          <li><strong>Ending</strong>Happily ever after</li>
          <li><strong>Formats</strong>EPUB and PDF, DRM free</li>
        </ul>
        <div class="howmini">
          <h2>How buying works</h2>
          <ol>
            <li>Press "Buy the ebook" and pay at Gumroad's secure checkout. No account needed.</li>
            <li>Your download link arrives by email right away.</li>
            <li>Read the EPUB on Kindle (with Send to Kindle), Kobo, Apple Books or your phone.</li>
          </ol>
          <p class="small" style="margin-top:10px"><a href="../#how">More questions answered</a></p>
        </div>
      </div>
    </div>
  </article>
{review_block}
{guide_links_for(b)}
  <section class="section" style="padding-top:8px">
    <div class="wrap narrow">
      {signup_box(b["slug"][:12], "../")}
    </div>
  </section>
  <section class="section tinted" aria-labelledby="more-title">
    <div class="wrap">
      <div class="section-head"><h2 id="more-title">More clean Regency romance from Emma Velott</h2></div>
      <div class="more-grid">
{more}
      </div>
    </div>
  </section>
</main>
{site_footer('../')}
</body>
</html>
"""


DUKE_SLUG = "clean-duke-romance-books"


def build_duke_page():
    """Landing page for searches like 'clean duke romance books'."""
    url = f"{SITE}/{DUKE_SLUG}/"
    dukes = [b for b in BOOKS if b.get("duke")]
    others = [b for b in BOOKS if not b.get("duke")]

    def card(b):
        return f"""      <article class="book">
        <div class="frame"><a href="../{b['slug']}/"><img src="../covers/{b['slug']}.jpg" width="500" height="800" loading="lazy" alt="{cover_alt(b)}"></a></div>
        <div>
          <span class="kicker">{esc(b['kicker'])}</span>
          <h3><a href="../{b['slug']}/">{esc(b['title'])}</a></h3>
          <p class="subtitle">{esc(b['subtitle'])}</p>
          <p class="tropes">{tropes_html(b['tropes'])}</p>
          <p class="blurb">{esc(b['short'])}</p>
          {buy_row(b, chr(10) + '            <a class="more-link" href="../' + b['slug'] + '/">Read more about this book</a>')}
        </div>
      </article>"""

    title = "Clean Duke Romance Books | Regency Romances by Emma Velott"
    desc = "Clean Regency duke romance books with grumpy dukes, scarred dukes and happily-ever-afters. Closed-door historical romance ebooks by Emma Velott."
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "CollectionPage", "name": "Clean Duke Romance Books", "url": url, "description": desc,
             "about": "Clean Regency duke romance",
             "mainEntity": {"@type": "ItemList", "itemListElement": [
                 {"@type": "ListItem", "position": i + 1, "url": f"{SITE}/{b['slug']}/", "name": b["title"]}
                 for i, b in enumerate(dukes)]}},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Clean Duke Romance Books", "item": url}]},
        ],
    }
    also = ""
    if others:
        also = f"""  <section class="section tinted" aria-labelledby="also-title">
    <div class="wrap">
      <div class="section-head">
        <h2 id="also-title">Not a duke, but you'll forgive him</h2>
        <p>A clean Regency novella with a rakish viscount, for when you want a shorter read.</p>
      </div>
{chr(10).join(card(b) for b in others)}
    </div>
  </section>"""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Emma Velott">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/covers/{dukes[0]['slug']}.jpg">
<meta name="twitter:card" content="summary_large_image">
{head_assets('../')}
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{site_header('../')}
<main id="main">
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="../">Home</a><span>&#8250;</span>Clean Duke Romance Books</nav>
  </div>
  <section class="section" style="padding-top:36px" aria-labelledby="duke-title">
    <div class="wrap">
      <div class="section-head">
        <span class="kicker">Regency romance by Emma Velott</span>
        <h1 id="duke-title" style="font-size:clamp(36px,4.6vw,52px)">Clean Duke Romance Books</h1>
        <p>Grumpy dukes, scarred dukes and the women who refuse to be frightened of them. Every one is a clean, closed-door Regency romance with a happily-ever-after, so you get all the longing and none of the explicit scenes.</p>
      </div>
{chr(10).join(card(b) for b in dukes)}
    </div>
  </section>
{also}
  <section class="section" aria-labelledby="what-title">
    <div class="wrap narrow">
      <h2 id="what-title" style="font-size:32px;margin-bottom:14px">What is a clean duke romance?</h2>
      <p>A clean duke romance is a love story set among the English aristocracy, usually in the Regency era of the early 1800s, where the hero is a duke and the romance stays behind closed doors. The tension comes from glances, arguments, arrangements and slow-growing trust rather than explicit scenes. Expect grand country houses, marriages of convenience, wounded or guarded dukes and heroines with more spirit than their circumstances allow.</p>
      <p>If you enjoy Bridgerton-style settings but prefer your romance sweet and swoony, these books are written for you.</p>
      <p style="margin-top:22px"><a class="btn btn-primary" href="../#how">How buying direct works</a></p>
    </div>
  </section>
  <section class="section" style="padding-top:0">
    <div class="wrap narrow">
      {signup_box("duke", "../")}
    </div>
  </section>
</main>
{site_footer('../')}
</body>
</html>
"""


XMAS_SLUG = "clean-christmas-regency-romance"

UPCOMING_XMAS = [
    {
        "title": "The Duke Who Wouldn't Keep Christmas",
        "kind": "A full-length clean Regency Christmas romance",
        "text": "Miles Aylward, Duke of Weyburn, and Emmeline Prowse, in a clean, closed-door Regency romance set over the Christmas season.",
    },
    {
        "title": "The Hollybourne Christmas Novellas",
        "kind": "Three linked clean Christmas novellas",
        "text": "One Yorkshire dale village, from Christmas 1815 to Twelfth Night 1816. Light-hearted, full of banter and closed door, with a happily-ever-after in every one.",
        "list": [
            "Twelve Days to Keep an Earl",
            "Twelve Nights to Trust a Duke",
            "Twelve Days to Teach a Marquess",
        ],
    },
]


def build_xmas_page():
    """Seasonal landing page for 'clean Christmas Regency romance' searches."""
    url = f"{SITE}/{XMAS_SLUG}/"
    title = "Clean Christmas Regency Romance Books | Emma Velott"
    desc = "Clean Christmas Regency romance from Emma Velott. Snowbound dukes, Yorkshire villages and Twelfth Night happily-ever-afters, plus a snowy winter novella to read now."
    rakish = next(b for b in BOOKS if b["slug"] == "the-rakish-viscounts-pretend-wife")

    upcoming = []
    for u in UPCOMING_XMAS:
        items = ""
        if u.get("list"):
            items = "<ul class=\"xlist\">" + "".join(f"<li><em>{esc(t)}</em></li>" for t in u["list"]) + "</ul>"
        upcoming.append(f"""      <article class="xcard">
        <span class="kicker">Coming soon</span>
        <h3>{esc(u['title'])}</h3>
        <p class="subtitle">{esc(u['kind'])}</p>
        <p>{esc(u['text'])}</p>
        {items}
      </article>""")


    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "CollectionPage", "name": "Clean Christmas Regency Romance", "url": url, "description": desc},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Clean Christmas Regency Romance", "item": url}]},
        ],
    }
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Emma Velott">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/covers/{rakish['slug']}.jpg">
<meta name="twitter:card" content="summary_large_image">
{head_assets('../')}
<style>
.xgrid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:28px}}
.xcard{{background:var(--card);border-radius:8px;padding:30px 32px}}
.xcard h3{{font-size:28px;margin:0 0 4px}}
.xcard p{{margin:0 0 10px}}
.xlist{{margin:6px 0 0;padding-left:20px}}
.xlist li{{margin:0 0 4px}}
@media (max-width:760px){{.xgrid{{grid-template-columns:1fr}}}}
</style>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{site_header('../')}
<main id="main">
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="../">Home</a><span>&#8250;</span>Clean Christmas Regency Romance</nav>
  </div>
  <section class="section" style="padding-top:36px" aria-labelledby="x-title">
    <div class="wrap">
      <div class="section-head">
        <span class="kicker">Regency romance for the festive season</span>
        <h1 id="x-title" style="font-size:clamp(36px,4.6vw,52px)">Clean Christmas Regency Romance</h1>
        <p>Candlelit drawing rooms, snow on the lanes and a duke who would very much prefer to skip the whole season. Emma's Christmas Regency romances are clean and closed-door, with all the longing of the season and a happily-ever-after by Twelfth Night.</p>
      </div>
      <div class="xgrid">
{chr(10).join(upcoming)}
      </div>
      <div style="margin-top:40px">
      {signup_box("xmas", "../", "Hear first when the Christmas books are out")}
      </div>
    </div>
  </section>
  <section class="section tinted" aria-labelledby="now-title">
    <div class="wrap">
      <div class="section-head">
        <h2 id="now-title">A snowy winter read for right now</h2>
        <p>Not a Christmas story, but snowed in at a coaching inn with a rakish viscount is the perfect warm-up for the season.</p>
      </div>
      <article class="book">
        <div class="frame"><a href="../{rakish['slug']}/"><img src="../covers/{rakish['slug']}.jpg" width="500" height="800" loading="lazy" alt="{cover_alt(rakish)}"></a></div>
        <div>
          <span class="kicker">{esc(rakish['kicker'])}</span>
          <h3><a href="../{rakish['slug']}/">{esc(rakish['title'])}</a></h3>
          <p class="subtitle">{esc(rakish['subtitle'])}</p>
          <p class="tropes">{tropes_html(rakish['tropes'])}</p>
          <p class="blurb">{esc(rakish['short'])}</p>
          {buy_row(rakish, chr(10) + '            <a class="more-link" href="../' + rakish['slug'] + '/">Read more about this book</a>')}
        </div>
      </article>
      <p style="text-align:center;margin-top:20px"><a class="more-link" href="../{DUKE_SLUG}/">Or browse Emma's clean duke romances</a></p>
    </div>
  </section>
</main>
{site_footer('../')}
</body>
</html>
"""


# ---------- reading guides ----------

def guide_links_for(b):
    """Small 'If you like...' block on a book page, linking the guides that feature it."""
    gs = [g for g in GUIDES if any(x["slug"] == b["slug"] for x in g["books"])]
    if not gs:
        return ""
    links = "".join(f'<li><a href="../{g["slug"]}/">{esc(g["h1"])}</a></li>' for g in gs)
    return f"""  <section class="section" style="padding-top:8px;padding-bottom:8px">
    <div class="wrap narrow">
      <h2 style="font-size:26px;margin-bottom:8px">Find more books like this</h2>
      <ul class="glist">{links}</ul>
    </div>
  </section>"""


GUIDE_CSS = """<style>
.gbody h2{font-size:30px;margin:44px 0 12px}
.gbody p{font-size:18px}
.glead{font-size:21px!important;color:var(--ink-soft);font-style:italic;font-family:var(--display)}
.glist{list-style:none;padding:0;margin:0;display:flex;flex-wrap:wrap;gap:10px 22px}
.glist a{color:var(--claret)}
.ghero{display:flex;gap:28px;align-items:center}
.ghero svg{flex:0 0 130px;width:130px;height:130px}
@media (max-width:640px){.ghero{flex-direction:column;align-items:flex-start}.ghero svg{width:96px;height:96px;flex-basis:96px}}
.gossip{margin:40px 0 8px;background:#fbf6ea;border:1px solid #d8bd85;padding:26px 30px 22px;position:relative;box-shadow:4px 4px 0 #efe3c8}
.gossip .mast{font-family:var(--display);font-size:26px;font-weight:600;text-align:center;letter-spacing:.04em;border-bottom:3px double var(--ink);padding-bottom:6px;margin-bottom:4px}
.gossip .date{text-align:center;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-soft);margin-bottom:14px}
.gossip p{font-family:var(--display);font-size:18px;line-height:1.65;margin:0}
.gossip p::first-letter{font-size:46px;float:left;line-height:.9;padding:4px 8px 0 0;color:var(--claret)}
.gossip .sig{display:block;text-align:right;font-style:italic;margin-top:10px;color:var(--ink-soft);font-family:var(--display)}
.pq{margin:56px auto 40px;max-width:640px;text-align:center;padding:40px 28px 28px;border-top:1px solid #d8bd85;border-bottom:1px solid #d8bd85;position:relative}
.pq::before{content:"\\201C";font-family:var(--display);font-size:64px;line-height:56px;height:44px;overflow:hidden;color:#d8bd85;position:absolute;top:-24px;left:50%;transform:translateX(-50%);background:var(--paper);padding:0 14px}
.pq blockquote{margin:0;font-family:var(--display);font-style:italic;font-size:24px;line-height:1.45;color:var(--ink)}
.pq figcaption{margin-top:12px;font-size:15px;color:var(--ink-soft)}
.pq figcaption a{color:var(--claret)}
.ticks{background:var(--card);border-radius:10px;padding:24px 28px;margin:40px 0}
.ticks h2{margin-top:0!important;font-size:26px!important}
.ticks label{display:flex;gap:12px;align-items:flex-start;padding:7px 0;cursor:pointer;font-size:17px}
.ticks input{accent-color:var(--claret);width:20px;height:20px;margin-top:4px;flex:0 0 20px}
.ticks .verdict{margin:12px 0 0;font-family:var(--display);font-style:italic;color:var(--claret);min-height:1.6em}
.gpin{margin:48px auto;text-align:center}
.gpin img{width:100%;max-width:340px;height:auto;border-radius:8px;box-shadow:0 10px 30px rgba(60,30,30,.18)}
.gpin figcaption{margin-top:14px;font-size:15px;color:var(--ink-soft)}
.gpin .btn{margin-top:10px;background:#bd2c35;color:#fff}
.ghub{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}
.ghub article{background:var(--card);border-radius:8px;padding:26px 28px}
.ghub article svg{width:64px;height:64px;margin-bottom:8px}
.ghub h2{font-size:26px;margin:0 0 8px}
.ghub h2 a{text-decoration:none;color:inherit}
@media (max-width:760px){.ghub{grid-template-columns:1fr}}
.quiz{background:var(--card);border-radius:10px;padding:30px 32px;margin:48px 0}
.quiz fieldset{border:0;padding:0;margin:0 0 22px}
.quiz legend{font-family:var(--display);font-size:21px;font-weight:600;margin-bottom:8px}
.quiz label{display:block;padding:5px 0;cursor:pointer}
.quiz input{accent-color:var(--claret);margin-right:10px}
.quiz .result{margin-top:18px;padding:22px 24px;border:1px solid #d8bd85;border-radius:8px;background:#fbf6ea;display:none}
.quiz .result.show{display:block}
.quiz .result h3{font-size:26px;margin-bottom:6px}
</style>"""

_G = 'fill="none" stroke="#7a2e33" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"'
_A = 'fill="none" stroke="#b08c48" stroke-width="1.6" stroke-linecap="round"'
ICONS = {
    # original line drawings, claret with antique gold accents
    "fan": f"""<svg viewBox="0 0 120 120" aria-hidden="true"><g {_G}><path d="M60 98 L14 52 A65 65 0 0 1 106 52 Z"/><path d="M60 98 L26 40"/><path d="M60 98 L42 32"/><path d="M60 98 L60 29"/><path d="M60 98 L78 32"/><path d="M60 98 L94 40"/></g><g {_A}><path d="M22 46 A58 58 0 0 1 98 46"/><circle cx="60" cy="98" r="5"/><path d="M60 103 q-6 10 2 14"/></g></svg>""",
    "ring": f"""<svg viewBox="0 0 120 120" aria-hidden="true"><g {_G}><circle cx="60" cy="72" r="30"/><circle cx="60" cy="72" r="23"/></g><g {_A}><path d="M48 40 L60 24 L72 40 L60 50 Z"/><path d="M48 40 H72"/><path d="M30 26 l4 4 M90 26 l-4 4 M60 10 v6"/></g></svg>""",
    "rose": f"""<svg viewBox="0 0 120 120" aria-hidden="true"><g {_G}><path d="M60 30 c-14 0-22 10-22 20 0 12 10 20 22 20 s22-8 22-20c0-10-8-20-22-20z"/><path d="M60 38 c-7 0-11 6-11 12 0 7 5 11 11 11"/><path d="M60 46 c4 0 6 3 6 6"/><path d="M60 70 v40"/></g><g {_A}><path d="M60 92 c-10-6-20-4-24 2 8 4 18 4 24-2z"/><path d="M60 84 c10-6 20-4 24 2-8 4-18 4-24-2z"/><path d="M58 100 l-4-3 M62 104 l4-3"/></g></svg>""",
    "teacup": f"""<svg viewBox="0 0 120 120" aria-hidden="true"><g {_G}><path d="M24 50 h60 v8 c0 18-12 30-30 30 s-30-12-30-30z"/><path d="M84 56 c12 0 14 18 0 18"/><path d="M14 96 h80"/></g><g {_A}><path d="M44 40 c-4-6 4-10 0-18"/><path d="M58 40 c-4-6 4-10 0-18"/><path d="M38 66 c6 4 26 4 32 0"/></g></svg>""",
    "quill": f"""<svg viewBox="0 0 120 120" aria-hidden="true"><g {_G}><path d="M30 104 C40 70 62 34 100 14 C92 46 70 78 38 96"/><path d="M30 104 l8-8"/><path d="M14 108 h40"/></g><g {_A}><path d="M48 80 L86 28"/><path d="M58 64 l-10-2 M66 52 l-10-2 M74 40 l-9-2"/><circle cx="88" cy="104" r="8"/><path d="M80 104 h16"/></g></svg>""",
}


def _quote_html(q, prefix="../"):
    by_slug = {b["slug"]: b for b in BOOKS}
    b = by_slug[q["book"]]
    return f"""      <figure class="pq">
        <blockquote>{esc(q['text'])}</blockquote>
        <figcaption>{esc(q['who'])}, in <a href="{prefix}{b['slug']}/"><em>{esc(b['title'])}</em></a></figcaption>
      </figure>"""


TICK_JS = """<script>
document.querySelectorAll('.ticks').forEach(function(box){
  var out=box.querySelector('.verdict'),cs=box.querySelectorAll('input'),
  msgs=['Tick away, dear reader. No one is watching. Probably.','A mild inclination. Perfectly respectable.','Two? Your aunt is beginning to wonder about you.','Three. You are, as the matrons say, quite far gone.','Four. There is no hope for you, and we could not be more pleased.','All five. Fetch the smelling salts and the books below.'];
  function upd(){var n=0;cs.forEach(function(c){if(c.checked)n++});out.textContent=msgs[n];}
  cs.forEach(function(c){c.addEventListener('change',upd)});upd();
});
</script>"""


def build_guide(g):
    url = f"{SITE}/{g['slug']}/"
    by_slug = {b["slug"]: b for b in BOOKS}
    picks = [(by_slug[x["slug"]], x["why"]) for x in g["books"]]

    def card(b, why):
        return f"""      <article class="book">
        <div class="frame"><a href="../{b['slug']}/"><img src="../covers/{b['slug']}.jpg" width="500" height="800" loading="lazy" alt="{cover_alt(b)}"></a></div>
        <div>
          <span class="kicker">{esc(b['kicker'])}</span>
          <h3><a href="../{b['slug']}/">{esc(b['title'])}</a></h3>
          <p class="subtitle">{esc(b['subtitle'])}</p>
          <p class="tropes">{tropes_html(b['tropes'])}</p>
          <p class="blurb">{esc(why)}</p>
          {buy_row(b, chr(10) + '            <a class="more-link" href="../' + b['slug'] + '/">Read more about this book</a>')}
          {sample_link(b, '../' + b['slug'] + '/')}
        </div>
      </article>"""

    sections = []
    quotes = list(g.get("quotes", []))
    for i, sec in enumerate(g["sections"]):
        paras = "\n".join(f"      <p>{esc(p)}</p>" for p in sec["paras"])
        sections.append(f"      <h2>{esc(sec['h2'])}</h2>\n{paras}")
        if i in (0, 2) and quotes:
            sections.append(_quote_html(quotes.pop(0)))
        if i == 1 and g.get("checklist"):
            items = "\n".join(f'        <label><input type="checkbox"> <span>{esc(c)}</span></label>' for c in g["checklist"])
            sections.append(f"""      <div class="ticks">
        <h2>{esc(g['checklist_heading'])}</h2>
        <p class="small" style="margin:0 0 8px;color:var(--ink-soft)">Tick all that apply. We shan't tell.</p>
{items}
        <p class="verdict" aria-live="polite"></p>
      </div>""")
    for q in quotes:
        sections.append(_quote_html(q))
    if g.get("pin"):
        from urllib.parse import quote as _q
        img = f"{SITE}/pins/{g['pin']}.jpg"
        save = ("https://www.pinterest.com/pin/create/button/?url=" + _q(url, safe="") +
                "&media=" + _q(img, safe="") + "&description=" + _q(g["h1"] + " | Emma Velott", safe=""))
        sections.append(f"""      <figure class="gpin">
        <img src="../pins/{g['pin']}.jpg" width="1000" height="1500" loading="lazy" alt="{esc(g['h1'])}, a reading guide by Emma Velott">
        <figcaption>Pin it for later, so you can find it again when the ton is being tiresome.</figcaption>
        <a class="btn" href="{save}" target="_blank" rel="noopener">Save to Pinterest</a>
      </figure>""")
    gossip = ""
    if g.get("gossip"):
        gossip = f"""      <aside class="gossip" aria-label="From the society pages">
        <div class="mast">The Mayfair Murmur</div>
        <div class="date">Society intelligence of a most pressing nature</div>
        <p>{esc(g['gossip'])}</p>
        <span class="sig">Yours in confidence, A Lady Who Notices</span>
      </aside>"""
    faq = "\n".join(f"""        <details><summary>{esc(f['q'])}</summary><p>{esc(f['a'])}</p></details>""" for f in g["faq"])
    others = [o for o in GUIDES if o["slug"] != g["slug"]]
    other_links = "".join(f'<li><a href="../{o["slug"]}/">{esc(o["h1"])}</a></li>' for o in others)
    other_links += f'<li><a href="../{DUKE_SLUG}/">Clean Duke Romance Books</a></li><li><a href="../{XMAS_SLUG}/">Clean Christmas Regency Romance</a></li>'

    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "Article", "headline": g["h1"], "description": g["desc"], "url": url,
             "author": {"@type": "Person", "name": "Emma Velott", "url": SITE + "/"},
             "publisher": {"@type": "Person", "name": "Emma Velott"},
             "dateModified": TODAY, "image": f"{SITE}/covers/{picks[0][0]['slug']}.jpg",
             "mentions": [{"@type": "Book", "name": b["title"], "url": f"{SITE}/{b['slug']}/",
                           "author": {"@type": "Person", "name": "Emma Velott"}} for b, _ in picks]},
            {"@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}}
                for f in g["faq"]]},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Reading Guides", "item": f"{SITE}/{GUIDES_SLUG}/"},
                {"@type": "ListItem", "position": 3, "name": g["h1"], "item": url}]},
        ],
    }
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(g['title'])}</title>
<meta name="description" content="{esc(g['desc'])}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Emma Velott">
<meta property="og:title" content="{esc(g['title'])}">
<meta property="og:description" content="{esc(g['desc'])}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/covers/{picks[0][0]['slug']}.jpg">
<meta name="twitter:card" content="summary_large_image">
{head_assets('../')}
{GUIDE_CSS}
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{site_header('../')}
<main id="main">
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="../">Home</a><span>&#8250;</span><a href="../{GUIDES_SLUG}/">Reading Guides</a><span>&#8250;</span>{esc(g['h1'])}</nav>
  </div>
  <section class="section" style="padding-top:36px">
    <div class="wrap narrow gbody">
      <div class="ghero">
        {ICONS.get(g.get("icon", "fan"), "")}
        <div>
          <span class="kicker">{esc(g['kicker'])}</span>
          <h1 style="font-size:clamp(36px,4.6vw,52px)">{esc(g['h1'])}</h1>
        </div>
      </div>
      <p class="glead" style="margin-top:22px">{esc(g['lead'])}</p>
{gossip}
    </div>
  </section>
  <section class="section tinted" aria-labelledby="picks-title">
    <div class="wrap">
      <div class="section-head"><h2 id="picks-title">{esc(g['books_heading'])}</h2></div>
{chr(10).join(card(b, why) for b, why in picks)}
    </div>
  </section>
  <section class="section">
    <div class="wrap narrow gbody">
{chr(10).join(sections)}
      <div class="faq">
        <h2>Questions readers ask</h2>
{faq}
      </div>
    </div>
  </section>
  <section class="section" style="padding-top:0">
    <div class="wrap narrow">
      {signup_box(g["slug"][:10], "../")}
      <h2 style="font-size:26px;margin:40px 0 10px">More reading guides</h2>
      <ul class="glist">{other_links}</ul>
    </div>
  </section>
</main>
{site_footer('../')}
{TICK_JS}
</body>
</html>
"""


HERO_QUIZ = """      <section class="quiz" aria-labelledby="quiz-title">
        <span class="kicker">A highly scientific diversion</span>
        <h2 id="quiz-title" style="font-size:32px;margin-bottom:6px">Which of Emma's heroes should you marry?</h2>
        <p style="margin:0 0 22px;color:var(--ink-soft)">Four questions. No chaperone. Your mother need never know.</p>
        <form id="heroquiz">
          <fieldset><legend>1. Your ideal evening is spent</legend>
            <label><input type="radio" name="q1" value="r"> by a fire in a very quiet house, reading aloud to someone who pretends not to listen</label>
            <label><input type="radio" name="q1" value="w"> winning an argument at the dinner table</label>
            <label><input type="radio" name="q1" value="s"> snowed in somewhere inconvenient with excellent company</label>
          </fieldset>
          <fieldset><legend>2. A gentleman insults you at a ball. You</legend>
            <label><input type="radio" name="q2" value="r"> throw your champagne, then leave with your head high</label>
            <label><input type="radio" name="q2" value="w"> explain to him, at length and in front of his mother, exactly what is wrong with him</label>
            <label><input type="radio" name="q2" value="s"> laugh, because he is clearly drunk and will be mortified by morning</label>
          </fieldset>
          <fieldset><legend>3. The quality you find most irresistible</legend>
            <label><input type="radio" name="q3" value="r"> a man who has been through the wars and still knows how to be gentle</label>
            <label><input type="radio" name="q3" value="w"> a man who scowls at everyone except you</label>
            <label><input type="radio" name="q3" value="s"> a man who can make you laugh when you are trying very hard to be cross</label>
          </fieldset>
          <fieldset><legend>4. Your wedding, ideally, is</legend>
            <label><input type="radio" name="q4" value="r"> small, at a house nobody has visited in years</label>
            <label><input type="radio" name="q4" value="w"> sensible, practical, and secretly the most romantic thing that has ever happened</label>
            <label><input type="radio" name="q4" value="s"> already announced to an innkeeper before anyone has actually proposed</label>
          </fieldset>
          <button class="btn btn-primary" type="submit">Reveal my fate</button>
        </form>
        <div class="result" id="quiz-r" aria-live="polite"><h3>Ronan Kingsford, Duke of Penwythe</h3><p>You want a man who has shut the world out and a reason to make him open the gates. Ronan has a hand that will not close, a face he will not look at, and four rules that you will have broken by the end of the week. He will pretend to mind.</p><p><a class="btn btn-primary" href="../a-jilted-bride-for-the-battle-scarred-duke/sample/">Read his story free</a></p></div>
        <div class="result" id="quiz-w" aria-live="polite"><h3>Alexander, Duke of Wrenwick</h3><p>You want a cold duke and the pleasure of thawing him. Alexander has frightened off every servant he ever had, eats breakfast alone, and has never once been told off by his own housekeeper. You would be the first.</p><p><a class="btn btn-primary" href="../a-fiery-widow-for-the-cold-duke/sample/">Read his story free</a></p></div>
        <div class="result" id="quiz-s" aria-live="polite"><h3>Simon Cathcart, the rakish viscount</h3><p>You want laughter, mischief and a man who is incapable of mild attachment. Simon will steal your side of the bed, invent your entire courtship on the spot, and declare it the most interesting marriage of his life.</p><p><a class="btn btn-primary" href="../the-rakish-viscounts-pretend-wife/sample/">Read his story free</a></p></div>
      </section>
<script>
document.getElementById('heroquiz').addEventListener('submit',function(e){
  e.preventDefault();var t={r:0,w:0,s:0},f=new FormData(this),n=0;
  f.forEach(function(v){t[v]++;n++});
  if(n<4){document.querySelector('#heroquiz button').textContent='Do answer all four, dear';return;}
  var best=Object.keys(t).sort(function(a,b){return t[b]-t[a]})[0];
  document.querySelectorAll('.quiz .result').forEach(function(r){r.classList.remove('show')});
  var el=document.getElementById('quiz-'+best);el.classList.add('show');el.scrollIntoView({behavior:'smooth',block:'nearest'});
  if(window.fbq)fbq('trackCustom','HeroQuiz',{hero:best});
});
</script>"""


def build_guides_hub():
    url = f"{SITE}/{GUIDES_SLUG}/"
    title = "Clean Regency Romance Reading Guides | Emma Velott"
    desc = "Witty reading guides to clean Regency romance. Books like Bridgerton, Georgette Heyer and Jane Austen, clean authors like Julia Quinn, plus marriage of convenience, scarred heroes and grumpy dukes."
    cards = "\n".join(f"""      <article>
        {ICONS.get(g.get('icon', 'fan'), '')}
        <h2><a href="../{g['slug']}/">{esc(g['h1'])}</a></h2>
        <p>{esc(g['desc'])}</p>
        <a class="more-link" href="../{g['slug']}/">Read the guide</a>
      </article>""" for g in GUIDES)
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "CollectionPage", "name": "Reading Guides", "url": url, "description": desc,
         "mainEntity": {"@type": "ItemList", "itemListElement": [
             {"@type": "ListItem", "position": i + 1, "url": f"{SITE}/{g['slug']}/", "name": g["h1"]} for i, g in enumerate(GUIDES)]}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Reading Guides", "item": url}]}]}
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Emma Velott">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/covers/{BOOKS[0]['slug']}.jpg">
{head_assets('../')}
{GUIDE_CSS}
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{site_header('../')}
<main id="main">
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="../">Home</a><span>&#8250;</span>Reading Guides</nav>
  </div>
  <section class="section" style="padding-top:36px">
    <div class="wrap">
      <div class="section-head">
        <span class="kicker">Find your next Regency romance</span>
        <h1 style="font-size:clamp(36px,4.6vw,52px)">Reading Guides</h1>
        <p>A small and entirely unreliable almanac of the tropes we love best, written with a raised eyebrow and a fresh pot of tea. Pick your poison, or let the quiz below pick it for you.</p>
      </div>
      <div class="ghub">
{cards}
      </div>
{HERO_QUIZ}
    </div>
  </section>
</main>
{site_footer('../')}
</body>
</html>
"""


def build_404():
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Page not found | Emma Velott</title>
<meta name="robots" content="noindex">
{head_assets('/')}
</head>
<body>
{site_header('/')}
<main id="main" class="section" style="text-align:center">
  <div class="wrap narrow">
    <h1 style="font-size:42px;margin-bottom:12px">This page has wandered off</h1>
    <p>Perhaps it eloped. The books, at least, are right where you left them.</p>
    <p style="margin-top:24px"><a class="btn btn-primary" href="/">Back to the books</a></p>
  </div>
</main>
{site_footer('/')}
</body>
</html>
"""


def build_simple(title, h1, body):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | Emma Velott</title>
<meta name="robots" content="noindex">
{head_assets('../')}
</head>
<body>
{site_header('../')}
<main id="main" class="section" style="text-align:center">
  <div class="wrap narrow">
    <h1 style="font-size:clamp(34px,4.4vw,46px);margin-bottom:14px">{h1}</h1>
{body}
    <p style="margin-top:28px"><a class="btn btn-primary" href="../#books">Browse the books</a></p>
  </div>
</main>
{site_footer('../')}
</body>
</html>
"""


def fetch_covers():
    os.makedirs(os.path.join(OUT, "covers"), exist_ok=True)
    for b in BOOKS:
        src = f"/tmp/{b['slug']}.src"
        dst = os.path.join(OUT, "covers", b["slug"] + ".jpg")
        local = os.path.join("covers", b["slug"] + ".jpg")
        if os.path.exists(local):
            src = local  # a cover kept in the repo takes priority over the Gumroad copy
        else:
            subprocess.run(["curl", "-fsSL", "https://public-files.gumroad.com/" + b["gumroad_cover_id"], "-o", src], check=True)
        subprocess.run(["convert", src, "-resize", "500x800^", "-gravity", "center", "-extent", "500x800",
                        "-strip", "-interlace", "Plane", "-sampling-factor", "4:2:0", "-quality", "80", dst], check=True)


def make_thumbs():
    """Square 1000x1000 Gumroad thumbnails (shown at checkout and in the library), served at /thumbs/.
    One per book, plus the-emma-velott-collection.jpg for the bundle."""
    d = os.path.join(OUT, "thumbs")
    os.makedirs(d, exist_ok=True)
    cov = lambda s: os.path.join(OUT, "covers", s + ".jpg")
    bg = ["-size", "1000x1000", "radial-gradient:#3c5c4f-#243a31"]
    shadow = ["(", "+clone", "-background", "black", "-shadow", "60x18+0+14", ")", "+swap",
              "-background", "none", "-layers", "merge", "+repage"]
    try:
        for b in BOOKS:
            subprocess.run(["convert", *bg, "(", cov(b["slug"]), "-resize", "x860", *shadow, ")",
                            "-gravity", "center", "-geometry", "+0-6", "-composite",
                            "-quality", "86", os.path.join(d, b["slug"] + ".jpg")], check=True)
        L, M, R = (cov(s) for s in BUNDLE_COVER_ORDER)
        side = lambda f, deg: ["(", f, "-resize", "x600", "-background", "none", "-rotate", str(deg), *shadow, ")"]
        subprocess.run(["convert", *bg,
                        *side(L, -9), "-gravity", "center", "-geometry", "-250+40", "-composite",
                        *side(R, 9), "-gravity", "center", "-geometry", "+250+40", "-composite",
                        "(", M, "-resize", "x700", *shadow, ")", "-gravity", "center", "-geometry", "+0+0", "-composite",
                        "-quality", "86", os.path.join(d, "the-emma-velott-collection.jpg")], check=True)
    except Exception as e:
        print("thumbnail generation skipped:", e)


def make_icons():
    """PNG/ICO versions of favicon.svg for phones and older browsers."""
    try:
        bg = ["-background", "none"]
        subprocess.run(["convert", *bg, "-density", "600", "favicon.svg", "-resize", "180x180",
                        "-gravity", "center", "-background", "#f8f3e9", "-extent", "180x180",
                        os.path.join(OUT, "apple-touch-icon.png")], check=True)
        subprocess.run(["convert", *bg, "-density", "300", "favicon.svg", "-define",
                        "icon:auto-resize=48,32,16", os.path.join(OUT, "favicon.ico")], check=True)
    except Exception as e:
        print("icon conversion skipped:", e)


def write(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    open(path, "w", encoding="utf-8").write(text)


def main():
    os.makedirs(OUT, exist_ok=True)
    if not os.environ.get("SKIP_COVERS"):
        fetch_covers()
    write(os.path.join(OUT, "index.html"), build_home())
    for b in BOOKS:
        write(os.path.join(OUT, b["slug"], "index.html"), build_book(b))
        if b["slug"] in SAMPLES:
            write(os.path.join(OUT, b["slug"], "sample", "index.html"), build_sample(b))
    write(os.path.join(OUT, DUKE_SLUG, "index.html"), build_duke_page())
    write(os.path.join(OUT, XMAS_SLUG, "index.html"), build_xmas_page())
    for g in GUIDES:
        write(os.path.join(OUT, g["slug"], "index.html"), build_guide(g))
    if GUIDES:
        write(os.path.join(OUT, GUIDES_SLUG, "index.html"), build_guides_hub())
    write(os.path.join(OUT, "404.html"), build_404())
    write(os.path.join(OUT, "thanks", "index.html"), build_simple(
        "Check your inbox", "One last step",
        "    <p>Emma has just sent you a short email. Tap the button inside it to confirm, and you're on the list.</p>\n"
        "    <p>Can't see it? Have a look in your Promotions or Spam folder.</p>"))
    write(os.path.join(OUT, "welcome", "index.html"), build_simple(
        "Welcome", "You're on the list",
        "    <p>Thank you for joining Emma's readers.</p>\n"
        "    <p>If you've read <em>A Jilted Bride for the Battle-Scarred Duke</em>, here is your Christmas gift, one more snowbound night at Penwythe with Ronan and Ariana.</p>\n"
        "    <p><a class=\"btn btn-primary\" href=\"https://dl.bookfunnel.com/hrc14ff4jz\">Download your free epilogue</a></p>\n"
        "    <p style=\"margin-top:28px\">Haven't met them yet? The epilogue takes place after the book ends, so start with the story first.</p>\n"
        "    <p><a class=\"btn\" href=\"../a-jilted-bride-for-the-battle-scarred-duke/\">Get A Jilted Bride for the Battle-Scarred Duke</a></p>"))
    if os.path.isdir("pins"):  # Pinterest pin images, served at /pins/
        shutil.copytree("pins", os.path.join(OUT, "pins"), dirs_exist_ok=True)
    shutil.copy("styles.css", OUT)
    shutil.copy("favicon.svg", OUT)
    js = open("bundle-upsell.js", encoding="utf-8").read()
    for k, v in {"__BUNDLE__": BUNDLE, "__FULL__": f"{BUNDLE_FULL:.2f}", "__PRICE__": f"{BUNDLE_PRICE:.2f}",
                 "__SAVE__": str(BUNDLE_SAVE), "__COVERS__": json.dumps(BUNDLE_COVER_ORDER),
                 "__BOOKS__": json.dumps({x["buy"].rstrip("/").rsplit("/l/", 1)[1]: {"slug": x["slug"], "title": x["title"], "price": float(x["price"])} for x in BOOKS})}.items():
        js = js.replace(k, v)
    write(os.path.join(OUT, "bundle-upsell.js"), js)
    make_icons()
    if not os.environ.get("SKIP_COVERS"):
        make_thumbs()
    urls = [SITE + "/", f"{SITE}/{DUKE_SLUG}/", f"{SITE}/{XMAS_SLUG}/"] + [f"{SITE}/{b['slug']}/" for b in BOOKS] + [f"{SITE}/{b['slug']}/sample/" for b in BOOKS if b["slug"] in SAMPLES] + ([f"{SITE}/{GUIDES_SLUG}/"] if GUIDES else []) + [f"{SITE}/{g['slug']}/" for g in GUIDES]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sm += "".join(f"  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in urls)
    sm += "</urlset>\n"
    write(os.path.join(OUT, "sitemap.xml"), sm)
    write(os.path.join(OUT, "robots.txt"), f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    if os.path.exists("CNAME"):
        shutil.copy("CNAME", OUT)
    print("built home +", len(BOOKS), "book pages,", len(REVIEWS), "reviews")


if __name__ == "__main__":
    main()
