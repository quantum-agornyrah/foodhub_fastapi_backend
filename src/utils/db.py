from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base
from src.utils.settings import settings

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

#Database creation logics
Base = declarative_base()

#Database connection with pool settings
engine = create_async_engine(
    settings.DB_CONNECTION,
    pool_size=0,          # connections kept open permanently
    max_overflow=0,       # extra connections allowed under load (then wait)
    pool_timeout=30,       # seconds to wait for a connection before error
    # pool_recycle=1800,     # recycle connections every 30 min (prevents stale)
    pool_pre_ping=True,    # test connection before using it (catches dropped conns)

    # Dynamically set echo based on your environment
    # For development, set to True to see SQL queries
    # For production, set to False to hide SQL queries
    # This is a safety measure to prevent SQL injection attacks
    echo=(settings.ENVIRONMENT == "development")
)

# Normal/Basic implementation for slow query response
# LocalSession = sessionmaker(bind=engine)

# def get_db():
#     session = LocalSession()
#     try:
#         yield session
#         # Commit the transaction if no exceptions occurred
#         session.commit()
#     except Exception:
#         # Rollback the transaction if an exception occurred
#         session.rollback()
#         raise
#     finally:
#         session.close()

# Async implementation for fast query response
LocalSession = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with LocalSession() as session:
        try:
            yield session
            # Commit the transaction if no exceptions occurred
            await session.commit()
        except Exception:
            # Rollback the transaction if an exception occurred
            await session.rollback()
            raise
        finally:
            await session.close()


# If a request fails mid-transaction, 
# the session is closed without rollback, 
# leaving the connection in an invalid state for the connection pool.
# And thhats why we add :

# def get_db():
#     ....................
#     try:
#         ................
#         session.commit()
#     except:
#         session.rollback()
#         raise
#     finally:
#         ...............