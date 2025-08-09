from fastapi import FastAPI, Query
from sqlalchemy import select, desc
from app.db.session import SessionLocal
from app.db.models import Article

app = FastAPI(title="FT Scraper API", version="0.1.0")

@app.get("/articles")
async def list_articles(limit: int = 50, q: str | None = Query(None)):
    async with SessionLocal() as session:
        stmt = select(Article).order_by(desc(Article.published_at)).limit(limit)
        rows = (await session.execute(stmt)).scalars().all()
        def serialize(a: Article):
            return {
                "url": a.url,
                "title": a.title,
                "content": a.content,
                "author": a.author,
                "published_at": a.published_at,
                "scraped_at": a.scraped_at,
                "subtitle": a.subtitle,
                "tags": a.tags,
                "image_url": a.image_url,
                "word_count": a.word_count,
                "reading_time": a.reading_time,
                "related_articles": a.related_articles,
            }
        data = [serialize(a) for a in rows]
        if q:
            data = [d for d in data if q.lower() in d["title"].lower()]
        return {"count": len(data), "items": data}
