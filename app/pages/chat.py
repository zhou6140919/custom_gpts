import os
import pathlib
import asyncio
import random
import json

import streamlit as st
from streamlit_modal import Modal

from utils import *
from sidebar import show

st.set_page_config(
    page_title="Quick Chat",
    page_icon="💬",
    layout="wide"
)

show()

st.header("Quick Chat")
st.write("Ask questions to our clever assistant.")


# TODO: save history messages to file

if 'confirm' not in st.session_state:
    st.session_state.confirm = False
if 'load_history' not in st.session_state:
    st.session_state.load_history = False

parent_path = pathlib.Path(__file__).parent.parent.resolve()
data_path = os.path.join(parent_path, "data")

with st.sidebar:
    st.header("Chat History")
    history_files = [f for f in os.listdir(data_path) if os.path.isfile(os.path.join(data_path, f))]
    history_look_ups = [{"title": json.load(open(os.path.join(data_path, f)))["title"], "file_name": f, "path": os.path.join(data_path, f)} for f in history_files]
    for s in history_look_ups:
        with st.container(height=75, border=True):
            if st.button(s["title"][:20], use_container_width=True):
                st.session_state.load_history = True
                st.session_state.file_key = int(s["file_name"].replace(".json", ""))
                st.session_state.messages = json.load(open(s["path"]))["messages"]
                st.session_state.model = json.load(open(s["path"]))["model"]
    
with st.container(border=True):
    # choose model by user
    a, b = st.columns(2)
    c, d = a.columns(2)
    with c: 
        model_options = ["gpt-4-1106-preview", 'gpt-3.5-turbo-0125', 'claude-3-opus-20240229', "claude-3-sonnet-20240229"]
        if 'model' not in st.session_state:
            index = 0
        else:
            index = model_options.index(st.session_state.model)
        model = st.radio("Select a model engine", options=model_options, index=index)
        st.session_state.model = model
        clear = st.button("Delete History")
    with d:
        st.write("\n")
        st.markdown("- \$10/1M tokens"+ "\n"
                    "- \$0.5/1M tokens" + "\n"
                    "- $15/1M tokens" + "\n"
                    "- $3/1M tokens")
        new_chat = st.button("New Chat")
        
    with b:
        if st.session_state.load_history:
            system_prompt = st.text_area("System Prompt", value=" ".join([m["content"] for m in st.session_state.messages if m["role"] == "system"]), disabled=True)
        else:
            if 'messages' in st.session_state and len(st.session_state.messages) > 1:
                flag = True
            else:
                flag = False
            system_prompt = st.text_area("System Prompt", value="You are a helpful assistant.", disabled=flag)


async def chat(messages, model):
    with st.chat_message("User"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        messages = await run_conversation(messages, model, message_placeholder)
        st.session_state.messages = messages
    if len(st.session_state.messages) > 2:
        st.session_state.need_save = True
    if st.session_state.need_save:
        if 'file_key' not in st.session_state:
            st.session_state.file_key = random.randint(0, 1000000000)
        if st.session_state.load_history:
            title = json.load(open(f"{st.session_state.file_key}.json"))["title"]
        else:
            # TODO: get title
            title = st.session_state.messages[1]["content"][:30]
        # auto save
        with open(os.path.join(data_path, f"{st.session_state.file_key}.json"), "w") as f:
            json.dump({"title": title, "model": st.session_state.model, "messages": st.session_state.messages}, f, indent=4, ensure_ascii=False)
            print(f"Saved to {st.session_state.file_key}.json")
    return messages


#if st.session_state.confirm:
if "messages" not in st.session_state or len(st.session_state.messages) < 2:
    messages = [{"role": "system", "content": system_prompt}]
    st.session_state.messages = messages
    print(messages)
if 'need_save' not in st.session_state:
    st.session_state.need_save = False
# Print all messages in the session state
for message in [m for m in st.session_state.messages if m["role"] != "system"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

confirm_modal = Modal(title="", key="confirm_modal", max_width=500)

    
    

if prompt := st.chat_input("Ask me anything"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    asyncio.run(chat(st.session_state.messages, st.session_state.model))

def delete_history():
    os.remove(os.path.join(data_path, f"{st.session_state.file_key}.json"))
    st.session_state.clear()
    
if clear:
    with confirm_modal.container():
        if len(st.session_state.messages) < 2:
            st.write("There is no chat history to delete.")
        else:
            st.write("Are you sure you want to delete the chat history?")
            st.button("Yes", on_click=delete_history)
                
if new_chat:
    st.session_state.clear()
    st.rerun()