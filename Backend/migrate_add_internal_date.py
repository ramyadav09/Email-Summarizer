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
        print("Adding internal_date to email_snippets table...")
        conn.execute(text("""
            ALTER TABLE email_snippets ADD COLUMN IF NOT EXISTS internal_date TIMESTAMP WITH TIME ZONE;
        """))
        print("Migration complete!")

if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"Migration error: {e}")
