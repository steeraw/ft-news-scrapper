import asyncio
import typer
from app.db.init_db import init_db
from app.crawler import crawl_once, scheduler_loop

app = typer.Typer(no_args_is_help=True, add_completion=False)

@app.command("init-db")
def init_db():
    """Create tables"""
    asyncio.run(init_db())

@app.command("crawl")
def crawl(bootstrap: bool = typer.Option(False, help="Backfill up to 30 days"),
          since_hours: int = typer.Option(1, help="For non-bootstrap, look back this many hours")):
    asyncio.run(crawl_once(bootstrap=bootstrap, since_hours=since_hours))

@app.command("schedule")
def schedule():
    asyncio.run(scheduler_loop())

if __name__ == "__main__":
    app()
