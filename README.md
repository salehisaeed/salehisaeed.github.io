# saeedsalehi.com

Source of my academic website, built with [Quarto](https://quarto.org) and served by GitHub Pages from the `docs/` folder (custom domain in `CNAME`).

## Build and preview

```bash
quarto preview        # live preview while editing
quarto render         # full build into docs/, then commit docs/ together with the sources
```

Rendering first runs `scripts/build_publications.py` (plain Python 3, no packages), which turns `Pubs.bib` into `_generated/publications.md` and `_generated/recent.md`.

## Common updates

| What | Where |
|---|---|
| Publications | Replace `Pubs.bib` with the CV's `Publications.bib` and re-render. The publication page and the home page's recent list update automatically. If a DOI stops resolving on the publisher's side, add a working URL to `LINK_OVERRIDES` in `scripts/build_publications.py`. |
| News | `index.qmd`, the `news-list` block. Keep about 6–8 dated items. |
| Research themes | `research.qmd`. The home page cards in `index.qmd` link to its anchors. |
| Teaching, supervision | `teaching.qmd` |
| CV summary | `cv.qmd`. The full PDF is linked from the CV repository. |
| Openings, thesis proposals | `opportunities.qmd`, PDFs in `files/` |
| Profile links | `_includes/profile-links.md`, used on the home and contact pages |
| Structured data | `_includes/jsonld.html` |
| Styling | `theme.scss` (light) and `theme-dark.scss` (dark overrides) |

## Images

Put web-ready images in `img/`: WebP or JPEG, no wider than about 1600 px, on a white background so figures stay legible in dark mode.

Old addresses of removed pages (`drl.html`, `uq.html`, …) redirect to `research.html` through `aliases` in `research.qmd`.
