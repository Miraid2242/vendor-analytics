# init_db.py
import asyncio
from database import engine, Base
import models  # ensure models are imported so metadata is registered

async def init_db():
    async with engine.begin() as conn:
        # run_sync accepts a sync callable; create_all is sync method
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(init_db())
    print("Database initialized (tables created).")
