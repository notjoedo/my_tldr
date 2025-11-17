from pydantic import BaseModel, Field, ConfigDict
from typing import List

# output model for tldr
class tldr_output(BaseModel):
    """
    Structured TLDR output.

    Enforces structured JSON output from LLM response.
    """
    # model config for pydantic
    model_config = ConfigDict(
        str_to_lower=True, 
        extra="forbid")

    summary: str = Field(
        description="A concise description of the given topic."
    )

    topic: str = Field(
        description="Main topic"
    )
    key_points: List[str] = Field(
        description = "Key points (summaries) from topic"
    )


