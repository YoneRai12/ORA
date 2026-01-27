import os
import sqlite3

from dotenv import load_dotenv

load_dotenv()

def migrate():
    db_name = os.getenv("ORA_BOT_DB", "ora_bot.db")
    print(f"Migrating database: {db_name}")
    
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # 1. Check existing columns in 'users'
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    
    # 2. Add missing columns
    if "failed_link_attempts" not in columns:
        print("Adding column 'failed_link_attempts' to table 'users'...")
        cursor.execute("ALTER TABLE users ADD COLUMN failed_link_attempts INTEGER DEFAULT 0")
    
    if "link_locked_until" not in columns:
        print("Adding column 'link_locked_until' to table 'users'...")
        cursor.execute("ALTER TABLE users ADD COLUMN link_locked_until DATETIME")
    
    # Check other tables if necessary
    # (Optional: Add more migrations here if more 500s appear)
    
    conn.commit()
    conn.close()
    print("Migration finished successfully.")

if __name__ == "__main__":
    migrate()
