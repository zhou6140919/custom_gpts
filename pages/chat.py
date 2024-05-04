import os
import asyncio
import random
import json
from glob import glob
import copy
import datetime
import clipboard

import streamlit as st
from streamlit_modal import Modal
from streamlit_option_menu import option_menu

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

print(st.session_state)

if 'load_history' not in st.session_state:
    st.session_state.load_history = False

if 'manual_selection' not in st.session_state:
    st.session_state.manual_selection = None



parent_path = os.getcwd()
data_path = os.path.join(parent_path, "data")
if not os.path.exists(data_path):
    os.makedirs(data_path)


def sort_by_date(timestamp):
    return datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S')

def load_history():
    history_files = [f for f in glob(f"{data_path}/*.json")]
    history_look_ups = [{"title": json.load(open(os.path.join(data_path, f)))["title"], "file_name": f, "path": os.path.join(data_path, f), "timestamp": json.load(open(os.path.join(data_path, f)))["timestamp"]} for f in history_files]
    history_look_ups = sorted(history_look_ups, key=lambda x: x["timestamp"], reverse=True)
    return history_look_ups

with st.sidebar:
    # st.session_state.default_odel = st.selectbox("Select a default model engine", options=["gpt-4-1106-preview", 'gpt-3.5-turbo-0125', 'claude-3-opus-20240229', "claude-3-sonnet-20240229"], index=0)
    # st.session_state.default_engine = st.selectbox("Select a default web search engine", options=["google", "duckduckgo"], index=0)
    with st.container():
        a, b = st.columns([2, 2.5])
        with a:
            st.header("Chat History")
        with b:
            clear_all = st.button("Delete All History", type="primary")
    # history_files = [f for f in glob(f"{data_path}/*.json")]
    # history_look_ups = [{"title": json.load(open(os.path.join(data_path, f)))["title"], "file_name": f, "path": os.path.join(data_path, f)} for f in history_files]
    history_look_ups = load_history()
    
    selected = option_menu(
        menu_title=None,
        options=["New Chat"] + [s["title"][:22] for s in history_look_ups],
        default_index=0,
        icons=["plus-square-fill"] + [f"{i}-circle-fill" for i, _ in enumerate(history_look_ups)],
        orientation="vertical",
        styles={
            "container": {"padding": "0!important", "background-color": "#74992e"},
            "icon": {"font-size": "20px", "margin-right": "10px"},
            "nav-link": {"font-size": "15px", "text-align": "left", "margin":"0px", "--hover-color": "darkblue"},
            "nav-link-selected": {"background-color": "green"},
        },
        manual_select=st.session_state.manual_selection
    )

    if selected == "New Chat":
        if 'need_clear' in st.session_state:
            st.session_state.clear()
            st.session_state.load_history = False
            st.session_state.manual_selection = None
            st.rerun()
    else:
        for s in history_look_ups:
            # TODO: same titles issue
            if selected == s["title"][:22]:
                st.session_state.load_history = True
                st.session_state.file_key = int(s["file_name"].split("/")[-1].replace(".json", ""))
                st.session_state.local_messages = json.load(open(s["path"]))["messages"]
                st.session_state.messages = copy.deepcopy(st.session_state.local_messages)
                for m in st.session_state.messages:
                    if m["role"] == "assistant":
                        m.pop("action", None)
                        m.pop("new_prompt", None)
                st.session_state.model = json.load(open(s["path"]))["model"]
                st.session_state.need_clear = True
        
        


with st.container(border=True):
    # choose model by user
    a, b = st.columns(2)
    c, d = a.columns(2)
    with c: 
        model_options = ["gpt-4-turbo-2024-04-09", 'gpt-3.5-turbo-0125', 'claude-3-opus-20240229', "claude-3-sonnet-20240229"]
        if 'model' not in st.session_state:
            index = 0
        else:
            index = model_options.index(st.session_state.model)
        if 'messages' in st.session_state and len(st.session_state.messages) > 1:
            flag = True
        else:
            flag = False
        #model = st.radio("Select a model engine", options=model_options, index=index, disabled=flag)
        model = st.selectbox("Select a model engine", options=model_options, index=index, disabled=flag)
        st.session_state.model = model
        clear = st.button("Delete History", type="primary")
        if 'max_tokens' not in st.session_state:
            st.session_state.max_tokens = 2048
        st.session_state.max_tokens = st.slider("Max Tokens", min_value=1024, max_value=4096, value=st.session_state.max_tokens, step=128)
    with d:
        st.write("\n")
        st.markdown("- \$10/1M tokens"+ "\n"
                    "- \$0.5/1M tokens" + "\n"
                    "- $15/1M tokens" + "\n"
                    "- $3/1M tokens")
        if 'use_internet' not in st.session_state:
            st.session_state.use_internet = False
        st.session_state.use_internet = st.toggle("Use Internet", value=st.session_state.use_internet)
        
        
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
    print("messages", messages)
    with st.chat_message("assistant"):
        if st.session_state.use_internet:
            new_prompt, action_query = ah.action(messages)
        else:
            new_prompt, action_query = None, None
        message_placeholder = st.empty()
        messages = await run_conversation(messages, model, message_placeholder, new_prompt if action_query else None, st.session_state.max_tokens)
        print("messages", messages)
        st.session_state.messages = messages
        st.session_state.local_messages = copy.deepcopy(messages)
        st.session_state.local_messages[-1].update({"action": action_query, "new_prompt": new_prompt})
    if len(st.session_state.messages) > 2:
        st.session_state.need_save = True
        st.session_state.need_clear = True
    if st.session_state.need_save:
        if 'file_key' not in st.session_state:
            st.session_state.file_key = random.randint(0, 1000000000)
            while st.session_state.file_key in [int(f.split("/")[-1].replace(".json", "")) for f in glob(f"{data_path}/*.json")]:
                st.session_state.file_key = random.randint(0, 1000000000)
        history_look_ups = load_history()
        if st.session_state.load_history:
            title = json.load(open(os.path.join(data_path, f"{st.session_state.file_key}.json")))["title"]
        else:
            # TODO: get title
            title = st.session_state.messages[1]["content"][:20]
            if title in [i["title"][:20] for i in history_look_ups]:
                title = title + f"_{random.randint(0, 100)}"
        # auto save
        with open(os.path.join(data_path, f"{st.session_state.file_key}.json"), "w") as f:
            json.dump({"title": title, "timestamp": str(datetime.datetime.now()), "model": st.session_state.model, "messages": st.session_state.local_messages}, f, indent=4, ensure_ascii=False)
            print(f"Saved to {st.session_state.file_key}.json")
        history_look_ups = load_history()
        st.session_state.manual_selection = [i["file_name"].split('/')[-1] for i in history_look_ups].index(f"{st.session_state.file_key}.json") + 1
    return messages


if "messages" not in st.session_state or len(st.session_state.messages) < 2:
    messages = [{"role": "system", "content": system_prompt}]
    st.session_state.messages = messages

if "local_messages" not in st.session_state:
    st.session_state.local_messages = copy.deepcopy(st.session_state.messages)
    

if 'need_save' not in st.session_state:
    st.session_state.need_save = False
# Print all messages in the session state

    
for message in [m for m in st.session_state.local_messages if m["role"] != "system"]:
    with st.chat_message(message["role"]):
        if message.get("action", None):
            with st.status(label=message["action"], expanded=False, state="complete"):
                st.write(message["new_prompt"])
        st.markdown(message["content"])
        if st.button("📃", key=message["content"]):
            # TODO: not working on server
            clipboard.copy(message["content"])

        
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
        if len(history_look_ups) < 1:
            st.write("There is no chat history to delete.")
        else:
            st.write("Are you sure you want to delete all chat history?")
            st.button("Yes", on_click=delete_all_history)
