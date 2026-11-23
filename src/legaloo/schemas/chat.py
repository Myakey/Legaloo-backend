from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    # Voice clients want short answers; text clients may not.
    voice_mode: bool = False
