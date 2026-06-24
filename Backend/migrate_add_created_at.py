"""Migration: add created_at column to the users table.

Existing rows will be backfilled with the current timestamp so that
the NOT NULL constraint is satisfied without data loss.
"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not set.")
    exit(1)

engine = create_engine(DATABASE_URL)


def migrate():
    with engine.begin() as conn:
        print("Adding created_at to users table...")
        conn.execute(text("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
        """))

        print("Backfilling created_at for existing rows that are NULL...")
        conn.execute(text("""
            UPDATE users SET created_at = NOW() WHERE created_at IS NULL;
        """))

        print("Setting created_at to NOT NULL...")
        conn.execute(text("""
            ALTER TABLE users ALTER COLUMN created_at SET NOT NULL;
        """))

        print("Migration complete!")


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"Migration error: {e}")
