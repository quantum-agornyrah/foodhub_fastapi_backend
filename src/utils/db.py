from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from src.utils.settings import settings

#Database creation logics
Base = declarative_base()

#Database connection with pool settings
engine = create_engine(
    settings.DB_CONNECTION,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,

    # Dynamically set echo based on your environment
    # For development, set to True to see SQL queries
    # For production, set to False to hide SQL queries
    # This is a safety measure to prevent SQL injection attacks
    echo=(settings.ENVIRONMENT == "development")
)

LocalSession = sessionmaker(bind=engine)

def get_db():
    session = LocalSession()
    try:
        yield session
        # Commit the transaction if no exceptions occurred
        session.commit()
    except Exception:
        # Rollback the transaction if an exception occurred
        session.rollback()
        raise
    finally:
        session.close()

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