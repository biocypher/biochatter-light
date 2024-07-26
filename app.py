# BioChatter Light: lightweight pure Python frontend for BioChatter
app_name = "biochatter-light"

import os
import streamlit as st
from components.logic import main_logic

st.set_page_config(
    page_title=os.getenv("BIOCHATTER_LIGHT_TITLE") or "BioChatter Light",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

ss = st.session_state

if os.getenv("BIOCHATTER_LIGHT_HEADER"):
    st.markdown(f'# {os.getenv("BIOCHATTER_LIGHT_HEADER")}')

if os.getenv("BIOCHATTER_LIGHT_SUBHEADER"):
    st.markdown(f'### {os.getenv("BIOCHATTER_LIGHT_SUBHEADER")}')


def local_css(file_name):
    """
    Load local CSS file.
    """
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


local_css("style.css")


if __name__ == "__main__":
    main_logic()
