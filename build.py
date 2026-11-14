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

def head_assets(prefix):
    return f"""<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='10' fill='%232f4a3f'/%3E%3Ctext x='32' y='43' font-family='Georgia,serif' font-style='italic' font-size='28' fill='%23d8bd85' text-anchor='middle'%3EEV%3C/text%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{prefix}styles.css">"""


def site_header(home):
    return f"""<div class="strip">Ebooks delivered to your inbox in moments<span>&#183;</span>EPUB &amp; PDF<span>&#183;</span>Read on any device</div>
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
      <li><a href="{home}#how">How It Works</a></li>
      <li><a href="https://www.instagram.com/emmavelott/" target="_blank" rel="noopener">Instagram</a></li>
      <li><a href="https://emaanspark835.gumroad.com/" target="_blank" rel="noopener">Shop</a></li>
    </ul>
    <small>&#169; {datetime.date.today().year} Emma Velott. Payments are handled securely by Gumroad, and your ebook is emailed to you right after purchase.</small>
  </div>
</footer>"""


def tropes_html(tropes):
    return "<span>&#183;</span>".join(esc(t) for t in tropes)


def buy_row(b, extra=""):
    return f"""<div class="buy-row">
            <span class="price">${b['price']}</span>
            <a class="btn btn-primary" href="{b['buy']}">Buy the ebook</a>
            <span class="format">EPUB &amp; PDF</span>{extra}
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
             "sameAs": ["https://www.instagram.com/emmavelott/"]},
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
                "bookFormat": "https://schema.org/EBook",
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
          <li><strong>Length</strong>{length}</li>
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


def fetch_covers():
    os.makedirs(os.path.join(OUT, "covers"), exist_ok=True)
    for b in BOOKS:
        src = f"/tmp/{b['slug']}.src"
        dst = os.path.join(OUT, "covers", b["slug"] + ".jpg")
        subprocess.run(["curl", "-fsSL", "https://public-files.gumroad.com/" + b["gumroad_cover_id"], "-o", src], check=True)
        subprocess.run(["convert", src, "-resize", "500x800^", "-gravity", "center", "-extent", "500x800",
                        "-strip", "-interlace", "Plane", "-sampling-factor", "4:2:0", "-quality", "80", dst], check=True)


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
    write(os.path.join(OUT, "404.html"), build_404())
    shutil.copy("styles.css", OUT)
    urls = [SITE + "/"] + [f"{SITE}/{b['slug']}/" for b in BOOKS]
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
