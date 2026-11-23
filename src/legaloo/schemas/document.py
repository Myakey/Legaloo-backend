from pydantic import BaseModel


class Chunk(BaseModel):
    id: str
    content: str
    source: str
    score: float
