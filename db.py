from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker

DATABASE_URL = "sqlite+aiosqlite:///./rpg.db"

engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,
)

SessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
)
