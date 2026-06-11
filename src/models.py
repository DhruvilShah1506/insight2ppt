from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class Insight(BaseModel):
    title: str
    summary: str
    details: Dict[str, Any] = {}


class PPTSlide(BaseModel):
    title: str
    content: str
    background_image: Optional[str] = None
    numeric_values: Optional[Dict[str, float]] = None


class OrchestratorConfig(BaseModel):
    title: str = "Executive Insights"
    max_slides: int = 6
