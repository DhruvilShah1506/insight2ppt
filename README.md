# insight2ppt

POC: Convert raw datasets into executive-ready PowerPoint slides automatically.

Quickstart

1. Create a virtualenv and install dependencies:

	```bash
	python -m venv .venv
	.\.venv\Scripts\activate
	pip install -r requirements.txt
	```

2. Run the Streamlit app:

	```bash
	streamlit run app.py
	```

3. Upload `data/sample.csv` in the UI and click "Generate PPT".

Notes

- The central orchestrator is `src.orchestrator.CentralOrchestrator`.
- Replace `src.agents.llm_adapter.QWEXAdapter` internals with real QWEX SDK calls.
- Pydantic models live in `src/models.py`.
