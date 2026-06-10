import streamlit as st
from src.orchestrator import CentralOrchestrator
from src.models import OrchestratorConfig
import tempfile
import os


st.title("PPT / Executive Insight Generator")

uploaded = st.file_uploader("Upload CSV", type=["csv"]) 
if uploaded is not None:
    bytes_data = uploaded.read()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    tmp.write(bytes_data)
    tmp.flush()
    tmp.close()

    title = st.text_input("Presentation Title", value="Executive Insights")
    max_slides = st.slider("Max slides", 1, 12, 6)

    if st.button("Generate PPT"):
        cfg = OrchestratorConfig(title=title, max_slides=max_slides)
        orch = CentralOrchestrator()
        out_path = os.path.join(tempfile.gettempdir(), "insights_poc.pptx")
        with st.spinner("Generating slides..."):
            pptx_path = orch.generate_ppt_from_csv(tmp.name, out_path, cfg=cfg)
        st.success("PPT generated")
        with open(pptx_path, "rb") as f:
            st.download_button("Download PPTX", data=f, file_name="insights_poc.pptx")
