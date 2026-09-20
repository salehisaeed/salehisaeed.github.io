# saeedsalehi.com

Source of my academic website, built with [Quarto](https://quarto.org) and served by GitHub Pages from the `docs/` folder (custom domain in `CNAME`).

## Build and preview

```bash
quarto preview        # live preview while editing
quarto render         # full build into docs/, then commit docs/ together with the sources
```

Rendering first runs `scripts/build_publications.py` (plain Python 3), which turns `Pubs.bib` into `_generated/publications.md` and `_generated/recent.md`, and `scripts/build_news.py` (needs PyYAML), which turns `news.yml` into `_generated/news-recent.md` and `_generated/news-all.md`. The generated files are committed, because Quarto resolves includes before the pre-render scripts run. Afterwards `scripts/postrender.py` adds canonical URLs and a skip link, sets the home page title, `<h1>` and structured data, and marks redirect pages `noindex`.

## Common updates

| What | Where |
|---|---|
| Publications | Replace `Pubs.bib` with the CV's `Publications.bib` and re-render. The publication page and the home page's recent list update automatically. If a DOI stops resolving on the publisher's side, add a working URL to `LINK_OVERRIDES` in `scripts/build_publications.py`. |
| News | Add an entry at the top of `news.yml`. The home page shows the latest 5 summaries; the News page shows every item with its details. |
| Research themes | `research.qmd`. The home page cards in `index.qmd` link to its anchors. |
| Teaching, supervision | `teaching.qmd` |
| CV summary | `cv.qmd`. The full PDF is linked from the CV repository. |
| Openings, thesis proposals | `opportunities.qmd`, PDFs in `files/` |
| Profile links | `_includes/profile-links.md`, used on the home and contact pages |
| Structured data (ProfilePage, injected into the home page) | `_includes/jsonld.html` |
| Styling | `theme.scss` (light) and `theme-dark.scss` (dark overrides) |

## Images

Put web-ready images in `img/`: WebP or JPEG, no wider than about 1600 px, on a white background so figures stay legible in dark mode.

The home page cards use dedicated 16:10 crops named `img/card-*.webp` so that each figure fills its card. Schematics are marked `theme-img-contain` in `index.qmd` and are fitted instead of cropped.

Avoid `title-block-style` or `include-in-header` in a single page's front matter: Quarto then compiles a second copy of the theme CSS (about 1 MB) for that page alone. Page-specific header content is injected by `scripts/postrender.py` instead.

Old addresses of removed pages (`drl.html`, `uq.html`, …) redirect to `research.html` through `aliases` in `research.qmd`.
