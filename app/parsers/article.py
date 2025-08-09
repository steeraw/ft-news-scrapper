from __future__ import annotations
from typing import Any
from lxml import html as lxml_html
from readability import Document
import extruct, json
from w3lib.html import get_base_url
from urllib.parse import urljoin
from dataclasses import dataclass
from datetime import datetime, timezone
from app.logger import log

@dataclass
class ArticleData:
    url: str
    title: str
    content: str
    author: str | None
    published_at: datetime | None
    subtitle: str | None = None
    tags: list[str] | None = None
    image_url: str | None = None
    word_count: int | None = None
    reading_time: str | None = None
    related_articles: list[str] | None = None
    is_paywalled: bool = False

def _jsonld(tree: lxml_html.HtmlElement, url: str) -> list[dict[str, Any]]:
    try:
        data = extruct.extract(
            lxml_html.tostring(tree, encoding="unicode"),
            base_url=url,
            syntaxes=["json-ld"],
            errors="ignore",
        )
        return data.get("json-ld", []) or []
    except Exception as e:
        log.warning("jsonld.extract.failed", error=str(e))
        return []

def detect_paywall(tree: lxml_html.HtmlElement, url: str) -> bool:
    # Prefer Schema.org JSON-LD
    for block in _jsonld(tree, url):
        if isinstance(block, dict):
            val = block.get("isAccessibleForFree")
            if isinstance(val, str):
                return val.lower() in ("false", "no")
            if isinstance(val, bool):
                return not val
    # Heuristics: known meta tags, lock icons, etc.
    metas = {m.get("name") or m.get("property"): m.get("content") for m in tree.xpath("//meta[@content]")}
    ft_access = metas.get("ft.access") or metas.get("content_tier") or metas.get("article:content_tier")
    if ft_access and "premium" in ft_access.lower():
        return True
    # Look for "Subscribe" banners (rough heuristic)
    text = "".join(tree.xpath("//body//text()")).lower()
    if "subscribe to read" in text or "subscribe to continue" in text:
        return True
    return False

def parse_article(url: str, html: str) -> ArticleData:
    tree = lxml_html.fromstring(html)
    tree.make_links_absolute(get_base_url(html, url))
    is_paywalled = detect_paywall(tree, url)

    # Title
    title = (tree.xpath("string(//meta[@property='og:title']/@content)") or
             tree.xpath("string(//title)") or "").strip()

    # Subtitle/description
    subtitle = (tree.xpath("string(//meta[@name='description']/@content)") or None)
    # Image
    image_url = (tree.xpath("string(//meta[@property='og:image']/@content)") or None)

    # Author(s)
    author = None
    author_meta = tree.xpath("string(//meta[@name='author']/@content)")
    if author_meta:
        author = author_meta.strip()
    else:
        a = tree.xpath("//a[contains(@href, '/author/')]//text()")
        if a:
            author = ", ".join([t.strip() for t in a if t.strip()])

    # Published time
    published_at = None
    dt = (tree.xpath("string(//meta[@property='article:published_time']/@content)") or
          tree.xpath("string(//time/@datetime)") or "")
    if dt:
        try:
            published_at = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except Exception:
            published_at = None

    # Content via Readability
    try:
        doc = Document(html)
        content_html = doc.summary(html_partial=True)
        content_text = lxml_html.fromstring(content_html).text_content()
    except Exception:
        # fallback: all paragraphs
        content_text = "\n".join([p.text_content().strip() for p in tree.xpath("//p") if p.text_content().strip()])

    # Tags
    tags = [t.strip() for t in tree.xpath("//meta[@property='article:tag']/@content") if t.strip()] or None

    # Related articles (links resembling article URLs)
    links = [a.get("href") for a in tree.xpath("//a[@href]")]
    related = [l for l in links if l and "/content/" in l]
    related = list(dict.fromkeys(related)) or None

    words = len(content_text.split())
    reading_time_min = max(1, round(words / 200)) if words else None
    reading_time = f"{reading_time_min} min" if reading_time_min else None

    return ArticleData(
        url=url,
        title=title or url,
        content=content_text,
        author=author,
        published_at=published_at,
        subtitle=subtitle,
        tags=tags,
        image_url=image_url,
        word_count=words or None,
        reading_time=reading_time,
        related_articles=related,
        is_paywalled=is_paywalled,
    )
