import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def create_db_if_not_exists():
    """
    Connects to the MySQL server and creates the database if it doesn't exist.
    Prevents startup failures when the database schema is missing.
    """
    if not DATABASE_URL:
        return

    # Extract base URL (without DB name) and the DB name itself
    try:
        base_url = DATABASE_URL.rsplit("/", 1)[0]
        db_name = DATABASE_URL.split("/")[-1]
        
        # Create a bootstrap engine to connect to the server
        engine_bootstrap = create_engine(base_url)
        with engine_bootstrap.connect() as conn:
            # Execute CREATE DATABASE outside of a transaction if possible
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {db_name}"))
        engine_bootstrap.dispose()
    except Exception as e:
        print(f"Warning: Could not verify/create database: {e}")

# Standard engine and session setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False)

Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
