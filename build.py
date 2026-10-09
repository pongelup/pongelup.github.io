"""Build the static site for leandropongeluppe.com.

Reads   data/*.yml      (site settings, news, publications, working papers, media)
        News (data/news.yml) and media (data/media.yml) are merged into one dated list, newest first,
        deduplicated by URL; it is shown on Practice & Media (/extension/#news). Home shows the 3 most recent items
        about different papers (optional "paper:" key; untagged items count as their own, see home_news).
        /news/ is a small redirect page to /extension/#news.
        content/*.yml   (free text for each page)
        templates/*.html (Jinja2 templates)
Writes  index.html, home/index.html, news/index.html, cv/index.html, research/index.html, teaching/index.html,
        extension/index.html, cia-framework/index.html, personal/index.html, 404.html

Usage:
    python build.py          build every page, then check internal links
    python build.py --check  only check internal links of the already built pages

Requires Python 3.9+ with PyYAML and Jinja2 (pip install pyyaml jinja2).
"""
import re
import sys
from urllib.parse import parse_qs, urlparse
from html.parser import HTMLParser
from pathlib import Path

try:
    import yaml
    from jinja2 import ChainableUndefined, Environment, FileSystemLoader
    from markupsafe import escape
except ImportError:
    sys.exit("Missing packages. Run:  python -m pip install pyyaml jinja2")

ROOT = Path(__file__).resolve().parent

# Default alt text for the banner photos (the banners are real <img> elements so screen readers get a
# description). A page can override it with "banner_alt:" in its content/<page>.yml.
BANNER_ALT = {
    "banner-favela.jpg": "Panoramic view of a hillside favela in Rio de Janeiro, with mountains and the ocean behind it",
    "banner-mangrove.jpg": "Mangrove forest along a riverbank, with a small house among the trees",
    "banner-rocinha-gavea-drone.jpg": "Aerial drone view of the border between the Rocinha favela and the Gávea neighborhood in Rio de Janeiro: dense rooftops on one side, houses with pools among trees on the other",
    "banner-rocinha-panorama.jpg": "Panoramic view of the Rocinha favela in Rio de Janeiro, with mountains and the ocean behind it",
    "banner-altamira-agroforest.jpg": "Floor of a cacao agroforest near Altamira, Pará, in the Brazilian Amazon, with seedlings among fallen leaves",
    "banner-para-2012-river-rainbow.jpg": "Rainbow over a river lined with mangrove forest in Pará, in the Brazilian Amazon, with a small house at the water's edge",
}

# Photo credits shown on the banner (text, link). A page can override with "banner_credit:" and
# "banner_credit_url:" in its content/<page>.yml.
BANNER_CREDIT = {
    "banner-rocinha-gavea-drone.jpg": ("Photo: Johnny Miller / Unequal Scenes", "https://unequalscenes.com"),
}

# page key -> (template, output paths relative to ROOT, canonical path)
PAGES = {
    "home": ("home.html", ["index.html", "home/index.html"], "/"),
    "news": ("news.html", ["news/index.html"], "/news/"),  # redirect to /extension/#news
    "cv": ("cv.html", ["cv/index.html"], "/cv/"),
    "research": ("research.html", ["research/index.html"], "/research/"),
    "teaching": ("teaching.html", ["teaching/index.html"], "/teaching/"),
    "extension": ("extension.html", ["extension/index.html"], "/extension/"),
    "cia-framework": ("cia-framework.html", ["cia-framework/index.html"], "/cia-framework/"),
    "personal": ("personal.html", ["personal/index.html"], "/personal/"),
    "404": ("404.html", ["404.html"], "/404.html"),
}


def load(path):
    with open(ROOT / path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

MONTHS_EN = ["january", "february", "march", "april", "may", "june", "july", "august", "september",
             "october", "november", "december"]
MONTHS_PT = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro",
             "outubro", "novembro", "dezembro"]
SEASONS = {"spring": 4, "summer": 7, "fall": 10, "autumn": 10, "winter": 12}


def month_num(word):
    w = word.lower()
    if w in MONTHS_EN:
        return MONTHS_EN.index(w) + 1
    if w in MONTHS_PT:
        return MONTHS_PT.index(w) + 1
    return None


def parse_date(text):
    """Turn a date as written in news.yml or media.yml into (sort key, English display text).

    Accepts "May 2026", "April 30th, 2026.", "24 de setembro de 2024.", "Janeiro de 2021.", "2026",
    and seasons such as "Fall/Winter, 2022.". Unknown days sort after known days of the same month.
    """
    t = str(text).strip().rstrip(".").strip()
    low = t.lower()
    m = re.match(r"^(\d{1,2}) de (\w+)(?: de)? (\d{4})$", low)                      # 24 de setembro de 2024
    if m and month_num(m.group(2)):
        y, mo, d = int(m.group(3)), month_num(m.group(2)), int(m.group(1))
        return (y, mo, d), f"{MONTHS_EN[mo - 1].title()} {y}"
    m = re.match(r"^(\w+) (\d{1,2})(?:st|nd|rd|th)?,? (\d{4})$", low)                 # April 30th, 2026
    if m and month_num(m.group(1)):
        y, mo, d = int(m.group(3)), month_num(m.group(1)), int(m.group(2))
        return (y, mo, d), f"{MONTHS_EN[mo - 1].title()} {y}"
    m = re.match(r"^(\w+)(?: de|,)? (\d{4})$", low)                                   # May 2026, Janeiro de 2021
    if m and month_num(m.group(1)):
        y, mo = int(m.group(2)), month_num(m.group(1))
        return (y, mo, 0), f"{MONTHS_EN[mo - 1].title()} {y}"
    m = re.match(r"^([a-z/]+),? (\d{4})$", low)                                       # Fall/Winter, 2022
    if m and all(p in SEASONS for p in m.group(1).split("/")):
        y = int(m.group(2))
        return (y, SEASONS[m.group(1).split("/")[0]], 0), f"{t.split(',')[0].split(' ')[0].title()} {y}"
    m = re.match(r"^(\d{4})$", low)                                                   # 2026
    if m:
        return (int(m.group(1)), 0, 0), m.group(1)
    raise ValueError(f"Cannot read the date {text!r}; use a form like 'May 2026' or 'April 30th, 2026.'")


def url_key(url):
    """Key used to spot the same story in news.yml and media.yml (scheme, www, query, slash ignored)."""
    if not url:
        return None
    u = urlparse(url.strip())
    host = u.netloc.lower().removeprefix("www.").removeprefix("www1.")
    if "youtube.com" in host:
        return "youtube:" + (parse_qs(u.query).get("v") or [u.path])[0]
    return host + u.path.rstrip("/").lower()


def merged_news(news, media):
    """One list of news and media items, newest first, deduplicated by URL (the news.yml text wins)."""
    items, seen = [], {}
    for n in news:
        key, display = parse_date(n["date"])
        html = str(n.get("text", ""))
        if n.get("link"):
            html += f' <a href="{escape(n["link"])}">{escape(n.get("link_text") or "Read more")}</a>'
        item = {"sort": key, "date": display, "html": html, "paper": n.get("paper")}
        k = url_key(n.get("link"))
        if k:
            seen[k] = item
        items.append(item)
    for lang in ("english", "portuguese"):
        for m in media.get(lang) or []:
            key, display = parse_date(m["date"])
            k = url_key(m.get("url"))
            if k and k in seen:
                # Same story already in news.yml: keep that text, but use the more precise media date to sort.
                if key[:2] == seen[k]["sort"][:2] and key[2] > seen[k]["sort"][2]:
                    seen[k]["sort"] = key
                if not seen[k].get("paper"):
                    seen[k]["paper"] = m.get("paper")
                continue
            html = f'<i>{escape(m.get("outlet", ""))}</i> <a href="{escape(m["url"])}">{escape(m["title"])}</a>'
            if m.get("lang") == "pt":
                html += ' <span class="lang-note">(in Portuguese)</span>'
            item = {"sort": key, "date": display, "html": html, "paper": m.get("paper")}
            if k:
                seen[k] = item
            items.append(item)
    items.sort(key=lambda i: i["sort"], reverse=True)  # stable: equal dates keep file order
    return items


def home_news(items, count=3):
    """The newest `count` items about different papers: one item per "paper:" key (the newest one).

    Items without a paper key (talks, podcasts, blog posts) are always treated as unique.
    """
    picked, papers = [], set()
    for item in items:
        paper = str(item.get("paper") or "").strip().lower()
        if paper:
            if paper in papers:
                continue
            papers.add(paper)
        picked.append(item)
        if len(picked) == count:
            break
    return picked


def asset_exists(path):
    """True if a file exists under assets/ (used for optional images such as SDG icons)."""
    return bool(path) and (ROOT / "assets" / str(path).lstrip("/")).is_file()


def build():
    site = load("data/site.yml")
    shared = {
        "site": site,
        "base": site.get("base_path", "") or "",
        "pubs": load("data/publications.yml"),
        "wps": load("data/working_papers.yml"),
        "media": load("data/media.yml"),
    }
    shared["news"] = merged_news(load("data/news.yml").get("items") or [], shared["media"])
    shared["home_news"] = home_news(shared["news"])
    env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=True,
                      undefined=ChainableUndefined,  # optional fields may be missing
                      trim_blocks=True, lstrip_blocks=True)
    env.globals["asset_exists"] = asset_exists
    for key, (tpl, outs, canonical) in PAGES.items():
        page = load(f"content/{key}.yml")
        html = env.get_template(tpl).render(
            page=page, active=key, canonical_path=canonical,
            banner_alt=page.get("banner_alt") or BANNER_ALT.get(page.get("banner", ""), ""),
            banner_credit=(page.get("banner_credit"), page.get("banner_credit_url"))
            if page.get("banner_credit") else BANNER_CREDIT.get(page.get("banner", ""), ("", "")), **shared)
        html = re.sub(r"\n\s*\n+", "\n", html)
        for out in outs:
            dest = ROOT / out
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(html, encoding="utf-8", newline="\n")
            print(f"wrote {out}")


class LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in ("href", "src") and value:
                self.links.append(value)


def check():
    """Verify that every internal link and asset in the built pages resolves to a file in the repo."""
    base = (load("data/site.yml").get("base_path") or "").rstrip("/")
    problems = 0
    for _, (_, outs, _) in PAGES.items():
        for out in outs:
            p = LinkCollector()
            p.feed((ROOT / out).read_text(encoding="utf-8"))
            for link in p.links:
                if re.match(r"^(https?:|mailto:|tel:|#|data:)", link) or link.startswith("//"):
                    continue
                path = link.split("#")[0].split("?")[0]
                if base and path.startswith(base):
                    path = path[len(base):]
                if not path.startswith("/"):
                    path = "/" + str((Path(out).parent / path).as_posix())
                target = ROOT / path.lstrip("/")
                if path.endswith("/"):
                    target = target / "index.html"
                if not target.exists():
                    problems += 1
                    print(f"BROKEN in {out}: {link}")
    print("internal links OK" if problems == 0 else f"{problems} broken internal link(s)")
    return problems


def write_sitemap():
    """sitemap.xml and robots.txt for search engines (Google Search Console)."""
    base = "https://www.leandropongeluppe.com"
    skip = {"news", "404"}  # redirect and error pages are not indexed
    urls = "".join(f"  <url><loc>{base}{canon}</loc></url>\n"
                   for key, (_, _, canon) in PAGES.items() if key not in skip)
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n",
        encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n",
                                     encoding="utf-8")


if __name__ == "__main__":
    if "--check" not in sys.argv:
        build()
        write_sitemap()
    sys.exit(1 if check() else 0)
