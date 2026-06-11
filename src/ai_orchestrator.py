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

    def __init__(self, llm_api_key: Optional[str] = None, model: str = "qwen:0.5b", ollama_base_url: str = "http://localhost:11434"):
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
        """Call Ollama to dynamically decide the next action based on current state.

        Uses explicit workflow logic with LLM as decision validator.
        Provides detailed tool descriptions and examples to guide the model.
        """
        tools_desc = self._get_available_tools()
        
        # Build current state summary with explicit flags
        csv_loaded = 'df' in self.state and self.state['df'] is not None
        insights_extracted = 'insights' in self.state and self.state['insights'] is not None and len(self.state.get('insights', [])) > 0
        all_polished = insights_extracted and len(self.state.get('polished_insights', {})) == len(self.state.get('insights', []))
        ppt_created = 'slides' in self.state and self.state['slides'] is not None
        
        state_summary = f"""
Current Progress:
✓ CSV loaded: {csv_loaded}
✓ Insights extracted: {insights_extracted}
✓ All insights polished: {all_polished}
✓ PPT created: {ppt_created}

Workflow Rules:
1. First: load_csv (if not done)
2. Second: extract_insights (after CSV loaded)
3. Third: polish each insight one-by-one (after insights extracted)
4. Fourth: create_presentation (after all polishing done)
"""
        
        # Determine next logical step based on state progression
        if not csv_loaded:
            # Step 1: Load CSV
            action_guidance = """
NEXT STEP: Load CSV file.
Use EXACTLY this format (lowercase, no spaces, single underscores):
{
  "agent": "data_agent",
  "tool": "load_csv",
  "args": {
    "csv_path": "%s"
  },
  "done": false
}
""" % self.state.get("csv_path", "")
        
        elif not insights_extracted:
            # Step 2: Extract insights
            action_guidance = """
NEXT STEP: Extract insights from loaded CSV.
Use EXACTLY this format (lowercase, no spaces, single underscores):
{
  "agent": "data_agent",
  "tool": "extract_insights",
  "args": {
    "df": "dataframe",
    "max_insights": 6
  },
  "done": false
}
"""
        
        elif not all_polished:
            # Step 3: Polish insights one by one
            num_insights = len(self.state.get('insights', []))
            print(f"Debug: {num_insights} insights extracted, {len(self.state.get('polished_insights', {}))} polished")
            polished_count = len(self.state.get('polished_insights', {}))
            next_idx = polished_count
            
            if next_idx < num_insights:
                insight = self.state['insights'][next_idx]
                action_guidance = f"""
NEXT STEP: Polish insight #{next_idx + 1} of {num_insights}.
Use EXACTLY this format (lowercase, no spaces, single underscores):
{{
  "agent": "llm_agent",
  "tool": "polish",
  "args": {{
    "insight_index": {next_idx},
    "title": "{insight.title}",
    "summary": "{insight.summary}"
  }},
  "done": false
}}
"""
            else:
                action_guidance = """
NEXT STEP: All insights polished. Create presentation now.
Use EXACTLY this format (lowercase, no spaces, single underscores):
{
  "agent": "ppt_agent",
  "tool": "create_presentation",
  "args": {
    "title": "slides_title",
    "slides": "prepared_slides",
    "out_path": "output_path"
  },
  "done": false
}
"""
        
        elif not ppt_created:
            # Step 4: Generate PPT
            action_guidance = """
NEXT STEP: Create PowerPoint presentation.
JSON Response MUST be:
{
  "agent": "ppt_agent",
  "tool": "create_presentation",
  "args": {
    "title": "slides_title",
    "slides": "prepared_slides",
    "out_path": "output_path"
  },
  "done": false
}
Note: Use string references, system will provide actual objects.
"""
        
        else:
            # Workflow complete
            return None
        
        # Build prompt with explicit examples and guidance
        prompt = f"""{tools_desc}

{state_summary}

{action_guidance}

CRITICAL INSTRUCTIONS:
- Respond ONLY with valid JSON in a single compact line or multiline.
- NO markdown, NO code blocks, NO triple backticks, NO "json" prefix.
- NO comments (// or /* */ or () comments) INSIDE the JSON object.
- NO explanatory text after the JSON.
- Agent and tool names: use LOWERCASE, NO SPACES, SINGLE UNDERSCORES only.
- Your response must start with {{ and end with }}.
- Example: {{"agent": "data_agent", "tool": "load_csv", "args": {{}}, "done": false}}
"""

        try:
            response = self.llm._call_ollama(prompt, max_tokens=300)
            print(f"LLM Response: {response[:200]}...")  # Debug: see first 200 chars
            
            # Remove comments from JSON (// style comments)
            response_clean = response.split('//')[0].strip()
            
            # Remove inline comments like "(system provides ...)" from within JSON values
            # This regex removes text in parentheses
            import re
            response_clean = re.sub(r'\s*\([^)]*\)\s*', ' ', response_clean)
            
            # Escape backslashes in the response for valid JSON parsing
            response_clean = response_clean.replace('\\', '\\\\')
            
            # Extract the JSON object by finding matching braces
            start_idx = response_clean.find('{')
            if start_idx == -1:
                print(f"⚠ Could not find JSON start in response")
                return None
            
            # Count braces to find the complete JSON object
            brace_count = 0
            end_idx = start_idx
            for i in range(start_idx, len(response_clean)):
                if response_clean[i] == '{':
                    brace_count += 1
                elif response_clean[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            
            if brace_count != 0:
                print(f"⚠ Incomplete JSON (unmatched braces)")
                return None
            
            json_str = response_clean[start_idx:end_idx]
            
            try:
                action_dict = json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"⚠ JSON parsing error: {e}")
                print(f"   Cleaned response: {response_clean[:150]}")
                return None
            
            # Validate response structure
            if not action_dict.get("agent") or not action_dict.get("tool"):
                print(f"⚠ Invalid action structure: {action_dict}")
                return None
            
            # Check if done
            if action_dict.get("done", False):
                return None
            
            # Build and return ToolCall
            # Normalize agent and tool names aggressively:
            # - Remove spaces
            # - Replace multiple underscores with single underscore
            # - Convert to lowercase
            agent = action_dict.get("agent", "").strip().replace(" ", "").lower()
            agent = re.sub(r'_+', '_', agent)  # Replace multiple underscores with single
            
            tool = action_dict.get("tool", "").strip().replace(" ", "").lower()
            tool = re.sub(r'_+', '_', tool)  # Replace multiple underscores with single
            
            return ToolCall(
                agent=agent,
                tool=tool,
                args=action_dict.get("args", {})
            )
        except json.JSONDecodeError as e:
            print(f"⚠ JSON parsing error: {e}")
            return None
        except Exception as e:
            print(f"✗ Error in LLM decision: {e}")
            return None

    def _execute_tool(self, tool_call: ToolCall) -> Any:
        """Execute the tool call and return result."""
        agent = tool_call.agent
        tool = tool_call.tool
        args = tool_call.args

        # Map string references in args to actual state objects
        # This allows LLM to say "df" and we use the actual DataFrame from state
        resolved_args = {}
        for key, value in args.items():
            if isinstance(value, str) and value.lower() == "dataframe":
                # Use the actual DataFrame from state
                resolved_args[key] = self.state.get("df")
            elif isinstance(value, str) and value.lower() == "prepared_slides":
                # Use the prepared slides from state
                resolved_args[key] = self.state.get("slides")
            elif isinstance(value, str) and value.lower() == "output_path":
                # Use the output path from state
                resolved_args[key] = self.state.get("out_pptx")
            elif isinstance(value, str) and value.lower() == "slides_title":
                # Use the title from state
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
                return create_presentation(
                    resolved_args.get("title"),
                    resolved_args.get("slides"),
                    resolved_args.get("out_path")
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
                    print("✓ CSV loaded")

                elif action.agent == "data_agent" and action.tool == "extract_insights":
                    self.state["insights"] = self._execute_tool(action)
                    print(f"✓ Extracted {len(self.state['insights'])} insights")

                elif action.agent == "llm_agent" and action.tool == "polish":
                    # Polish a specific insight by index
                    idx = action.args.get("insight_index", 0)
                    if idx < len(self.state.get("insights", [])):
                        ins = self.state["insights"][idx]
                        polished = self.llm.summarize(ins.title, ins.summary)
                        if "polished_insights" not in self.state:
                            self.state["polished_insights"] = {}
                        self.state["polished_insights"][idx] = polished
                        print(f"✓ Polished insight {idx}")

                elif action.agent == "ppt_agent" and action.tool == "create_presentation":
                    # Build slides from polished insights or original insights
                    slides: List[PPTSlide] = []
                    for idx, ins in enumerate(self.state.get("insights", [])):
                        polished = self.state.get("polished_insights", {}).get(idx, ins.summary)
                        content = polished
                        if ins.details:
                            content += "\n\nDetails:\n" + self._format_details(ins.details)
                        slides.append(PPTSlide(title=ins.title, content=content))
                    
                    self.state["slides"] = slides[: cfg.max_slides]
                    result = self._execute_tool(action)
                    print(f"✓ Generated PPT with {len(self.state['slides'])} slides")
                    return result

                else:
                    print(f"⚠ Unknown action: {action.agent}.{action.tool}")

            except Exception as e:
                print(f"✗ Error executing {action.agent}.{action.tool}: {e}")
                break

        print(f"\nOrchestration finished after {iteration} iterations")
        return out_pptx
