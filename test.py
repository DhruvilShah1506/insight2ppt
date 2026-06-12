import streamlit as st
import requests

st.title("C42 GPU Chat")

if "messages" not in st.session_state:
  st.session_state.messages = []

for msg in st.session_state.messages:
  with st.chat_message(msg["role"]):
      st.write(msg["content"])

prompt = st.chat_input("Ask anything...")

if prompt:
  st.session_state.messages.append({"role": "user", "content": prompt})
  with st.chat_message("user"):
      st.write(prompt)

  with st.chat_message("assistant"):
      with st.spinner("Thinking..."):
          r = requests.post("http://localhost:8000/v1/chat/completions", json={
              "model": "Qwen/Qwen2-7B-Instruct",
              "messages": st.session_state.messages,
              "temperature": 0.7,
              "max_tokens": 512
          })
          reply = r.json()["choices"][0]["message"]["content"]
          st.write(reply)

  st.session_state.messages.append({"role": "assistant", "content": reply})