from pydantic import BaseModel
from typing import List, Dict, Any


class Insight(BaseModel):
    title: str
    summary: str
    details: Dict[str, Any] = {}


class PPTSlide(BaseModel):
    title: str
    content: str


class OrchestratorConfig(BaseModel):
    title: str = "Executive Insights"
    max_slides: int = 6
