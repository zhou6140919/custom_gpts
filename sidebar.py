import streamlit as st


def show() -> None:
	with st.sidebar:
		st.markdown(f"""
			<a href="/" style="color:black;text-decoration: none;">
				<div style="display:table;margin-top:-16rem;margin-left:0%;">
					<span style="font-size: 0.8em; color: grey">&nbsp;&nbsp;v0.1.0</span>
					<br>
					<span style="font-size: 0.8em">Your custom gpts</span>
				</div>
			</a>
			<br>
				""", unsafe_allow_html=True)
