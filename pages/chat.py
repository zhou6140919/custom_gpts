import os
import asyncio
import random
import json
from glob import glob

import streamlit as st
from streamlit_modal import Modal

from utils import *
from sidebar import show
from search import ActionHandler

st.set_page_config(
    page_title="Quick Chat",
    page_icon="💬",
    layout="wide"
)

show()

st.title("Quick Chat")
st.write("Ask questions to our clever assistant. Successfully connected to :spider_web:")


if 'load_history' not in st.session_state:
    st.session_state.load_history = False


parent_path = os.getcwd()
data_path = os.path.join(parent_path, "data")
if not os.path.exists(data_path):
    os.makedirs(data_path)


with st.sidebar:
    with st.container():
        a, b = st.columns(2)
        with a:
            st.header("Chat History")
        with b:
            clear_all = st.button("Delete All History", type="primary")
    history_files = [f for f in glob(f"{data_path}/*.json")]
    history_look_ups = [{"title": json.load(open(os.path.join(data_path, f)))["title"], "file_name": f, "path": os.path.join(data_path, f)} for f in history_files]
    for s in history_look_ups:
        with st.container(height=75, border=True):
            if st.button(s["title"][:20], use_container_width=True, key=int(s["file_name"].split("/")[-1].replace(".json", ""))):
                st.session_state.load_history = True
                st.session_state.file_key = int(s["file_name"].split("/")[-1].replace(".json", ""))
                st.session_state.local_messages = json.load(open(s["path"]))["messages"]
                st.session_state.messages = st.session_state.local_messages
                for m in st.session_state.messages:
                    if m["role"] == "user":
                        m.pop("action", None)
                        m.pop("new_prompt", None)
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
        if 'messages' in st.session_state and len(st.session_state.messages) > 1:
            flag = True
        else:
            flag = False
        model = st.radio("Select a model engine", options=model_options, index=index, disabled=flag)
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
    with st.chat_message("assistant"):
        new_prompt, action_query = ah.action(messages)
        message_placeholder = st.empty()
        messages = await run_conversation(messages, model, message_placeholder, new_prompt if action_query else None)
        st.session_state.messages = messages
        st.session_state.local_messages = messages
        st.session_state.local_messages[-1].update({"action": action_query, "new_prompt": new_prompt})
    if len(st.session_state.messages) > 2:
        st.session_state.need_save = True
    if st.session_state.need_save:
        if 'file_key' not in st.session_state:
            st.session_state.file_key = random.randint(0, 1000000000)
            while st.session_state.file_key in [int(f.split("/")[-1].replace(".json", "")) for f in glob(f"{data_path}/*.json")]:
                st.session_state.file_key = random.randint(0, 1000000000)
        if st.session_state.load_history:
            title = json.load(open(os.path.join(data_path, f"{st.session_state.file_key}.json")))["title"]
        else:
            # TODO: get title
            title = st.session_state.messages[1]["content"][:30]
        # auto save
        with open(os.path.join(data_path, f"{st.session_state.file_key}.json"), "w") as f:
            json.dump({"title": title, "model": st.session_state.model, "messages": st.session_state.local_messages}, f, indent=4, ensure_ascii=False)
            print(f"Saved to {st.session_state.file_key}.json")
    return messages


if "messages" not in st.session_state or len(st.session_state.messages) < 2:
    messages = [{"role": "system", "content": system_prompt}]
    st.session_state.messages = messages

    

if 'need_save' not in st.session_state:
    st.session_state.need_save = False
# Print all messages in the session state
for message in [m for m in st.session_state.local_messages if m["role"] != "system"]:
    with st.chat_message(message["role"]):
        if message.get("action", None):
            with st.status(label=message["action"], expanded=False, state="complete"):
                st.write(message["new_prompt"])
        st.markdown(message["content"])

        
confirm_modal = Modal(title="", key="confirm_modal", max_width=500)

if prompt := st.chat_input("Ask me anything"):
    with st.chat_message("User"):
        st.markdown(prompt)
    ah = ActionHandler(model)
    st.session_state.messages.append({"role": "user", "content": prompt})
    asyncio.run(chat(st.session_state.messages, st.session_state.model))
    st.rerun()

def delete_history():
    if 'file_key' in st.session_state:
        os.remove(os.path.join(data_path, f"{st.session_state.file_key}.json"))
    st.session_state.clear()

def delete_all_history():
    for f in glob(f"{data_path}/*.json"):
        os.remove(f)
    st.session_state.clear()
    
if clear:
    with confirm_modal.container():
        if len(st.session_state.messages) < 2:
            st.write("There is no chat history to delete.")
        else:
            st.write("Are you sure you want to delete the chat history?")
            st.button("Yes", on_click=delete_history)

if clear_all:
    with confirm_modal.container():
        if len(history_files) < 1:
            st.write("There is no chat history to delete.")
        else:
            st.write("Are you sure you want to delete all chat history?")
            st.button("Yes", on_click=delete_all_history)
                
if new_chat:
    st.session_state.clear()
    st.rerun()
