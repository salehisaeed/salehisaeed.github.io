#!/usr/bin/env python3
"""Generate the publication lists from Pubs.bib.

Runs automatically before every `quarto render` (see `pre-render` in
_quarto.yml) and writes two include files:

  _generated/publications.md  full list, grouped by type and year
  _generated/recent.md        the most recent journal papers, for the home page

To update the publication list, replace Pubs.bib with the latest copy of the
CV's Publications.bib and re-render. No third-party packages are needed.
"""

import html
import re
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIB = ROOT / "Pubs.bib"
OUT = ROOT / "_generated"
RECENT_COUNT = 5
HIGHLIGHT_SURNAME = "Salehi"

# DOIs whose resolver target is broken on the publisher's side, mapped to a
# working article page. Pubs.bib is copied from the CV, so fixes go here.
LINK_OVERRIDES = {
    "10.18869/acadpub.jafm.73.241.26311": "https://www.jafmonline.net/article_496.html",
}


# --------------------------------------------------------------------------
# Minimal BibTeX parser (handles nested braces, quoted values, % comments)
# --------------------------------------------------------------------------

def _read_braced(text, i):
    """Return (content, index after closing brace) for text[i] == '{'."""
    depth, j = 1, i + 1
    while depth:
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
        j += 1
    return text[i + 1 : j - 1], j


def parse_bib(text):
    text = re.sub(r"(?m)^\s*%.*$", "", text)
    entries = []
    for m in re.finditer(r"@(\w+)\s*\{", text):
        body, _ = _read_braced(text, m.end() - 1)
        key, _, rest = body.partition(",")
        fields, p = {}, 0
        field_re = re.compile(r"\s*([\w+\-]+)\s*=\s*")
        while True:
            fm = field_re.match(rest, p)
            if not fm:
                break
            name, q = fm.group(1).lower(), fm.end()
            if rest[q] == "{":
                val, q = _read_braced(rest, q)
            elif rest[q] == '"':
                end = rest.index('"', q + 1)
                val, q = rest[q + 1 : end], end + 1
            else:
                end = q
                while end < len(rest) and rest[end] not in ",\n}":
                    end += 1
                val, q = rest[q:end], end
            fields[name] = re.sub(r"\s+", " ", val.strip())
            p = re.compile(r"\s*,?").match(rest, q).end()
        entries.append({"type": m.group(1).lower(), "key": key.strip(), **fields})
    return entries


# --------------------------------------------------------------------------
# LaTeX to plain text
# --------------------------------------------------------------------------

ACCENTS = {"'": "\u0301", "`": "\u0300", '"': "\u0308", "^": "\u0302", "~": "\u0303", "c": "\u0327"}
MATH = [
    (r"\ell_1", "ℓ<sub>1</sub>"),
    (r"\ell", "ℓ"),
    (r"\varepsilon", "ε"),
    (r"\epsilon", "ε"),
    (r"\omega", "ω"),
]


def delatex(s):
    if not s:
        return ""
    import unicodedata

    s = re.sub(r"\\([`'\"^~c])\{?\\?([A-Za-z])\}?",
               lambda m: unicodedata.normalize("NFC", m.group(2) + ACCENTS[m.group(1)]), s)
    s = re.sub(r"\\(?:textbf|textit|emph|mathrm|text)\{([^{}]*)\}", r"\1", s)
    s = html.escape(s, quote=False)
    for tex, out in MATH:
        s = s.replace(tex, out)
    s = re.sub(r"\$([^$]*)\$", lambda m: m.group(1).replace("-", "–"), s)
    s = s.replace("\\&amp;", "&amp;").replace("---", "—").replace("--", "–")
    s = s.replace("{", "").replace("}", "").replace("\\", "")
    return s.strip()


def format_author(name):
    name = delatex(name)
    if "," in name:
        last, first = [p.strip() for p in name.split(",", 1)]
    else:
        parts = name.split()
        last, first = parts[-1], " ".join(parts[:-1])
    initials = " ".join(
        "-".join(sub[0] + "." for sub in part.split("-") if sub)
        for part in first.replace(".", ". ").split()
    )
    return f"{initials} {last}".strip()


def format_authors(entry):
    authors = [a for a in re.split(r"\s+and\s+", entry.get("author", "")) if a.strip()]
    out = []
    for a in authors:
        s = format_author(a)
        if HIGHLIGHT_SURNAME in s:
            s = f'<span class="me">{s}</span>'
        out.append(s)
    if len(out) > 1:
        return ", ".join(out[:-1]) + " and " + out[-1]
    return "".join(out)


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

def is_preprint(e):
    return e["type"] == "article" and (e.get("archiveprefix", "").lower() == "arxiv" or "arxiv.org" in e.get("url", ""))


def link_of(e):
    if e.get("doi"):
        doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", e["doi"].strip("{}"))
        if doi in LINK_OVERRIDES:
            return LINK_OVERRIDES[doi], "Article"
        return f"https://doi.org/{doi}", "DOI"
    if is_preprint(e):
        return e.get("url") or f"https://arxiv.org/abs/{e['eprint']}", "arXiv"
    if e.get("url"):
        return e["url"], "Code" if e["type"] == "software" else "Link"
    return None, None


def pages_of(e):
    return re.sub(r"\s*-+\s*", "–", delatex(e.get("pages", "")))


def venue_of(e):
    t = e["type"]
    if is_preprint(e):
        return f"arXiv preprint arXiv:{e['eprint']}" if e.get("eprint") else "arXiv preprint"
    if t == "article":
        v = f"<em>{delatex(e.get('journal'))}</em>"
        if e.get("volume"):
            v += f", {delatex(e['volume'])}"
            if e.get("number"):
                v += f"({delatex(e['number'])})"
        if e.get("pages"):
            v += f", {pages_of(e)}"
        return v
    if t == "incollection":
        v = f"In <em>{delatex(e.get('booktitle'))}</em>"
        if e.get("publisher"):
            v += f", {delatex(e['publisher'])}"
        if e.get("pages"):
            v += f", pp. {pages_of(e)}"
        return v
    if t == "inproceedings":
        v = f"<em>{delatex(e.get('booktitle'))}</em>"
        if e.get("volume") and e["volume"].isdigit():
            v += f", {e['volume']}"
        if e.get("pages"):
            v += f", {pages_of(e)}"
        return v
    if t == "unpublished":
        return delatex(e.get("addendum", ""))
    if t == "software":
        return delatex(e.get("note", ""))
    return ""


def render_entry(e, show_year=True):
    url, label = link_of(e)
    title = delatex(e.get("title", ""))
    title_html = f'<a href="{html.escape(url)}">{title}</a>' if url else title
    year = f" ({e['year']})" if show_year and e.get("year") else ""
    plain_title = html.escape(re.sub(r"<[^>]+>", "", title))
    links = f' <a class="pub-link" href="{html.escape(url)}" aria-label="{label}: {plain_title}">{label}</a>' if url else ""
    return (
        f'<li class="pub">'
        f'<span class="pub-title">{title_html}</span>'
        f'<span class="pub-authors">{format_authors(e)}</span>'
        f'<span class="pub-venue">{venue_of(e)}{year}{links}</span>'
        f"</li>"
    )


def by_year(entries):
    groups = OrderedDict()
    for e in sorted(entries, key=lambda e: -int(e.get("year", 0) or 0)):
        groups.setdefault(e.get("year", "n.d."), []).append(e)
    return groups


def section(anchor, title, entries, group_years):
    if not entries:
        return ""
    out = [f'<section class="pub-section" id="{anchor}">',
           f'<h2 class="anchored">{title} <span class="pub-count">{len(entries)}</span></h2>']
    if group_years:
        for year, items in by_year(entries).items():
            out.append(f'<div class="pub-year-group"><h3 class="pub-year">{year}</h3><ol class="pub-list">')
            out += [render_entry(e, show_year=False) for e in items]
            out.append("</ol></div>")
    else:
        out.append('<ol class="pub-list">')
        out += [render_entry(e) for e in sorted(entries, key=lambda e: -int(e.get("year", 0) or 0))]
        out.append("</ol>")
    out.append("</section>")
    return "\n".join(out)


def main():
    entries = parse_bib(BIB.read_text(encoding="utf-8"))
    journal = [e for e in entries if e["type"] == "article" and not is_preprint(e)]
    preprints = [e for e in entries if is_preprint(e)]
    chapters = [e for e in entries if e["type"] == "incollection"]
    conf = [e for e in entries if e["type"] == "inproceedings"]
    talks = [e for e in entries if e["type"] == "unpublished"]
    software = [e for e in entries if e["type"] == "software"]

    groups = [
        ("journal-articles", "Journal articles", journal, True),
        ("preprints", "Preprints", preprints, False),
        ("book-chapters", "Book chapters", chapters, False),
        ("conference-papers", "Conference papers", conf, True),
        ("presentations", "Conference presentations", talks, False),
        ("software-datasets", "Software and datasets", software, False),
    ]
    nav = " · ".join(
        f'<a href="#{a}">{t} ({len(es)})</a>' for a, t, es, _ in groups if es
    )
    body = [f'<nav class="pub-nav" aria-label="Publication types">{nav}</nav>']
    body += [section(*g) for g in groups]

    OUT.mkdir(exist_ok=True)
    (OUT / "publications.md").write_text(
        "<!-- Generated by scripts/build_publications.py from Pubs.bib. Do not edit. -->\n\n"
        "```{=html}\n" + "\n".join(b for b in body if b) + "\n```\n",
        encoding="utf-8",
    )

    recent = sorted(journal + preprints, key=lambda e: -int(e.get("year", 0) or 0))[:RECENT_COUNT]
    (OUT / "recent.md").write_text(
        "<!-- Generated by scripts/build_publications.py from Pubs.bib. Do not edit. -->\n\n"
        '```{=html}\n<ol class="pub-list pub-list-compact">\n'
        + "\n".join(render_entry(e) for e in recent)
        + "\n</ol>\n```\n",
        encoding="utf-8",
    )
    print(f"build_publications: {len(journal)} journal, {len(preprints)} preprints, "
          f"{len(chapters)} chapters, {len(conf)} conference papers, {len(talks)} presentations, "
          f"{len(software)} software/datasets")


if __name__ == "__main__":
    main()
