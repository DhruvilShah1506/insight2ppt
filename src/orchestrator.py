from .ai_orchestrator import AIOrchestrator
from .models import OrchestratorConfig
from typing import Optional


class CentralOrchestrator:
    """Facade orchestrator that delegates to the AI-driven orchestrator.

    This keeps the original single-entrypoint API while using AI-driven
    orchestration to decide which agents to call next.
    """

    def __init__(self, llm_api_key: Optional[str] = None, model: str = "Qwen/Qwen2-7B-Instruct", ollama_base_url: str = "http://localhost:8000"):
        # Default to a local GPU chat server and the Qwen2-7B Instruct model
        self._orch = AIOrchestrator(llm_api_key=llm_api_key, model=model, ollama_base_url=ollama_base_url)

    def generate_ppt_from_csv(self, csv_path: str, out_pptx: str, cfg: OrchestratorConfig = OrchestratorConfig()):
        return self._orch.run(csv_path, out_pptx, cfg)
