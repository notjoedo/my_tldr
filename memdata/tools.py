from datetime import datetime
from google import genai
from google.genai import types
from dotenv import load_dotenv
import sqlite3, os, re

"""
This file will contain utility functions for the agent.
"""

# load env & initialize client
load_dotenv()

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

# search web and return JSON with sources
# returns tuple of (JSON string, list of source URLs)
def search_web(user_query: str) -> tuple[str, list[str]]:
    # initialize google genai client
    client = genai.Client(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))

    grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
    )

    config = types.GenerateContentConfig(
        tools=[grounding_tool]
    )

    prompt = f"""Create a TLDR summary for: {user_query}
    Return your response as valid JSON with this exact structure:
    {{
        "topic": "string (3-100 characters)",
        "summary": "string (60-120 characters)",
        "key_points": ["point1", "point2", "point3"],
        "sources": []
    }}
    Return ONLY valid JSON, no other text."""

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=[prompt],
        config=config
    )

    # retrieving URLs from grounding metadata
    text = response.text

    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        json_text = json_match.group(1)
    else:
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            json_text = json_match.group(0)
        else:
            json_text = text

    if not response.candidates:
        raise ValueError("No candidates found in response")

    if not response.candidates[0].grounding_metadata:
        raise ValueError("No grounding metadata found in response")

    supports = response.candidates[0].grounding_metadata.grounding_supports or []
    chunks = response.candidates[0].grounding_metadata.grounding_chunks or []

    sorted_supports = sorted(supports, key=lambda s: s.segment.end_index, reverse=True)

    all_sources = []
    sources = set()

    for support in sorted_supports:
        if support.grounding_chunk_indices:
            for i in support.grounding_chunk_indices:
                if i < len(chunks):
                    chunk = chunks[i]
                    if chunk.web and chunk.web.uri:
                        uri = chunk.web.uri
                        if uri not in sources:
                            sources.add(uri)
                            all_sources.append(uri)

    return json_text, all_sources