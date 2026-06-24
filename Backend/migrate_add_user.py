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
        print("Dropping existing users table if any...")
        conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        
        print("Creating users table...")
        conn.execute(text("""
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL,
                email VARCHAR NOT NULL UNIQUE,
                password_hash VARCHAR NOT NULL,
                last_email_fetched TIMESTAMP WITH TIME ZONE,
                google_access_token VARCHAR,
                google_refresh_token VARCHAR
            );
            CREATE INDEX ix_users_id ON users (id);
            CREATE INDEX ix_users_email ON users (email);
        """))

        print("Adding user_id to emails...")
        conn.execute(text("""
            ALTER TABLE emails ADD COLUMN IF NOT EXISTS user_id INTEGER;
        """))
        
        print("Adding user_id to email_snippets...")
        conn.execute(text("""
            ALTER TABLE email_snippets ADD COLUMN IF NOT EXISTS user_id INTEGER;
        """))

        print("Checking if default user exists...")
        result = conn.execute(text("SELECT id FROM users WHERE email = 'default@example.com'")).fetchone()
        if not result:
            print("Creating default user...")
            conn.execute(text("""
                INSERT INTO users (name, email, password_hash) 
                VALUES ('Default User', 'default@example.com', 'dummy_hash')
            """))
            result = conn.execute(text("SELECT id FROM users WHERE email = 'default@example.com'")).fetchone()
        
        default_user_id = result[0]
        
        print("Updating existing records to default user_id...")
        conn.execute(text("UPDATE emails SET user_id = :uid WHERE user_id IS NULL"), {"uid": default_user_id})
        conn.execute(text("UPDATE email_snippets SET user_id = :uid WHERE user_id IS NULL"), {"uid": default_user_id})

        print("Altering user_id columns to SET NOT NULL...")
        conn.execute(text("ALTER TABLE emails ALTER COLUMN user_id SET NOT NULL;"))
        conn.execute(text("ALTER TABLE email_snippets ALTER COLUMN user_id SET NOT NULL;"))

        print("Dropping old constraints if any...")
        conn.execute(text("ALTER TABLE emails DROP CONSTRAINT IF EXISTS emails_email_id_key;"))
        conn.execute(text("ALTER TABLE email_snippets DROP CONSTRAINT IF EXISTS email_snippets_email_id_key;"))
        conn.execute(text("ALTER TABLE emails DROP CONSTRAINT IF EXISTS uq_user_email;"))
        conn.execute(text("ALTER TABLE email_snippets DROP CONSTRAINT IF EXISTS uq_user_email_snippet;"))
        conn.execute(text("ALTER TABLE emails DROP CONSTRAINT IF EXISTS fk_emails_user_id;"))
        conn.execute(text("ALTER TABLE email_snippets DROP CONSTRAINT IF EXISTS fk_email_snippets_user_id;"))

        print("Adding composite unique constraints (user_id, email_id)...")
        conn.execute(text("""
            ALTER TABLE emails ADD CONSTRAINT uq_user_email UNIQUE (user_id, email_id);
        """))
        conn.execute(text("""
            ALTER TABLE email_snippets ADD CONSTRAINT uq_user_email_snippet UNIQUE (user_id, email_id);
        """))

        print("Adding foreign keys...")
        conn.execute(text("""
            ALTER TABLE emails ADD CONSTRAINT fk_emails_user_id 
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
        """))
        conn.execute(text("""
            ALTER TABLE email_snippets ADD CONSTRAINT fk_email_snippets_user_id 
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
        """))

        print("Migration complete!")

if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"Migration error: {e}")
