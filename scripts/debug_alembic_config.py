import sys
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
# sys.path.append('.') # PYTHONPATH handles this
from app.core.config import settings

async def debug_alembic():
    print(f"DEBUG: settings.DATABASE_URL raw: {settings.DATABASE_URL}")
    try:
        engine = create_async_engine(settings.DATABASE_URL)
        print("Engine created.")
        async with engine.connect() as conn:
            print("Connected.")
        print("Connection debug check passed.")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(debug_alembic())
    except Exception as e:
        import traceback
        traceback.print_exc()
