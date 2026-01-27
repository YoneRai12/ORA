import os
import sqlite3


def fix_schema():
    db_name = "ora_bot.db"
    if not os.path.exists(db_name):
        print(f"File {db_name} not found.")
        return

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "discord_user_id" in columns and "id" not in columns:
        print(f"Renaming 'discord_user_id' to 'id' in {db_name}...")
        cursor.execute("ALTER TABLE users RENAME COLUMN discord_user_id TO id")
        conn.commit()

    # Conflict handling: Rename incompatible legacy tables
    for table in ["conversations", "messages"]:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        if cursor.fetchone():
            # Check if it has 'scope' (if so, it's new, don't rename)
            cursor.execute(f"PRAGMA table_info({table})")
            cols = [r[1] for r in cursor.fetchall()]
            if (table == "conversations" and "scope" not in cols) or (table == "messages" and "author" not in cols):
                print(f"Renaming legacy table '{table}' to 'legacy_{table}'...")
                cursor.execute(f"ALTER TABLE {table} RENAME TO legacy_{table}")
                conn.commit()
        
    conn.close()

if __name__ == "__main__":
    fix_schema()
