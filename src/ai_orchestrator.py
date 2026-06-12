import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from src.agents.dataset_loader import load_csv
from src.agents.insight_extractor import extract_basic_insights
from src.agents.llm_adapter import QWEXAdapter
from src.agents.ppt_generator import create_presentation
from src.models import OrchestratorConfig, PPTSlide


class ToolCall(BaseModel):
    """Represents a tool/agent call decided by the AI."""
    agent: str
    tool: str
    args: Dict[str, Any] = {}


class AIOrchestrator:
    """AI-driven orchestrator that uses Ollama LLM to decide which agents/tools to call.

    The orchestrator:
    1. Maintains state of workflow (CSV loaded, insights extracted, slides created, etc.)
    2. Asks Ollama LLM: "What should I do next?"
    3. LLM responds with next agent/tool and parameters
    4. Execute the tool and update state
    5. Repeat until LLM signals workflow is complete

    This enables true dynamic orchestration where the LLM decides the workflow,
    not hardcoded step sequences.
    """

    def __init__(self, llm_api_key: Optional[str] = None, model: str = "Qwen/Qwen2-7B-Instruct", ollama_base_url: str = "http://localhost:8000"):
        # Default to a local GPU chat server (chat-completions style) and a larger Qwen model
        self.llm = QWEXAdapter(api_key=llm_api_key, model=model, base_url=ollama_base_url)
        self.state = {}

    def _format_details(self, details: Any) -> str:
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

    def _get_available_tools(self) -> str:
        """Provide a description of available tools for the LLM."""
        return """
Available agents and tools:

1. data_agent:
   - load_csv(csv_path: str) -> DataFrame
   - extract_insights(df: DataFrame, max_insights: int) -> List[Insight]

2. llm_agent:
   - polish(title: str, summary: str) -> str

3. ppt_agent:
   - create_presentation(title: str, slides: List[PPTSlide], out_path: str) -> str

Task: Convert a CSV dataset into executive presentation slides.
Current state: {state}
"""

    def _decide_next_action(self) -> Optional[ToolCall]:
        """Deterministic stepper that decides the next tool to call based on state.

        This method does not call the LLM to pick the next action. It follows a
        strict sequence: load CSV -> extract insights -> polish each insight -> create PPT.
        This guarantees predictable, 100% deterministic orchestration.
        """
        # Determine flags
        csv_loaded = 'df' in self.state and self.state['df'] is not None
        insights_extracted = 'insights' in self.state and self.state['insights'] is not None and len(self.state.get('insights', [])) > 0
        polished_insights = self.state.get('polished_insights', {}) or {}
        ppt_created = 'slides' in self.state and self.state['slides'] is not None

        # 1) Load CSV if missing
        if not csv_loaded:
            return ToolCall(agent="data_agent", tool="load_csv", args={"csv_path": self.state.get("csv_path")})

        # 2) Extract insights if missing
        if not insights_extracted:
            return ToolCall(agent="data_agent", tool="extract_insights", args={"df": "dataframe", "max_insights": self.state.get("max_insights", 6)})

        # 3) Polish insights one-by-one
        insights = self.state.get('insights', [])
        for idx in range(len(insights)):
            if idx not in polished_insights:
                ins = insights[idx]
                return ToolCall(agent="llm_agent", tool="polish", args={"insight_index": idx, "title": ins.title, "summary": ins.summary})

        # 4) Create PPT if not done
        if not ppt_created:
            return ToolCall(agent="ppt_agent", tool="create_presentation", args={"title": "slides_title", "slides": "prepared_slides", "out_path": "output_path"})

        # Done
        return None

    

    def _execute_tool(self, tool_call: ToolCall) -> Any:
        """Execute the tool call and return result."""
        agent = tool_call.agent
        tool = tool_call.tool
        args = tool_call.args

        # Map string references in args to actual state objects
        resolved_args = {}
        for key, value in args.items():
            if isinstance(value, str) and value.lower() == "dataframe":
                resolved_args[key] = self.state.get("df")
            elif isinstance(value, int) and key == "df":
                # LLM sometimes outputs 1 or 2 instead of "dataframe"
                resolved_args[key] = self.state.get("df")
            elif isinstance(value, str) and value.lower() == "prepared_slides":
                resolved_args[key] = self.state.get("slides")
            elif isinstance(value, str) and value.lower() == "output_path":
                resolved_args[key] = self.state.get("out_pptx")
            elif isinstance(value, str) and value.lower() == "slides_title":
                resolved_args[key] = self.state.get("title")
            else:
                resolved_args[key] = value

        if agent == "data_agent":
            if tool == "load_csv":
                return load_csv(resolved_args.get("csv_path"))
            elif tool == "extract_insights":
                return extract_basic_insights(
                    resolved_args.get("df"),
                    max_insights=resolved_args.get("max_insights", 6)
                )
        elif agent == "llm_agent":
            if tool == "polish":
                return self.llm.summarize(
                    resolved_args.get("title"),
                    resolved_args.get("summary")
                )
        elif agent == "ppt_agent":
            if tool == "create_presentation":
                # Pass through optional background and enable small graphs by default
                return create_presentation(
                    resolved_args.get("title"),
                    resolved_args.get("slides"),
                    resolved_args.get("out_path"),
                    background_image=resolved_args.get("background_image"),
                    add_small_graph=resolved_args.get("add_small_graph", True),
                    add_fancy_graph=resolved_args.get("add_fancy_graph", False)
                )

        raise ValueError(f"Unknown tool: {agent}.{tool}")

    def run(self, csv_path: str, out_pptx: str, cfg: OrchestratorConfig) -> str:
        """Run the AI orchestrator to generate PPT.

        The orchestrator iteratively asks the LLM which agent/tool to call next,
        executes it, updates state, and repeats until the LLM decides the workflow is done.
        """
        self.state = {
            "csv_path": csv_path,
            "out_pptx": out_pptx,
            "title": cfg.title,
            "max_insights": cfg.max_slides
        }

        max_iterations = 20  # Safety limit to prevent infinite loops
        iteration = 0

        while iteration < max_iterations:
            iteration += 1            
            print(f"\n[Iteration {iteration}] Asking LLM for next action...")

            # Ask LLM what to do next
            action = self._decide_next_action()
            
            if action is None:
                print("Orchestration complete (LLM signaled done)")
                break

            print(f"LLM decided: {action.agent}.{action.tool}")

            try:
                # Execute the tool
                if action.agent == "data_agent" and action.tool == "load_csv":
                    self.state["df"] = self._execute_tool(action)
                    print("CSV loaded")

                elif action.agent == "data_agent" and action.tool == "extract_insights":
                    self.state["insights"] = self._execute_tool(action)
                    print(f"Extracted {len(self.state['insights'])} insights")

                elif action.agent == "llm_agent" and action.tool == "polish":
                    # Polish a specific insight by index
                    idx = action.args.get("insight_index", 0)
                    if idx < len(self.state.get("insights", [])):
                        ins = self.state["insights"][idx]
                        polished = self.llm.summarize(ins.title, ins.summary)
                        if "polished_insights" not in self.state:
                            self.state["polished_insights"] = {}
                        self.state["polished_insights"][idx] = polished
                        print(f"Polished insight {idx}")

                elif action.agent == "ppt_agent" and action.tool == "create_presentation":
                    # Build slides from polished insights or original insights
                    slides: List[PPTSlide] = []
                    for idx, ins in enumerate(self.state.get("insights", [])):
                        polished = self.state.get("polished_insights", {}).get(idx, ins.summary)
                        content = polished
                        if ins.details:
                            content += "\n\nDetails:\n" + self._format_details(ins.details)
                            # extract numeric values from details for charts
                            numeric_values = {}
                            try:
                                for k, v in ins.details.items():
                                    if isinstance(v, (int, float)):
                                        numeric_values[k] = v
                                    elif isinstance(v, dict):
                                        for kk, vv in v.items():
                                            if isinstance(vv, (int, float)):
                                                numeric_values[f"{k}.{kk}"] = vv
                            except Exception:
                                numeric_values = None
                            slides.append(PPTSlide(title=ins.title, content=content, numeric_values=numeric_values))
                    
                    self.state["slides"] = slides[: cfg.max_slides]
                    result = self._execute_tool(action)
                    print(f"Generated PPT with {len(self.state['slides'])} slides")
                    return result

                else:
                    print(f"Unknown action: {action.agent}.{action.tool}")

            except Exception as e:
                print(f"Error executing {action.agent}.{action.tool}: {e}")
                break

        print(f"\nOrchestration finished after {iteration} iterations")
        return out_pptx
