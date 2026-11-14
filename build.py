"""Builds the Emma Velott site into _site/.

- copies index.html (adding links from the home page to each book page)
- creates one page per book at /<slug>/
- writes robots.txt, sitemap.xml and 404.html

To add a new book: add an entry to BOOKS below, add its cover to the
workflow, and add its card to index.html.
"""
import html, json, os, re, shutil, datetime

SITE = "https://emmavelott.com"
OUT = "_site"
TODAY = datetime.date.today().isoformat()

BOOKS = [
    {
        "slug": "the-rakish-viscounts-pretend-wife",
        "title": "The Rakish Viscount's Pretend Wife",
        "anchor": "rakish-viscount",
        "kicker": "A clean fake-marriage Regency novella",
        "kind": "novella",
        "tropes": ["Fake marriage", "One bed", "Forced proximity", "Snowed in"],
        "meta": "A clean, closed-door Regency novella. A governess and a rake snowed in at a coaching inn agree to pose as husband and wife. Ebook by Emma Velott.",
        "buy": "https://emaanspark835.gumroad.com/l/rakish-viscount-pretend-wife",
        "hook": "“Sir! You are in my bed.”",
        "blurb": [
            "Six years of relentless propriety have kept Delilah Pearce employed, respectable, and entirely alone. Then a snowstorm strands her at a coaching inn, and she climbs the stairs to the room she paid for and finds a stranger sprawled across the mattress, one boot on, snoring like a man trying to expel his own soul.",
            "Simon Cathcart has woken in a great many beds that were not his. This is the first one that arrives with a wife attached, since he apparently announced the imminent arrival of one before the brandy finished with him, and the innkeeper believed every word.",
            "The storm will not lift for days, and a governess caught sharing a room with a rake has no career left to speak of. So Delilah sets her terms. He will play the adequate husband, keep to the left side of the bed, and keep his hands, his remarks, and his eyebrows entirely to himself.",
            "The terms hold rather better than either of them expected. What refuses to hold is everything underneath them.",
            "A clean, closed-door Regency novella about a fake marriage, a snowbound inn, and two people who agreed on the rules long before they understood the cost.",
        ],
    },
    {
        "slug": "a-fiery-widow-for-the-cold-duke",
        "title": "A Fiery Widow for the Cold Duke",
        "anchor": "fiery-widow",
        "kicker": "A clean grumpy-duke Regency romance",
        "kind": "novel",
        "tropes": ["Grumpy duke", "Widow heroine", "Marriage of convenience", "Housekeeper and duke"],
        "meta": "A clean, closed-door Regency romance. A widowed housekeeper refuses to be cowed by the cold Duke of Wrenwick, and an arrangement becomes a marriage. By Emma Velott.",
        "buy": "https://emaanspark835.gumroad.com/l/fiery-widow-cold-duke",
        "hook": "She has run out of patience. He has run out of excuses.",
        "blurb": [
            "Fourteen months of widowhood have left Anastasia Reddington with two rented rooms, a ledger that refuses to balance, and a temper she has swallowed so often it sits in her like a coal that will not go out. When a position at Wrenwick Hall is offered at twice the going rate, she takes it, and she does not ask why nobody else would.",
            "Alexander, Duke of Wrenwick, has emptied his own house. Servants flinch. Footmen leave. The table is laid every morning for a man who never eats at it. He expects the new housekeeper to last a week.",
            "She lasts three days before telling him, to his face, that fear is the most expensive economy he has ever practised.",
            "What begins as a trial becomes an arrangement, and the arrangement becomes a marriage neither of them planned to want. Then a charming young clergyman takes an interest in the new duchess, an old secret surfaces that someone has been saving for years, and Anastasia discovers how much of her husband's coldness was only ever armour.",
            "A clean, closed-door Regency romance with a grumpy duke, a widow who has finally run out of saying nothing, and a hard-won happily ever after.",
        ],
    },
    {
        "slug": "a-jilted-bride-for-the-battle-scarred-duke",
        "title": "A Jilted Bride for the Battle-Scarred Duke",
        "anchor": "jilted-bride",
        "kicker": "A clean slow-burn Regency romance",
        "kind": "novel",
        "tropes": ["Scarred hero", "Jilted bride", "Reclusive duke", "Slow-building love"],
        "meta": "A clean, closed-door Regency romance. A jilted vicar's daughter becomes companion at Penwythe, home of a reclusive, war-scarred duke. By Emma Velott.",
        "buy": "https://emaanspark835.gumroad.com/l/jilted-bride-battle-scarred-duke",
        "hook": "Jilted in a ballroom with three hundred people watching, and the first thing she feels is not heartbreak.",
        "blurb": [
            "Ariana Raye is a vicar's daughter with her father's debts hanging round her neck, and when Lionel Lockhart withdraws from their engagement in the middle of a ball, what rises in her once the shock clears is a clean and unladylike fury. A ruined woman takes what work she can get, which is how she comes to be rattling toward Penwythe in a hired coach while the driver explains that nobody has been past those gates in four years.",
            "Ronan Kingsford, sixth Duke of Penwythe, came back from the war with a hand that will not close, a face he refuses to look at, and four rules that keep him upright. Rise at five. Dress without help. Do not leave the east wing. Do not look in mirrors.",
            "The rules were working perfectly well until a voice started carrying through the plaster.",
            "Hired as companion to the duke's young sister, Ariana has no intention of being anybody's cure. She simply declines to pretend the man does not exist. What grows between them is slow, reluctant and thoroughly inconvenient, and it is very nearly enough, right until the man who jilted her walks back through the door with a use for her after all.",
            "A clean, closed-door Regency romance with a scarred recluse, a heroine who refuses to be made small, and a happily ever after earned the hard way.",
        ],
    },
]

EXTRA_CSS = """<style>
.book h3 a,.mini h3 a{text-decoration:none;color:inherit}
.book h3 a:hover,.mini h3 a:hover{color:var(--claret)}
.more-link{font-size:16px;color:var(--green);text-underline-offset:4px}
.crumbs{font-size:14px;color:var(--ink-soft);padding:22px 0 0}
.crumbs a{color:var(--ink-soft)}
.crumbs span{margin:0 8px}
.bp{padding:40px 0 70px}
.bp-grid{display:grid;grid-template-columns:340px 1fr;gap:60px;align-items:start}
.bp-cover img{box-shadow:0 24px 40px -22px rgba(43,38,34,.6)}
.bp h1{font-size:clamp(36px,4.6vw,52px);margin:0 0 10px}
.hook{font-family:var(--display);font-style:italic;font-size:24px;color:var(--green);margin:18px 0 18px}
.bp .buy-row{margin:22px 0 10px}
.small{font-size:15px;color:var(--ink-soft);margin:0}
.facts{list-style:none;padding:0;margin:26px 0 0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px 28px;font-size:16px}
.facts li strong{display:block;font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--claret)}
.bp-blurb p{margin:0 0 16px;max-width:64ch}
.howmini{background:var(--card);border-radius:8px;padding:26px 30px;margin-top:34px}
.howmini h2{font-size:26px;margin:0 0 10px}
.howmini ol{margin:0;padding-left:20px}
.howmini li{margin:0 0 6px}
.more-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:40px}
.mini{display:grid;grid-template-columns:130px 1fr;gap:24px;align-items:start}
.mini img{box-shadow:0 16px 26px -16px rgba(43,38,34,.55)}
.mini h3{font-size:24px;margin:0 0 8px}
.mini p{margin:0 0 12px;font-size:16px;color:var(--ink-soft)}
@media (max-width:860px){.bp-grid{grid-template-columns:1fr;gap:34px}.bp-cover{max-width:280px}.more-grid{grid-template-columns:1fr}.facts{grid-template-columns:1fr}}
</style>
"""


def esc(s):
    return html.escape(s, quote=True)


def head_assets(index_html):
    """Font links and all <style> blocks from the home page, so every page matches."""
    links = re.findall(r'<link rel="preconnect"[^>]*>|<link href="https://fonts[^>]*>', index_html)
    styles = re.findall(r"<style>.*?</style>", index_html, flags=re.S)
    icon = re.search(r'<link rel="icon"[^>]*>', index_html).group(0)
    return "\n".join([icon] + links + styles) + "\n" + EXTRA_CSS


def site_header(prefix):
    return f"""<div class="strip">Ebooks delivered to your inbox in moments<em>&#10086;</em>EPUB &amp; PDF<em>&#10086;</em>Read on any device</div>
<header class="masthead">
  <div class="wrap">
    <p class="tag">Clean Regency Romance</p>
    <a class="name" href="{prefix}">Emma Velott</a>
  </div>
  <nav class="mainnav" aria-label="Main">
    <ul>
      <li><a href="{prefix}#books">The Books</a></li>
      <li><a href="{prefix}#how">How It Works</a></li>
      <li><a href="{prefix}#indie">A Note from Emma</a></li>
      <li><a href="{prefix}#follow">Follow</a></li>
    </ul>
  </nav>
</header>"""


def site_footer(prefix):
    return f"""<footer>
  <div class="wrap">
    <a class="name" href="{prefix}">Emma Velott</a>
    <ul>
      <li><a href="{prefix}#books">The Books</a></li>
      <li><a href="{prefix}#how">How It Works</a></li>
      <li><a href="https://www.instagram.com/emmavelott/" target="_blank" rel="noopener">Instagram</a></li>
      <li><a href="https://emaanspark835.gumroad.com/" target="_blank" rel="noopener">Shop</a></li>
    </ul>
    <small>&#169; {datetime.date.today().year} Emma Velott. Payments are handled securely by Gumroad, and your ebook is emailed to you right after purchase.</small>
  </div>
</footer>"""


def book_page(b, assets):
    url = f"{SITE}/{b['slug']}/"
    img = f"{SITE}/covers/{b['slug']}.jpg"
    others = [o for o in BOOKS if o["slug"] != b["slug"]]
    length = "Novella" if b["kind"] == "novella" else "Full-length novel"
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Book",
                "@id": url + "#book",
                "name": b["title"],
                "url": url,
                "image": img,
                "description": " ".join(b["blurb"]),
                "author": {"@type": "Person", "name": "Emma Velott", "url": SITE + "/"},
                "genre": ["Regency romance", "Historical romance", "Clean romance"],
                "keywords": ", ".join(["clean Regency romance", "closed-door romance"] + [t.lower() for t in b["tropes"]]),
                "inLanguage": "en",
                "bookFormat": "https://schema.org/EBook",
                "offers": {
                    "@type": "Offer",
                    "price": "3.99",
                    "priceCurrency": "USD",
                    "availability": "https://schema.org/InStock",
                    "url": b["buy"],
                },
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
    tropes = '<span>&#183;</span>'.join(esc(t) for t in b["tropes"])
    blurb = "\n".join(f"<p>{esc(p)}</p>" for p in b["blurb"])
    more = "\n".join(
        f"""<article class="mini">
  <a href="../{o['slug']}/"><img src="../covers/{o['slug']}.jpg" width="500" height="800" loading="lazy" alt="Cover of {esc(o['title'])} by Emma Velott"></a>
  <div>
    <h3><a href="../{o['slug']}/">{esc(o['title'])}</a></h3>
    <p>{esc(o['hook'])}</p>
    <a class="more-link" href="../{o['slug']}/">See the book</a>
  </div>
</article>"""
        for o in others
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(b['title'])} | Clean Regency Romance by Emma Velott</title>
<meta name="description" content="{esc(b['meta'])}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="book">
<meta property="og:site_name" content="Emma Velott">
<meta property="og:title" content="{esc(b['title'])} by Emma Velott">
<meta property="og:description" content="{esc(b['meta'])}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{img}">
<meta property="og:image:alt" content="Cover of {esc(b['title'])} by Emma Velott">
<meta property="book:author" content="Emma Velott">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(b['title'])} by Emma Velott">
<meta name="twitter:description" content="{esc(b['meta'])}">
<meta name="twitter:image" content="{img}">
{assets}
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
      <div class="bp-cover"><img src="../covers/{b['slug']}.jpg" width="500" height="800" alt="Cover of {esc(b['title'])} by Emma Velott"></div>
      <div>
        <p class="kicker">{esc(b['kicker'])}</p>
        <h1>{esc(b['title'])}</h1>
        <p class="tropes">{tropes}</p>
        <div class="buy-row">
          <span class="price">$3.99</span>
          <a class="btn btn-primary" href="{b['buy']}">Buy the ebook</a>
          <span class="format">EPUB &amp; PDF</span>
        </div>
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
  <section class="section tinted" aria-labelledby="more-title">
    <div class="wrap">
      <div class="section-head"><h2 id="more-title">More from Emma Velott</h2></div>
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


def page_404(assets):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Page not found | Emma Velott</title>
<meta name="robots" content="noindex">
{assets}
</head>
<body>
{site_header('/')}
<main id="main" class="section" style="text-align:center">
  <div class="wrap narrow">
    <h1 style="font-size:44px;margin-bottom:12px">This page has wandered off</h1>
    <p>Perhaps it eloped. The books, at least, are right where you left them.</p>
    <p style="margin-top:24px"><a class="btn btn-primary" href="/">Back to the books</a></p>
  </div>
</main>
{site_footer('/')}
</body>
</html>
"""


def link_home_page(index_html):
    """Turn titles and covers on the home page into links to each book page."""
    s = index_html
    for b in BOOKS:
        t = esc(b["title"]).replace("&#x27;", "'")
        s = s.replace(f"<h3>{t}</h3>", f'<h3><a href="{b["slug"]}/">{t}</a></h3>', 1)
        s = re.sub(
            r'(<div class="frame">)(<img src="covers/' + re.escape(b["slug"]) + r'\.jpg"[^>]*>)(</div>)',
            r'\1<a href="' + b["slug"] + r'/">\2</a>\3',
            s,
            count=1,
        )
        s = s.replace(
            f'href="#{b["anchor"]}"><img',
            f'href="{b["slug"]}/"><img',
            1,
        )
        s = re.sub(
            r'(<a class="btn btn-primary" href="' + re.escape(b["buy"]) + r'">Buy the ebook</a>\s*<span class="format">EPUB &amp; PDF</span>)',
            r'\1\n            <a class="more-link" href="' + b["slug"] + r'/">Read more about this book</a>',
            s,
            count=1,
        )
        # structured data on the home page should point at the book's own page
        s = s.replace(
            f'"url":"{b["buy"]}","offers"',
            f'"url":"{SITE}/{b["slug"]}/","image":"{SITE}/covers/{b["slug"]}.jpg","offers"',
            1,
        )
    s = s.replace(
        "<title>Emma Velott | Clean Regency Romance Author</title>",
        "<title>Emma Velott | Clean Regency Romance Books and Ebooks</title>",
        1,
    )
    s = s.replace(
        '<meta name="twitter:card"',
        '<meta property="og:site_name" content="Emma Velott">\n<meta name="twitter:card"',
        1,
    )
    s = s.replace("</head>", EXTRA_CSS + "</head>", 1)
    return s


def main():
    os.makedirs(OUT, exist_ok=True)
    index_html = open("index.html", encoding="utf-8").read()
    assets = head_assets(index_html)
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(link_home_page(index_html))
    for b in BOOKS:
        d = os.path.join(OUT, b["slug"])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(book_page(b, assets))
    open(os.path.join(OUT, "404.html"), "w", encoding="utf-8").write(page_404(assets))
    urls = [SITE + "/"] + [f"{SITE}/{b['slug']}/" for b in BOOKS]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sm += "".join(f"  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in urls)
    sm += "</urlset>\n"
    open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8").write(sm)
    shutil.copy("robots.txt", OUT)
    if os.path.exists("CNAME"):
        shutil.copy("CNAME", OUT)
    print("built", len(BOOKS), "book pages")


if __name__ == "__main__":
    main()
