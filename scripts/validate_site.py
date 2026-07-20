#!/usr/bin/env python3
"""Dependency-free structural and internal-link checks for the Jiak static site."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
HTML_FILES = sorted(ROOT.glob("*.html")) + sorted(ROOT.glob("*/index.html"))


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.links: list[str] = []
        self.assets: list[str] = []
        self.images: list[dict[str, str | None]] = []
        self.html_lang: str | None = None
        self.title_count = 0
        self.description_count = 0
        self.h1_count = 0
        self._in_title = False
        self._title_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"] or "")
        if tag == "html":
            self.html_lang = values.get("lang")
        elif tag == "title":
            self.title_count += 1
            self._in_title = True
        elif tag == "meta" and values.get("name", "").lower() == "description":
            if values.get("content", "").strip():
                self.description_count += 1
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "a" and values.get("href"):
            self.links.append(values["href"] or "")
        elif tag == "link" and values.get("href"):
            self.assets.append(values["href"] or "")
        elif tag in {"img", "script"} and values.get("src"):
            self.assets.append(values["src"] or "")
            if tag == "img":
                self.images.append({
                    "src": values.get("src"),
                    "alt": values.get("alt"),
                    "width": values.get("width"),
                    "height": values.get("height"),
                })

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_text.append(data)

    @property
    def title_text(self) -> str:
        return "".join(self._title_text).strip()


def local_target(url: str, source: Path) -> tuple[Path, str] | None:
    parsed = urlsplit(url)
    if parsed.scheme in {"http", "https", "mailto", "tel"} or parsed.netloc:
        return None
    path = unquote(parsed.path)
    if not path:
        target = source
    elif path.startswith("/"):
        target = ROOT / path.lstrip("/")
    else:
        target = source.parent / path
    if path.endswith("/") or target.is_dir():
        target /= "index.html"
    return target.resolve(), unquote(parsed.fragment)


def main() -> int:
    errors: list[str] = []
    parsed_pages: dict[Path, PageParser] = {}

    for page in HTML_FILES:
        parser = PageParser()
        parser.feed(page.read_text(encoding="utf-8"))
        parsed_pages[page.resolve()] = parser
        label = page.relative_to(ROOT)

        if parser.html_lang != "en-GB":
            errors.append(f"{label}: expected html lang=en-GB")
        if parser.title_count != 1 or not parser.title_text:
            errors.append(f"{label}: expected one non-empty title")
        if parser.description_count != 1 and page.name != "404.html":
            errors.append(f"{label}: expected one non-empty meta description")
        if parser.h1_count != 1:
            errors.append(f"{label}: expected exactly one h1, found {parser.h1_count}")
        if len(parser.ids) != len(set(parser.ids)):
            errors.append(f"{label}: duplicate id attribute")
        for image in parser.images:
            if image["alt"] is None:
                errors.append(f"{label}: image {image['src']} has no alt attribute")
            if not image["width"] or not image["height"]:
                errors.append(f"{label}: image {image['src']} needs width and height")

    for page, parser in parsed_pages.items():
        label = page.relative_to(ROOT)
        for url in parser.links + parser.assets:
            target_info = local_target(url, page)
            if target_info is None:
                continue
            target, fragment = target_info
            try:
                target.relative_to(ROOT)
            except ValueError:
                errors.append(f"{label}: local target escapes site root: {url}")
                continue
            if not target.exists():
                errors.append(f"{label}: missing local target {url} -> {target.relative_to(ROOT)}")
                continue
            if fragment and target.suffix == ".html":
                target_parser = parsed_pages.get(target)
                if target_parser is None:
                    target_parser = PageParser()
                    target_parser.feed(target.read_text(encoding="utf-8"))
                if fragment not in target_parser.ids:
                    errors.append(f"{label}: missing fragment #{fragment} in {target.relative_to(ROOT)}")

    try:
        ET.parse(ROOT / "sitemap.xml")
    except (ET.ParseError, OSError) as exc:
        errors.append(f"sitemap.xml: {exc}")

    css = (ROOT / "styles.css").read_text(encoding="utf-8")
    if css.count("{") != css.count("}"):
        errors.append("styles.css: unbalanced braces")
    if "@import" in css or "url(\"http" in css or "url('http" in css:
        errors.append("styles.css: external stylesheet or asset request detected")

    placeholders = sum(
        page.read_text(encoding="utf-8").count("CONTROLLER NAME — REPLACE BEFORE PUBLISHING")
        for page in HTML_FILES
    )

    if errors:
        print("Site validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"Validated {len(HTML_FILES)} HTML pages and all internal links.")
    print(f"Expected controller placeholders still present: {placeholders}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
