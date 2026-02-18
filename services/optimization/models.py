from pydantic import BaseModel
from typing import List

class PostMetadata(BaseModel):
    title: str
    description: str
    hashtags: List[str]
    cta: str
    best_posting_time: str # ISO format or relative
    platform: str
