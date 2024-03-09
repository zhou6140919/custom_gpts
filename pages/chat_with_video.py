import os
import json
import datetime
import asyncio

import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import streamlit.components.v1 as components

from utils import *
from sidebar import show
from bili_sub import get_bilibili_sub

st.set_page_config(
    page_title="Chat with Video",
    page_icon="🎬",
    layout="wide"
)

show()

st.title("Chat with Video")

parent_path = os.getcwd()
data_path = os.path.join(parent_path, "video_data")

if not os.path.exists(data_path):
    os.makedirs(data_path)

if 'video_need_save' not in st.session_state:
    st.session_state.video_need_save = False

if 'video_load_history' not in st.session_state:
    st.session_state.video_load_history = False

if os.path.exists(os.path.join(data_path, "video_data.json")):
    file = json.load(open(os.path.join(data_path, "video_data.json")))
    st.session_state.video_load_history = True
    st.session_state.video_messages = file["messages"]
    st.session_state.video_model = file["model"]
    st.session_state.video_link = file["link"]
    st.session_state.video_language = file["language"]

def float2time(float_time):
    m, s = divmod(float_time, 60)
    h, m = divmod(m, 60)
    return f"{h:02.0f}:{m:02.0f}:{s:05.2f}"

with st.container(border=True):
    video_link = st.text_input("Enter the video link:", value=st.session_state.video_link if "video_link" in st.session_state else "")
    st.session_state.video_link = video_link
    language = st.selectbox(
        label="Select Video Language",
        options=["Chinese", "English"],
        index=0 if "video_language" not in st.session_state else 0 if st.session_state.video_language == "Chinese" else 1
    )
    st.session_state.video_language = language
    if not video_link:
        st.warning("Please enter a video link.")
        st.stop()
    a, b = st.columns([3, 1])
    with a:
        if "youtube.com" in video_link:
            st.video(video_link, start_time=0)
        elif "bilibili.com" in video_link:
            bid = [t for t in video_link.split("/") if t.startswith('BV')][0]
            embed_link = "https://player.bilibili.com/player.html?bvid=" + bid + "&page=1&highQuality=1&danmuku=0&autoplay=0"
            #components.html(f'<iframe src="{embed_link}" width="100%" frameborder="0" allowfullscreen="allowfullscreen" scrolling="no"></iframe>', height=0, scrolling=True)
            #embed_link = "https://xbeibeix.com/api/bilibili/biliplayer/?url=" + video_link
            st.video(embed_link, start_time=0)
    with b:
        model_options = ["gpt-4-1106-preview", 'gpt-3.5-turbo-0125', 'claude-3-opus-20240229', "claude-3-sonnet-20240229"]
        if 'video_model' not in st.session_state:
            index = 3
        else:
            index = model_options.index(st.session_state.video_model)
        if 'video_messages' in st.session_state and len(st.session_state.video_messages) > 3:
            flag = True
        else:
            flag = False
        model = st.selectbox("Select a model engine", options=model_options, index=index, disabled=flag)
        st.session_state.video_model = model
        clear = st.button("Delete History", type="primary")

        lang = "zh" if language == "Chinese" else "en"
        with st.container(height=700):
            with st.status("Loading subtitle...") as status:
                try:
                    if "youtube.com" in video_link:
                        video_id = video_link.split("v=")[1]
                        subtitle_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
                        formatted_subtitle = [f"{float2time(i['start'])} => {float2time(i['start'] + i['duration'])}: {i['text']}" for i in subtitle_list]
                        for s in formatted_subtitle:
                            st.write(s)
                        formatted_subtitle = "\n".join(formatted_subtitle)
                    elif "bilibili.com" in video_link:
                        # TODO: bilibili subtitle
                        bid = [t for t in video_link.split("/") if t.startswith('BV')][0]
                        subtitle_list = get_bilibili_sub(bid, lang)
                        formatted_subtitle = [f"{float2time(i['from'])} => {float2time(i['to'])}: {i['content']}" for i in subtitle_list]
                        for s in formatted_subtitle:
                            st.write(s)
                        formatted_subtitle = "\n".join(formatted_subtitle)
                    else:
                        st.error("Unsupported video link.")
                        st.stop()
                except Exception as e1:
                    if lang == "zh":
                        if "youtube.com" in video_link:
                            try:
                                subtitle_list = YouTubeTranscriptApi.get_transcript(video_id, languages=["zh-Hans"])
                            except Exception as e2:
                                st.error(f"Error: {e2}")
                                st.stop()
                    else:
                        st.error(f"Error: {e1}")
                        st.stop()
                if not subtitle_list:
                    st.error("No subtitle found for this video.")
                    st.stop()
                if "video_messages" not in st.session_state:
                    st.session_state.video_messages = [{"role": "system", "content": "You are an expert of watching videos. You should help users to find the information they need."}]
                    st.session_state.video_messages.append({"role": "user", "content": "This is the video subtitle with timestamp:\n\n" + formatted_subtitle})
                    st.session_state.video_messages.append({"role": "assistant", "content": "OK, I got the subtitle. What can I do for you?"})


async def chat(messages, model):
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        messages = await run_conversation(messages, model, message_placeholder, None)
        st.session_state.video_messages = messages
    if len(st.session_state.video_messages) > 2:
        st.session_state.video_need_save = True
    if st.session_state.video_need_save:
        with open(os.path.join(data_path, "video_data.json"), "w") as f:
            json.dump({"link": st.session_state.video_link, "language": st.session_state.video_language, "timestamp": str(datetime.datetime.now()), "model": st.session_state.video_model, "messages": st.session_state.video_messages}, f, indent=4, ensure_ascii=False)
    return messages

# Print all messages in the session state
for message in [m for m in st.session_state.video_messages if m["role"] != "system"]:
    if message["role"] == "user" and message["content"].startswith("This is the video subtitle with timestamp:"):
        continue
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me anything"):
    with st.chat_message("User"):
        st.markdown(prompt)
    st.session_state.video_messages.append({"role": "user", "content": prompt})
    asyncio.run(chat(st.session_state.video_messages, st.session_state.video_model))
    st.rerun()
    
if clear:
    if os.path.exists(os.path.join(data_path, "video_data.json")):
        os.remove(os.path.join(data_path, "video_data.json"))
    for key in list(st.session_state.keys()):
        if key != "video_link" and key != "video_language" and key != "video_model":
            del st.session_state[key]
    st.rerun()
