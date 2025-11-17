from datetime import datetime
from google import genai
from google.genai import types
import sqlite3, requests, os, dotenv

# this file will contail util functions for agent

# load env & initialize client
dotenv.load_dotenv()

if not os.getenv("GOOGLE_GEMINI_API_KEY"):
    raise ValueError("GOOGLE_GEMINI_API_KEY is not set")

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

def search_web(user_query: str) -> list[str]:
    # initialize google genai client
    client = genai.Client(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))
    
    grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
    )

    config = types.GenerateContentConfig(
        tools=[grounding_tool]
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=[user_query],
        config=config
    )

    print(response.text)