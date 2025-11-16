from pydantic import BaseModel

# output model for tldr
class tldr_output(BaseModel):
    summary: str
    topic: str
    sources: list[str]
    key_points: list[str]
