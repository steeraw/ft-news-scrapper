from __future__ import annotations
import asyncio
from datetime import datetime, timedelta, timezone
# from typing import Iterable
import httpx
from selectolax.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from tenacity import retry, stop_after_attempt, wait_exponential #, retry_if_exception_type

from app.config import settings
from app.logger import log
from app.parsers.article import parse_article
from app.db.session import SessionLocal
from app.db.models import Article
# from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from app.db.session import SessionLocal

def is_article_link(url: str) -> bool:
    try:
        p = urlparse(url)
        return "/content/" in p.path
    except Exception:
        return False

def extract_article_links(base_url: str, html: str) -> list[str]:
    parser = HTMLParser(html)
    links = set()
    for a in parser.css("a"):
        href = a.attributes.get("href")
        if not href:
            continue
        abs_url = urljoin(base_url, href)
        if is_article_link(abs_url):
            links.add(abs_url)
    return list(links)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10), reraise=True)
async def fetch(client: httpx.AsyncClient, url: str) -> str:
    r = await client.get(url)
    r.raise_for_status()
    return r.text

async def save_article(session, data) -> bool:
    # skip paywalled
    if getattr(data, "is_paywalled", False):
        log.info("skipped", reason="paywalled", url=data.url)
        return False

    row = Article(
        url=data.url,
        title=data.title,
        content=data.content,
        author=data.author,
        published_at=data.published_at,
        subtitle=data.subtitle,
        tags=data.tags,
        image_url=data.image_url,
        word_count=data.word_count,
        reading_time=data.reading_time,
        related_articles=data.related_articles,
    )
    session.add(row)
    try:
        await session.commit()
        log.info("article saved", url=data.url)
        return True
    except IntegrityError:
        await session.rollback()
        log.info("article duplicate", url=data.url)
        return False

async def crawl_once(bootstrap: bool = False, since_hours: int = 1, max_pages: int = 10):
    headers = {"user-agent": settings.USER_AGENT, "accept": "text/html,application/xhtml+xml"}
    async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT, headers=headers, http2=True) as client:
        index_html = await fetch(client, settings.START_URL)
        links = extract_article_links(settings.START_URL, index_html)

        parser = HTMLParser(index_html)
        next_candidates = [a.attributes.get("href") for a in parser.css("a") if a.text().strip().lower() in {"next", "older"}]
        for href in next_candidates[:max_pages-1]:
            if not href: 
                continue
            page_url = urljoin(settings.START_URL, href)
            try:
                html = await fetch(client, page_url)
                links.extend(extract_article_links(page_url, html))
            except Exception as e:
                log.warning("pagination fetch failed", page_url=page_url, error=str(e))

        # de-dup in-memory
        links = list(dict.fromkeys(links))

        log.info("index links collected", count=len(links))

        threshold = datetime.now(timezone.utc) - (timedelta(days=30) if bootstrap else timedelta(hours=since_hours))

        async with SessionLocal() as session:
            saved = 0
            for url in links:
                try:
                    html = await fetch(client, url)
                    data = parse_article(url, html)

                    # time filter
                    if data.published_at and data.published_at < threshold:
                        log.info("article skipped, too_old", url=url, published_at=str(data.published_at), threshold=str(threshold))
                        continue

                    ok = await save_article(session, data)
                    if ok:
                        saved += 1
                except httpx.HTTPStatusError as e:
                    log.warning("article fetch http_error", url=url, status=e.response.status_code)
                except Exception as e:
                    log.warning("article fetch failed", url=url, error=str(e))
            log.info("crawl finished", saved=saved, total=len(links))

async def scheduler_loop():
    # Backfill if database is empty
    async with SessionLocal() as s:
        cnt = (await s.execute(text("select count(*) from articles"))).scalar()
    if not cnt:
        await crawl_once(bootstrap=True)
    # Then hourly
    while True:
        try:
            await crawl_once(bootstrap=False, since_hours=1)
        except Exception as e:
            log.error("scheduler run failed", error=str(e))
        await asyncio.sleep(60 * 60)
