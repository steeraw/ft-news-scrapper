from app.db.session import engine, Base
from app.logger import log

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("db.initialized")
