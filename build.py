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
REVIEWS = json.load(open("reviews.json", encoding="utf-8"))
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

# Meta Pixel: PageView on every page, Lead on newsletter signup, InitiateCheckout on any Gumroad buy link.
PIXEL = f"""<script>
!function(f,b,e,v,n,t,s){{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)}};if(!f._fbq)f._fbq=n;
n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}}(window,
document,'script','https://connect.facebook.net/en_US/fbevents.js');
fbq('init','{META_PIXEL_ID}');fbq('track','PageView');
document.addEventListener('click',function(e){{var a=e.target.closest&&e.target.closest('a[href*="gumroad.com/l/"]');if(a)fbq('track','InitiateCheckout',{{content_name:a.href.split('/l/')[1]}});}});
document.addEventListener('submit',function(e){{if(e.target.classList&&e.target.classList.contains('signup'))fbq('track','Lead');}});
</script>
<noscript><img height="1" width="1" style="display:none" alt="" src="https://www.facebook.com/tr?id={META_PIXEL_ID}&ev=PageView&noscript=1"></noscript>"""


def head_assets(prefix):
    return f"""<link rel="icon" href="{prefix}favicon.svg" type="image/svg+xml">
<link rel="icon" href="{prefix}favicon.ico" sizes="32x32">
<link rel="apple-touch-icon" href="{prefix}apple-touch-icon.png">
<meta name="theme-color" content="#7a2e33">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{prefix}styles.css">
<meta name="p:domain_verify" content="dcd450609e6fd7a415d088125b18bd74">
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


def site_header(home):
    return f"""<div class="strip"><a href="{home or './'}#newsletter">Get free bonus epilogues and reader gifts</a><span>&#183;</span>Ebooks delivered in moments<span>&#183;</span>Read on any device</div>
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
    write(os.path.join(OUT, DUKE_SLUG, "index.html"), build_duke_page())
    write(os.path.join(OUT, XMAS_SLUG, "index.html"), build_xmas_page())
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
    shutil.copy("styles.css", OUT)
    shutil.copy("favicon.svg", OUT)
    make_icons()
    urls = [SITE + "/", f"{SITE}/{DUKE_SLUG}/", f"{SITE}/{XMAS_SLUG}/"] + [f"{SITE}/{b['slug']}/" for b in BOOKS]
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
