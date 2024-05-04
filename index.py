import streamlit as st

from sidebar import show

st.set_page_config(
	page_title="CustomGPTs",
	page_icon="💸",
	layout="wide"
)

show()

st.toast("Welcome to CustomGPTs!", icon="💸")
