from pydantic import BaseModel, Field, ConfigDict
from typing import List

STR_MAX_LENGTH = 120
STR_MIN_LENGTH = 60

# output model for tldr
class tldr_output(BaseModel):
    """
    Structured TLDR output.

    Enforces structured JSON output from LLM response.
    """
    # model config for pydantic
    model_config = ConfigDict(
        validate_assignment=True, 
        str_to_lower=True, 
        extra="forbid", 
        frozen=True)

    summary: str = Field(
        min_length=STR_MIN_LENGTH, 
        max_length=STR_MAX_LENGTH,
        description="A concise description of the given topic."
    )

    topic: str = Field(
        min_length=3,
        max_length=100,
        description="Main topic"
    )
    sources: List[str] = Field(
        default=[], # could be default no sources
        description="sources from internet",
        max_length = 3
        )
    key_points: List[str] = Field(
        min_length = 3,
        max_length = 6,
        description = "Key points (summaries) from topic"
    )


