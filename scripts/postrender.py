#!/usr/bin/env python3
"""SEO touch-ups applied to docs/ after every `quarto render`.

Quarto cannot express these directly:
  * a canonical URL and og:url on every page (the home page as "/")
  * the home page <title> with the name first and no site-name suffix
  * the home page hero name as a real <h1> (Quarto hoists a literal <h1>
    into its own title block, so the source uses a placeholder)
  * noindex on redirect stubs and the 404 page
  * "/" instead of "/index.html" in the sitemap

The script is idempotent, so running it on an already processed page is safe.
"""

import re
from pathlib import Path

SITE = "https://saeedsalehi.com"
DOCS = Path(__file__).resolve().parent.parent / "docs"
HOME_TITLE = "Saeed Salehi – Associate Professor of Fluid Mechanics, Linköping University"


def canonical_url(page):
    return f"{SITE}/" if page == "index.html" else f"{SITE}/{page}"


def add_head(html, tag):
    return html if tag in html else html.replace("</head>", f"{tag}\n</head>", 1)


def main():
    for path in sorted(DOCS.glob("*.html")):
        html = path.read_text(encoding="utf-8")
        page = path.name

        redirect = re.search(r'var redirects = \{"":"([^"]+)"\}', html)
        if redirect:
            html = add_head(html, '<meta name="robots" content="noindex">')
            html = add_head(html, f'<link rel="canonical" href="{canonical_url(redirect.group(1))}">')
        elif page == "404.html":
            html = add_head(html, '<meta name="robots" content="noindex">')
        else:
            url = canonical_url(page)
            html = add_head(html, f'<link rel="canonical" href="{url}">')
            html = add_head(html, f'<meta property="og:url" content="{url}">')

        if page == "index.html":
            html = re.sub(r"<title>.*?</title>", f"<title>{HOME_TITLE}</title>", html, count=1, flags=re.S)
            html = re.sub(r'(<meta (?:property="og:title"|name="twitter:title") content=")[^"]*"',
                          rf'\1{HOME_TITLE}"', html)
            html = re.sub(r'<p id="hero-name" class="hero-name" role="heading" aria-level="1">(.*?)</p>',
                          r'<h1 id="hero-name" class="hero-name">\1</h1>', html, count=1)

        path.write_text(html, encoding="utf-8")

    sitemap = DOCS / "sitemap.xml"
    if sitemap.exists():
        text = sitemap.read_text(encoding="utf-8")
        sitemap.write_text(text.replace(f"<loc>{SITE}/index.html</loc>", f"<loc>{SITE}/</loc>"), encoding="utf-8")


if __name__ == "__main__":
    main()
