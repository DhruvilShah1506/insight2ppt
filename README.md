# insight2ppt

POC: Convert raw datasets into executive-ready PowerPoint slides automatically using AI-driven agent orchestration with local Ollama LLM.

## Troubleshooting 404 Error

If you see: `[Error calling Ollama: 404 Client Error: Not Found...]`

**→ See [OLLAMA_SETUP.md](OLLAMA_SETUP.md) for quick fixes**

In short:
1. Open terminal and run: `ollama serve`
2. In another terminal, ensure model exists: `ollama pull qwen:0.5b`
3. Run the app: `streamlit run app.py`

## Prerequisites

**Install Ollama** (if not already installed):
- Download from [ollama.ai](https://ollama.ai)
- Windows/Mac/Linux installers available

**Download Qwen 3.5 model**:
```bash
ollama pull qwen:0.5b
```

**Start Ollama server** (runs on `http://localhost:11434` by default):
```bash
ollama serve
```
> Keep this running in a separate terminal while using the app.

## Quickstart

1. Create a virtualenv and install dependencies:

	```bash
	python -m venv .venv
	.\.venv\Scripts\activate
	pip install -r requirements.txt
	```

2. Ensure Ollama is running with Qwen 3.5 model:
	```bash
	ollama serve
	```

3. Run the Streamlit app (in a new terminal):

	```bash
	streamlit run app.py
	```

4. Upload `data/sample.csv` in the UI, configure model/Ollama URL, and click "Generate PPT".

## Architecture

- **Central Orchestrator** (`src.orchestrator.CentralOrchestrator`): Single entry point
- **AI Orchestrator** (`src.ai_orchestrator.AIOrchestrator`): LLM-driven agent sequencing with dynamic workflow
- **Data Agent** (`src.agents.dataset_loader`, `src.agents.insight_extractor`): CSV loading & analysis
- **LLM Agent** (`src.agents.llm_adapter.OllamaAdapter`): Uses Ollama for text polishing
- **PPT Agent** (`src.agents.ppt_generator`): Slide generation

## Configuration

In the Streamlit UI:
- **Ollama URL**: Default `http://localhost:11434` (adjust if Ollama runs elsewhere)
- **Model Name**: Default `qwen:0.5b` (use other models if available: `qwen:2.5`, `mistral`, etc.)

## Features

- ✅ AI-driven dynamic orchestration (LLM decides next step, not hardcoded sequences)
- ✅ Local Ollama integration (no cloud API calls)
- ✅ Automatic CSV → Insights → Slides pipeline
- ✅ LLM text polishing for executive summaries
- ✅ Beautiful PowerPoint generation with formatting

## Notes

- Pydantic models in `src/models.py`
- Agent framework in `src/agents/agent_framework.py`
- Detailed Ollama setup guide: [OLLAMA_SETUP.md](OLLAMA_SETUP.md)
