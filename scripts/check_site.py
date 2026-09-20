#!/usr/bin/env python3
"""Check the built site in docs/ without rendering it.

Run it after `quarto render`, or in CI, where it needs only Python and PyYAML:

    python3 scripts/check_site.py

It fails (exit code 1) on:
  * internal links pointing at a missing file or a missing #anchor
  * images or other assets referenced but not present
  * a content page without exactly one <h1>, a description, a canonical
    URL, a skip link, or with an image lacking alt text, or with a
    skipped heading level
  * generated files in _generated/ that are out of date with respect to
    Pubs.bib or news.yml (that is, a render was forgotten)

External URLs are not checked here: publishers and social networks block
automated requests, so the result would be noisy rather than useful.
"""

import html
import importlib.util
import re
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
problems = []


def fail(where, message):
    problems.append(f"{where}: {message}")


def is_redirect(source):
    return "window.location.replace" in source and len(source) < 2500


def check_links():
    pages = {p.name: p.read_text(encoding="utf-8") for p in DOCS.glob("*.html")}
    for name, source in pages.items():
        for match in re.finditer(r'(?:href|src)="([^"]+)"', source):
            url = html.unescape(match.group(1))
            if url.startswith(("http", "mailto:", "tel:", "javascript:", "data:")):
                continue
            path, _, fragment = url.partition("#")
            path = urllib.parse.unquote(path.split("?")[0])
            target = path.lstrip("/") if path else name
            if path and not (DOCS / target).exists():
                fail(name, f"link to missing file: {url}")
            elif fragment and target.endswith(".html") and target in pages:
                if not re.search(rf'id="{re.escape(fragment)}"', pages[target]):
                    fail(name, f"link to missing anchor: {url}")


def check_pages():
    for path in sorted(DOCS.glob("*.html")):
        source = path.read_text(encoding="utf-8")
        if is_redirect(source):
            continue
        name = path.name
        body = source[source.index("<main"):] if "<main" in source else source
        if len(re.findall(r"<h1\b", body)) != 1:
            fail(name, "expected exactly one <h1>")
        levels = [int(x) for x in re.findall(r"<h([1-6])\b", body)]
        skips = [(a, b) for a, b in zip(levels, levels[1:]) if b > a + 1]
        if skips:
            fail(name, f"heading levels skipped: {skips}")
        for img in re.findall(r"<img\b[^>]*>", body):
            if not re.search(r'\balt="[^"]+"', img):
                fail(name, f"image without alt text: {img[:80]}")
        if 'name="description"' not in source:
            fail(name, "missing meta description")
        if "skip-link" not in source:
            fail(name, "missing skip link")
        if name != "404.html" and 'rel="canonical"' not in source:
            fail(name, "missing canonical URL")


def check_generated():
    """Re-run the generators into a temporary directory and compare."""
    with tempfile.TemporaryDirectory() as tmp:
        for script in ("build_publications.py", "build_news.py"):
            spec = importlib.util.spec_from_file_location(script[:-3], ROOT / "scripts" / script)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.OUT = Path(tmp)
            module.main()
        for produced in sorted(Path(tmp).glob("*.md")):
            committed = ROOT / "_generated" / produced.name
            if not committed.exists():
                fail(produced.name, "generated file is missing from _generated/")
            elif committed.read_text(encoding="utf-8") != produced.read_text(encoding="utf-8"):
                fail(produced.name, "out of date; run `quarto render` and commit _generated/ and docs/")


def main():
    if not DOCS.exists():
        sys.exit("docs/ not found; run `quarto render` first")
    check_links()
    check_pages()
    check_generated()
    pages = sum(1 for p in DOCS.glob("*.html") if not is_redirect(p.read_text(encoding="utf-8")))
    if problems:
        print(f"{len(problems)} problem(s) found in {pages} pages:")
        for problem in problems:
            print("  -", problem)
        sys.exit(1)
    print(f"check_site: {pages} content pages, no problems found")


if __name__ == "__main__":
    main()
