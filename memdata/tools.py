from datetime import datetime
import sqlite3
# this file will contail util functions for agent

# creating db
def init_database():
    conn = sqlite3.connect("convo.db")
    cursor = conn.cursor()

    table_creation_query = """
        CREATE TABLE IF NOT EXISTS CONVO (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user_query TEXT,
            tldr_response TEXT
        );
    """

    cursor.execute(table_creation_query)
    conn.commit()
    print("table is ready")
    conn.close()

# inserts new record
def save_conversation(user_query, tldr_response, auto_clean=True):
    conn = sqlite3.connect("convo.db")
    cursor = conn.cursor()
    
    timestamp = datetime.now().isoformat()
    insert_query = """
        INSERT INTO CONVO (timestamp, user_query, tldr_response) VALUES (?, ?, ?)
    """

    cursor.execute(insert_query, (timestamp, user_query, tldr_response))
    conn.commit()

    # clean up old convo
    if auto_clean:
        cursor.execute("SELECT COUNT(*) FROM CONVO")
        count = cursor.fetchone()[0]
        if count > 30: # 30 convos
            cursor.execute("""
            DELETE FROM CONVO
            WHERE id NOT IN(
                SELECT id FROM CONVO
                ORDER BY timestamp DESC
                LIMIT ?
            )
            """, (30,))
        conn.commit()

    conn.close()

# search web
def search_web():
    pass

# send response to user
def send_response():
    pass

init_database()
save_conversation("What is Python?", "Python is a programming language...")