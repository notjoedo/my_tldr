import memdata.tools as tools
from memdata.models import tldr_output

"""
This function will handle the user's query and return a formatted tldr response.
"""
def handle_query(user_query: str) -> str:
    tools.init_database()
    json_text, sources = tools.search_web(user_query)

    tldr_data = tldr_output.model_validate_json(json_text)

    if not tldr_data.sources:
        tldr_data.sources = sources[:3]
    
    tools.save_conversation(user_query, tldr_data.model_dump_json())

    formatted_response = f"""
    Topic: {tldr_data.topic}
    Summary: {tldr_data.summary}
    Key Points: {chr(10).join([f"{i+1}. {point}" for i, point in enumerate(tldr_data.key_points)])}
    Sources: {chr(10).join([f"- {url}" for url in tldr_data.sources])}
    """

    return formatted_response