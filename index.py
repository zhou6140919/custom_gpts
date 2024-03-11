import streamlit as st

from sidebar import show

st.set_page_config(
	page_title="CustomGPTs",
	page_icon="💸",
	layout="wide"
)

show()

st.toast("Welcome to CustomGPTs!", icon="💸")

st.session_state.default_model = st.selectbox("Select a default model engine", options=["gpt-4-1106-preview", 'gpt-3.5-turbo-0125', 'claude-3-opus-20240229', "claude-3-sonnet-20240229"], index=0)
st.session_state.default_engine = st.selectbox("Select a default web search engine", options=["google", "duckduckgo"], index=0)
