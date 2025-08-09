# FT News Scraper

Async scraper for Financial Times World section.

## Quick start (Docker)
```bash
cp .env.example .env
docker compose up --build
# in another terminal (first run backfill)
docker compose exec app python -m app.cli init-db
# hourly schedule (inside container)
docker compose exec app python -m app.cli schedule
```
