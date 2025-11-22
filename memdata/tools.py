from datetime import datetime
from google import genai
from google.genai import types
from dotenv import load_dotenv
from models import tldr_output
import sqlite3, os, json, re

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

# search web and return JSON
# returns JSON string
def search_web(user_query: str) -> str:
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
        "topic": "string (10-30 words)",
        "summary": "string (up to 60 words)",
        "key_points": ["point1", "point2", "point3"]
    }}
    Return ONLY valid JSON, no other text."""

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=[prompt],
        config=config
    )

    if not response.candidates:
        raise ValueError("No candidates found in response")

    text = response.text

    if not text:
        raise ValueError("No text content in response")

    if text.startswith('```'):
        json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', text, re.DOTALL)
        if json_match:
            json_text = json_match.group(1)
        else:
            json_text = text
    else:
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            json_text = text[start:end+1]
        else:
            json_text = text

    try:
        json.loads(json_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON response from API: {str(e)}")

    return json_text

import tools
"""
This function will handle the user's query and return a formatted tldr response.
"""
def handle_query(user_query: str) -> str:
    tools.init_database()
    json_text = tools.search_web(user_query)

    tldr_data = tldr_output.model_validate_json(json_text)
    
    tools.save_conversation(user_query, tldr_data.model_dump_json())

    formatted_response = f"""
    Topic: \n{tldr_data.topic}
    Summary: \n{tldr_data.summary}
    Key Points: \n{chr(10).join([f"{i+1}. {point}" for i, point in enumerate(tldr_data.key_points)])}
    """

    return formatted_response
