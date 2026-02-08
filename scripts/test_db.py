import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

async def test_connection():
    print(f"Connecting to {settings.DATABASE_URL}")
    try:
        engine = create_async_engine(settings.DATABASE_URL)
        async with engine.connect() as conn:
            print("Connection successful!")
            result = await conn.execute("SELECT 1")
            print(result.scalar())
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
