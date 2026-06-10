from typing import Optional


class QWEXAdapter:
    """Adapter for QWEX LLM. If `qwex` isn't installed, falls back to a simple rule-based summarizer.

    Replace internals with actual QWEX SDK calls when available.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def summarize(self, title: str, text: str, max_chars: int = 500) -> str:
        # Placeholder: use simple truncation + heuristic
        if not text:
            return "No content to summarize."
        s = text.strip()
        if len(s) <= max_chars:
            return s
        # Try to cut at sentence boundary
        cut = s[:max_chars].rfind('.')
        if cut > 100:
            return s[:cut+1]
        return s[:max_chars].rsplit(' ', 1)[0] + '...'
