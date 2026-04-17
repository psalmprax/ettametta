from pydantic import BaseModel

class PostMetadata(BaseModel):
    title: str
    description: str
    hashtags: list[str]
    cta: str
    best_posting_time: str # ISO format or relative
    platform: str
