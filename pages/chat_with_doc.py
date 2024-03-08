import os
import json
import datetime
import asyncio

import streamlit as st
from pypdf import PdfReader

from utils import *
from sidebar import show

st.set_page_config(
    page_title="Chat with Doc",
    page_icon="📃",
    layout="wide"
)

st.title("Chat with Doc")

show()


parent_path = os.getcwd()
data_path = os.path.join(parent_path, "doc_data")

if not os.path.exists(data_path):
    os.makedirs(data_path)

if 'doc_messages' not in st.session_state:
    st.session_state.doc_messages = [{"role": "system", "content": "You are an expert of reading documents. You should help users to find the information they need."}]
        
if 'doc_need_save' not in st.session_state:
    st.session_state.doc_need_save = False

if 'doc_load_history' not in st.session_state:
    st.session_state.doc_load_history = False

if os.path.exists(os.path.join(data_path, "doc_data.json")):
    file = json.load(open(os.path.join(data_path, "doc_data.json")))
    st.session_state.doc_load_history = True
    st.session_state.doc_messages = file["messages"]
    st.session_state.doc_model = file["model"]
    
with st.container(border=True):
    a, b = st.columns([1, 1])
    c, d = a.columns([1, 1])
    with c:
        model_options = ["gpt-4-1106-preview", 'gpt-3.5-turbo-0125', 'claude-3-opus-20240229', "claude-3-sonnet-20240229"]
        if 'doc_model' not in st.session_state:
            index = 0
        else:
            index = model_options.index(st.session_state.doc_model)
        if 'doc_messages' in st.session_state and len(st.session_state.doc_messages) > 2:
            flag = True
        else:
            flag = False
        model = st.selectbox("Select a model engine", options=model_options, index=index, disabled=flag)
        st.session_state.doc_model = model
        clear = st.button("Delete History", type="primary")
    with d:
        st.write("\n")
        st.markdown("- \$10/1M tokens"+ "\n"
                    "- \$0.5/1M tokens" + "\n"
                    "- $15/1M tokens" + "\n"
                    "- $3/1M tokens")
    with b:
        uploaded_file = st.file_uploader("Upload a file", type=["pdf", "docx", "txt"])
        if uploaded_file is not None:
            if uploaded_file.type == "application/pdf":
                pdf = PdfReader(uploaded_file)
                text = pdf.pages[0].extract_text()
            else:
                text = uploaded_file.getvalue().decode("utf-8")
            st.session_state.doc_messages.append({"role": "user", "content": "This is the document:\n\n" + text})
            st.session_state.doc_messages.append({"role": "assistant", "content": "OK, I got the document. What can I do for you?"})
        else:
            if not st.session_state.doc_load_history:
                st.info("Please upload a file")
                st.stop()


async def chat(messages, model):
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        messages = await run_conversation(messages, model, message_placeholder, None)
        st.session_state.doc_messages = messages
    if len(st.session_state.doc_messages) > 2:
        st.session_state.doc_need_save = True
    if st.session_state.doc_need_save:
        with open(os.path.join(data_path, "doc_data.json"), "w") as f:
            json.dump({"timestamp": str(datetime.datetime.now()), "model": st.session_state.doc_model, "messages": st.session_state.doc_messages}, f, indent=4, ensure_ascii=False)
    return messages

# Print all messages in the session state
for message in [m for m in st.session_state.doc_messages if m["role"] != "system"]:
    if message["role"] == "user" and message["content"].startswith("This is the document:"):
        continue
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me anything"):
    with st.chat_message("User"):
        st.markdown(prompt)
    st.session_state.doc_messages.append({"role": "user", "content": prompt})
    asyncio.run(chat(st.session_state.doc_messages, st.session_state.doc_model))
    st.rerun()
    
if clear:
    os.remove(os.path.join(data_path, "doc_data.json"))
    st.session_state.clear()
    st.rerun()
