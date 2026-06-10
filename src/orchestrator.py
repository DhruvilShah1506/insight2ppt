from .agents.dataset_loader import load_csv
from .agents.insight_extractor import extract_basic_insights
from .agents.llm_adapter import QWEXAdapter
from .agents.ppt_generator import create_presentation
from .models import OrchestratorConfig, PPTSlide
from typing import Optional, Any


def format_details(details: Any) -> str:
    if not details:
        return ""
    if isinstance(details, dict):
        out = []
        for k, v in details.items():
            if isinstance(v, dict):
                out.append(f"{k}:")
                for kk, vv in v.items():
                    out.append(f"- {kk}: {vv}")
            elif isinstance(v, list):
                out.append(f"{k}:")
                for item in v:
                    out.append(f"- {item}")
            else:
                out.append(f"- {k}: {v}")
        return "\n".join(out)
    if isinstance(details, list):
        return "\n".join(f"- {i}" for i in details)
    return str(details)


class CentralOrchestrator:
    def __init__(self, llm_api_key: Optional[str] = None):
        self.llm = QWEXAdapter(api_key=llm_api_key)

    def generate_ppt_from_csv(self, csv_path: str, out_pptx: str, cfg: OrchestratorConfig = OrchestratorConfig()):
        df = load_csv(csv_path)
        insights = extract_basic_insights(df, max_insights=cfg.max_slides)

        slides = []
        for ins in insights:
            # use LLM to polish summary
            polished = self.llm.summarize(ins.title, ins.summary)
            content = polished
            # include short details (formatted)
            if ins.details:
                content += "\n\nDetails:\n" + format_details(ins.details)
            slides.append(PPTSlide(title=ins.title, content=content))

        # Ensure not to exceed max slides
        slides = slides[: cfg.max_slides]
        create_presentation(cfg.title, slides, out_pptx)
        return out_pptx
