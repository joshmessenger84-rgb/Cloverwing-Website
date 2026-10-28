#!/usr/bin/env python3
"""Cloverwing Studio site builder.

Reads books.json and writes the whole website into ../dist:
  index.html                the landing page (front of the shop)
  home.html                 the shop interior
  picture-books.html, workbooks.html, colouring-books.html
  <slug>.html               one page per book

To add a book: add an entry to books.json, drop its cover images into
dist/img/covers/, and run this script again. Nothing else needs editing.
"""
import json, shutil
from html import escape as e
from pathlib import Path

SRC = Path(__file__).parent
DIST = SRC.parent / "docs"  # GitHub Pages publishes this folder
DATA = json.loads((SRC / "books.json").read_text(encoding="utf-8"))
SITE = DATA["site"]
BOOKS = [b for b in DATA["books"] if not b.get("hidden")]  # "hidden": true keeps a book off the site
BY_SLUG = {b["slug"]: b for b in BOOKS}

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&amp;family=Karla:wght@300;400;500;600&amp;display=swap">')

CATS = {
    "picture":   dict(page="picture-books.html",   name="Picture Books",   one="Picture book",
                      intro="Stories for reading aloud, with pictures worth lingering over."),
    "workbook":  dict(page="workbooks.html",       name="Workbooks",       one="Workbook", sign="Cloverwing Digital",
                      intro="Workbooks from Cloverwing Digital, our educational imprint. Watch a documentary together, then pick up a pencil. Every subject comes in three editions, so each child in the family gets pages made for their age."),
    "colouring": dict(page="colouring-books.html", name="Colouring Books", one="Colouring book",
                      intro="The artwork from our picture books, drawn again as line art for colouring in. A new one arrives with each new story."),
}
# a section with no visible books is left out of the menu, home page and build
CATS = {k: v for k, v in CATS.items() if any(b["category"] == k for b in BOOKS)}
STORES = {"lulu": "Lulu", "amazon": "Amazon"}
STOREFRONTS_TOP = [("london", "London"), ("kyoto", "Kyoto"), ("new-york", "snowy New York"),
                   ("florence", "Florence"), ("havana", "Havana"), ("istanbul", "Istanbul")]
STOREFRONTS_BOTTOM = [("hoi-an", "Hoi An"), ("sydney", "Sydney"), ("shanghai", "Shanghai"),
                      ("san-francisco", "San Francisco"), ("santorini", "Santorini")]


def of(cat):
    return [b for b in BOOKS if b["category"] == cat]


def available(b):
    return any(b.get("links", {}).get(k) for k in STORES)


def full_title(b):
    return f'{b["title"]} Workbook, Ages {b["age_label"]}' if b["category"] == "workbook" else b["title"]


# ---------- covers ----------
def cover(b, view="front", lazy=True):
    """A real cover image when one is listed in books.json, otherwise a typeset stand-in."""
    src = b.get("covers", {}).get(view)
    alt = {"front": "Front cover", "back": "Back cover", "inside": "Inside pages"}[view] + " of " + full_title(b)
    if src:
        return f'<img class="cover" src="{e(src)}" alt="{e(alt)}"{" loading=lazy" if lazy else ""}>'
    kind = CATS[b["category"]]["one"]
    foot = f'Ages {b["age_label"]}' if b["category"] == "workbook" else "Cover to come"
    long = " long" if len(b["title"]) > 18 else ""
    if view == "front":
        inner = (f'<span class="ph-kind">{e(kind)}</span><span class="ph-title{long}">{e(b["title"])}</span>'
                 f'<span class="ph-foot">{e(foot)}</span>')
        cls = ""
    elif view == "back":
        inner = ('<span class="ph-kind">Back cover</span><span class="ph-title long">Blurb and barcode</span>'
                 '<span class="ph-foot">Image to come</span>')
        cls = ""
    else:
        inner = ('<span class="ph-kind">Inside pages</span><span class="ph-title">A spread from the book</span>'
                 '<span class="ph-foot">Image to come</span>')
        cls = " wide"
    return (f'<span class="cover ph{cls} tone-{e(b.get("tone", "blush"))}" style="--ar:{e(b.get("aspect", "4 / 5"))}" '
            f'role="img" aria-label="{e(alt)} (placeholder)">{inner}</span>')


# ---------- shared chrome ----------
def head_bar(current=""):
    links = [(c["page"], c["name"]) for c in CATS.values()] + [("home.html#about", "About")]
    nav = "".join(f'<a href="{h}"{" aria-current=page" if h == current else ""}>{e(n)}</a>' for h, n in links)
    return (f'<header class="site-head"><div class="wrap">'
            f'<a class="brand" href="home.html" aria-label="Cloverwing Studio, home"><img class="wordmark" src="img/logo-gold.webp" alt="Cloverwing Studio" width="1400" height="489">'
            f'<img src="img/clover-mark.webp" alt="" width="650" height="460"></a>'
            f'<nav class="nav" aria-label="Sections">{nav}</nav></div></header>')


def foot_bar():
    links = [(c["page"], c["name"]) for c in CATS.values()] + [("home.html#about", "About")]
    if SITE.get("instagram"):
        links.append((SITE["instagram"], "Instagram @cloverwing_studio"))
    if SITE.get("lulu_store"):
        links.append((SITE["lulu_store"], "Our Lulu store"))
    if SITE.get("amazon_store"):
        links.append((SITE["amazon_store"], "Our Amazon page"))
    nav = "".join(f'<a href="{e(h)}">{e(n)}</a>' for h, n in links)
    mail = f' &middot; {e(SITE["email"])}' if SITE.get("email") else ""
    return (f'<footer class="site-foot"><div class="wrap">'
            f'<div class="foot-brand"><img src="img/clover-stamp.webp" alt="" width="276" height="300">'
            f'<div><img class="wordmark" src="img/logo-gold.webp" alt="Cloverwing Studio" width="1400" height="489"><span>{e(SITE["tagline"])}</span></div></div>'
            f'<nav class="foot-nav" aria-label="Footer">{nav}</nav>'
            f'<p class="fine">&copy; {SITE["year"]} Cloverwing Studio{mail}. Our books are printed to order and sold through Lulu and Amazon.</p>'
            f'</div></footer>')


def sign(text, tag="h2"):
    return f'<{tag} class="sign"><img src="img/clover-line-gold.webp" alt="" width="147" height="160">{e(text)}</{tag}>'


def document(title, desc, body, fragment=False):
    head = (f'<title>{e(title)}</title><meta name="description" content="{e(desc)}">'
            f'<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">'
            f'<meta property="og:type" content="website">'
            f'<link rel="icon" type="image/png" href="img/favicon.png">{FONTS}<link rel="stylesheet" href="site.css">')
    tail = '<script src="site.js" defer></script>'
    if fragment:  # the artifact preview wraps the page in its own <html>/<body>
        return f"{head}\n{body}\n{tail}\n"
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
            f'{head}</head><body>\n{body}\n{tail}\n</body></html>\n')


# ---------- shelf items ----------
def shelf_item(b, caption=None, tag=True):
    cap = caption if caption is not None else b.get("short", "")
    soon = '' if available(b) or not tag else '<span class="tag">Coming soon</span>'
    data = f' data-age="{b["age"]}" data-topic="{b["topic"]}"' if b["category"] == "workbook" else ""
    return (f'<li class="book"{data}><a class="stand" href="{b["slug"]}.html" tabindex="-1" aria-hidden="true">{cover(b)}</a>'
            f'<div class="cap">{soon}<h3><a href="{b["slug"]}.html">{e(b["title"])}</a></h3>'
            f'{f"<p>{e(cap)}</p>" if cap else ""}</div></li>')


def topic_item(topic_books):
    """Home page: one card per workbook subject, with a chip for each age edition."""
    b = topic_books[0]
    chips = "".join(f'<a class="chip" href="{x["slug"]}.html" aria-label="{e(x["topic_name"])} workbook, ages {e(x["age_label"])}">{e(x["age_label"])}</a>'
                    for x in topic_books)
    soon = '' if any(available(x) for x in topic_books) else '<span class="tag">Coming soon</span>'
    stand_in = dict(b, title=b["topic_name"], age_label="6 to 16")
    return (f'<li class="book"><a class="stand" href="workbooks.html#{b["topic"]}" tabindex="-1" aria-hidden="true">{cover(stand_in)}</a>'
            f'<div class="cap">{soon}<h3><a href="workbooks.html#{b["topic"]}">{e(b["topic_name"])}</a></h3>'
            f'<div class="ages" aria-label="Age editions">{chips}</div></div></li>')


def topics():
    seen = {}
    for b in of("workbook"):
        seen.setdefault(b["topic"], []).append(b)
    return list(seen.values())


def room(cat, items, big=False):
    c = CATS[cat]
    return (f'<section class="room" id="{cat}"><div class="wrap"><div class="room-head">{sign(c.get("sign", c["name"]))}'
            f'<div class="room-intro"><p>{e(c["intro"])}</p><a class="more" href="{c["page"]}">All {e(c["name"].lower())}</a></div></div>'
            f'<ul class="shelf{" big" if big else ""}">{items}</ul></div></section>')


# ---------- pages ----------
def landing(fragment=False):
    def track(items, cls):
        imgs = "".join(f'<img src="img/storefronts/{s}.webp" alt="Cloverwing Studio in {e(n)}" width="1280" height="853">' for s, n in items)
        dup = "".join(f'<img src="img/storefronts/{s}.webp" alt="" width="1280" height="853" aria-hidden="true">' for s, n in items)
        return f'<div class="track {cls}">{imgs}{dup}</div>'
    body = (f'<div class="landing"><header><div class="est">{e(SITE["est"])}</div>'
            f'<div class="lockup"><h1><img class="wordmark" src="img/logo-gold.webp" alt="Cloverwing Studio" width="1400" height="489"></h1><img src="img/clover-mark.webp" alt="" width="650" height="460"></div>'
            f'<div class="tagline">{e(SITE["tagline"])}</div></header>'
            f'<div class="strip">{track(STOREFRONTS_TOP, "a")}{track(STOREFRONTS_BOTTOM, "b")}'
            f'<div class="door"><a href="home.html">Come inside</a></div></div><div class="floor"></div></div>')
    return document("Cloverwing Studio", "Cloverwing Studio publishes picture books and documentary workbooks for children. Come inside.", body, fragment)


def home():
    welcome = ('<section class="welcome"><div class="wrap"><div>'
               '<p class="eyebrow">Welcome in</p>'
               '<h1>Books to read together, and books to work through.</h1>'
               '<p class="lede">Cloverwing Studio makes picture books and documentary workbooks for children. '
               'Have a look along the shelves. When you find one you like, we will point you to Lulu or Amazon, where it is printed to order and posted to you.</p>'
               '<div class="rooms">' + "".join(f'<a class="more" href="#{k}">{e(c["name"])}</a>' for k, c in CATS.items()) + '</div></div>'
               '<figure><img src="img/storefronts/hoi-an.webp" alt="The Cloverwing Studio shopfront, covered in flowers, on a street in Hoi An" width="1280" height="853">'
               '<figcaption>The shop as we picture it in Hoi An.</figcaption></figure></div></section>')
    about = ('<section class="about" id="about"><div class="wrap"><div>'
             '<p class="eyebrow">About the studio</p><h2>The shop is wherever you are.</h2>'
             '<p>Cloverwing Studio is a small publisher of children&rsquo;s books. We do not have a shop on a real street, '
             'so we painted ourselves into a few of our favourite ones.</p>'
             '<p>Our books are printed one at a time, when you order them. Nothing sits in a warehouse, and nothing is sold on this website.</p>'
             '<ol class="steps"><li>Choose a book from the shelves.</li>'
             '<li>Follow its button to Lulu or Amazon and order there.</li>'
             '<li>Your copy is printed and posted straight to you.</li></ol></div>'
             '<img src="img/storefronts/kyoto.webp" alt="The Cloverwing Studio shopfront on a lantern-lit street in Kyoto" width="1280" height="853" loading="lazy">'
             '</div></section>')
    body = (head_bar() + "<main>" + welcome
            + room("picture", "".join(shelf_item(b) for b in of("picture")), big=True)
            + room("workbook", "".join(topic_item(t) for t in topics()))
            + (room("colouring", "".join(shelf_item(b) for b in of("colouring")), big=True) if "colouring" in CATS else "")
            + about + "</main>" + foot_bar())
    return document("Cloverwing Studio | Picture books and workbooks for children",
                    "Picture books and documentary workbooks for children, printed to order through Lulu and Amazon.", body)


def page_head(cat, extra=""):
    c = CATS[cat]
    return (f'<section class="page-head"><div class="wrap"><p class="crumb"><a href="home.html">Home</a> / {e(c["name"])}</p>'
            f'{sign(c.get("sign", c["name"]), "h1")}<p class="lede">{e(c["intro"])}</p>{extra}</div></section>')


def picture_page():
    rows = ""
    for b in of("picture"):
        soon = "" if available(b) else '<span class="tag">Coming soon</span>'
        rows += (f'<article class="feature"><a class="plinth" href="{b["slug"]}.html" tabindex="-1" aria-hidden="true">{cover(b)}</a>'
                 f'<div>{soon}<h2><a href="{b["slug"]}.html">{e(b["title"])}</a></h2><p class="hook">{e(b["hook"])}</p>'
                 f'<p>{e(b["blurb"][0])}</p><a class="btn alt" href="{b["slug"]}.html">See the book</a></div></article>')
    body = head_bar("picture-books.html") + "<main>" + page_head("picture") + f'<div class="wrap">{rows}</div></main>' + foot_bar()
    return document("Picture Books | Cloverwing Studio", CATS["picture"]["intro"], body)


def workbooks_page():
    wb = of("workbook")
    ages = []
    for b in wb:
        if (b["age"], b["age_label"]) not in ages:
            ages.append((b["age"], b["age_label"]))
    def chips(kind, opts):
        return "".join(f'<button type="button" class="chip" id="f-{kind}-{v}" data-filter="{kind}" data-value="{v}" aria-pressed="{"true" if v == "all" else "false"}">{e(l)}</button>'
                       for v, l in [("all", "All")] + opts)
    filters = (f'<div class="filters"><div class="filter-row"><span>Age</span>{chips("age", ages)}</div>'
               f'<div class="filter-row"><span>Subject</span>{chips("topic", [(t[0]["topic"], t[0]["topic_name"]) for t in topics()])}</div></div>')
    shelf = ('<ul class="shelf" data-filter-shelf>' + "".join(shelf_item(b, caption=f'Ages {b["age_label"]}') for b in wb) + '</ul>'
             '<p class="empty" id="no-match" hidden>No workbook matches both of those yet. Try another age or subject.</p>')
    body = (head_bar("workbooks.html") + "<main>" + page_head("workbook")
            + f'<section class="room"><div class="wrap">{filters}{shelf}</div></section></main>' + foot_bar())
    return document("Workbooks | Cloverwing Studio", CATS["workbook"]["intro"], body)


def colouring_page():
    shelf = '<ul class="shelf big">' + "".join(shelf_item(b) for b in of("colouring")) + '</ul>'
    body = (head_bar("colouring-books.html") + "<main>" + page_head("colouring")
            + f'<section class="room"><div class="wrap">{shelf}</div></section></main>' + foot_bar())
    return document("Colouring Books | Cloverwing Studio", CATS["colouring"]["intro"], body)


def book_page(b):
    c = CATS[b["category"]]
    views = [("front", "Front cover"), ("back", "Back cover"), ("inside", "Inside pages")]
    if b.get("covers"):  # once a book has real images, only offer the views we actually have
        views = [v for v in views if b["covers"].get(v[0])]
    panes = "".join(f'<div data-pane="{v}"{"" if i == 0 else " hidden"}>{cover(b, v, lazy=i > 0)}</div>' for i, (v, _) in enumerate(views))
    thumbs = "".join(f'<button type="button" class="chip" id="view-{v}" data-view="{v}" aria-pressed="{"true" if i == 0 else "false"}">{l}</button>'
                     for i, (v, l) in enumerate(views))
    facts = "".join(f"<dt>{e(k)}</dt><dd>{e(v)}</dd>" for k, v in b.get("facts", {}).items())
    buttons = ""
    for i, (key, name) in enumerate(STORES.items()):
        url = b.get("links", {}).get(key)
        if url:
            buttons += f'<a class="btn{" alt" if i else ""}" href="{e(url)}" target="_blank" rel="noopener">Buy on {name}</a>'
        else:
            buttons += f'<span class="btn soon">Coming soon to {name}</span>'
    note = ("You will finish your order on Lulu or Amazon, in a new tab. They print the book and post it to you."
            if available(b) else "This one is still on its way to the printers. Check back soon.")

    related = []
    if b.get("companion") in BY_SLUG:
        comp = BY_SLUG[b["companion"]]
        label = "Colour the story" if comp["category"] == "colouring" else "Read the story"
        related.append((label, [comp], comp["category"] != "workbook"))
    if b["category"] == "workbook":
        sibs = [x for x in of("workbook") if x["topic"] == b["topic"] and x is not b]
        related.append((f'{b["topic_name"]} for other ages', sibs, False))
        others = [t[0] for t in topics() if t[0]["topic"] != b["topic"]]
        others = [next(x for x in of("workbook") if x["topic"] == o["topic"] and x["age"] == b["age"]) for o in others]
        related.append((f'More workbooks for ages {b["age_label"]}', others, False))
    else:
        others = [x for x in of(b["category"]) if x is not b]
        if others:
            related.append((f'More {c["name"].lower()}', others, True))
    rel_html = ""
    for label, items, big in related:
        cap = (lambda x: f'Ages {x["age_label"]}') if items and items[0]["category"] == "workbook" else (lambda x: x.get("short", ""))
        rel_html += (f'<section class="room"><div class="wrap"><div class="room-head">{sign(label)}</div>'
                     f'<ul class="shelf{" big" if big else ""}">' + "".join(shelf_item(x, caption=cap(x)) for x in items) + '</ul></div></section>')

    sub = f'<p class="eyebrow">Cloverwing Digital &middot; {e(b.get("series", "Workbook"))} &middot; Ages {e(b["age_label"])}</p>' if b["category"] == "workbook" else ""
    body = (head_bar(c["page"]) + '<main><div class="wrap">'
            f'<p class="crumb" style="padding-top:28px"><a href="home.html">Home</a> / <a href="{c["page"]}">{e(c["name"])}</a></p>'
            f'<article class="detail"><div><div class="viewer">{panes}</div>' + (f'<div class="thumbs" role="group" aria-label="Choose a picture">{thumbs}</div>' if len(views) > 1 else "") + '</div>'
            f'<div class="info">{sub}<h1>{e(b["title"])}</h1><p class="hook">{e(b["hook"])}</p>'
            f'<div class="blurb">' + "".join(f"<p>{e(p)}</p>" for p in b["blurb"]) + '</div>'
            f'<dl class="facts">{facts}</dl><div class="buy">{buttons}</div><p class="buy-note">{note}</p></div></article></div>'
            + rel_html + "</main>" + foot_bar())
    return document(f'{full_title(b)} | Cloverwing Studio', b["blurb"][0], body)


def not_found():
    body = (head_bar() + '<main><section class="page-head"><div class="wrap">'
            '<p class="eyebrow">Page not found</p><h1 style="font-size:var(--t-3xl)">This shelf is empty.</h1>'
            '<p class="lede">The page you were looking for has moved or never existed.</p>'
            '<a class="btn" href="home.html">Back to the shop</a></div></section></main>' + foot_bar())
    return document("Page not found | Cloverwing Studio", "This page could not be found.", body).replace(
        '<head>', '<head><base href="/">', 1)


def main():
    DIST.mkdir(exist_ok=True)
    for f in ("site.css", "site.js"):
        shutil.copy(SRC / f, DIST / f)
    pages = {"index.html": landing(), "home.html": home()}
    for key, fn in (("picture", picture_page), ("workbook", workbooks_page), ("colouring", colouring_page)):
        if key in CATS:
            pages[CATS[key]["page"]] = fn()
    images = {}
    for b in BOOKS:
        pages[b["slug"] + ".html"] = book_page(b)
        if b.get("covers", {}).get("front"):
            images[b["slug"] + ".html"] = b["covers"]["front"]
    pages["404.html"] = not_found()
    for old in DIST.glob("*.html"):  # clear pages for books that were removed or hidden
        if old.name not in pages:
            old.unlink()
    base = SITE.get("url", "").rstrip("/")
    for name, html in pages.items():
        if base and name != "404.html":
            url = base + "/" + ("" if name == "index.html" else name)
            share = DIST / "img" / "share" / (name[:-5] + ".jpg")  # JPEG copies: every app can show these
            img = base + "/" + ("img/share/" + share.name if share.exists() else "img/share/cloverwing-studio.jpg")
            html = html.replace('<meta property="og:type" content="website">',
                                f'<meta property="og:type" content="website"><link rel="canonical" href="{url}">'
                                f'<meta property="og:url" content="{url}"><meta property="og:image" content="{img}">'
                                '<meta name="twitter:card" content="summary_large_image">', 1)
        (DIST / name).write_text(html, encoding="utf-8")
    if base:  # files the live host needs
        host = base.split("://", 1)[-1]
        (DIST / "CNAME").write_text(host + "\n", encoding="utf-8")
        (DIST / ".nojekyll").write_text("", encoding="utf-8")
        (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n", encoding="utf-8")
        locs = "".join(f"<url><loc>{base}/{'' if n == 'index.html' else n}</loc></url>" for n in pages if n != "404.html")
        (DIST / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
                                          f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{locs}</urlset>\n', encoding="utf-8")
    # the same landing page, without the outer <html> wrapper, for the Claude preview
    prev = SRC.parent / "preview"
    prev.mkdir(exist_ok=True)
    (prev / "cloverwing-studio.html").write_text(landing(fragment=True), encoding="utf-8")
    print(f"Built {len(pages)} pages into {DIST}")


if __name__ == "__main__":
    main()
