# app.py: streamlit chat app for contextualisation of biomedical results
import streamlit as st
from _llm_connect import generate_response


def _render_prompt(input_text: str, user_name: str):
    prompt = user_name + ": " + input_text
    return prompt


def _render_response(input_text: str, context: str):
    response = "ChatGSE: " + generate_response(input_text, context)
    return response


st.set_page_config(
    page_title="ChatGSE",
    page_icon=":robot_face:",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("ChatGSE")


if "history" not in st.session_state:
    st.markdown(
        """
        Welcome to ChatGSE. What is your name?
        """
    )
    st.session_state.history = []
else:
    for msg in st.session_state.history:
        st.write(msg)

if "input" not in st.session_state:
    st.session_state.input = ""

if "mode" not in st.session_state:
    st.session_state.mode = "name"

if "user_name" not in st.session_state:
    st.session_state.user_name = "User"

if "context" not in st.session_state:
    st.session_state.context = "biomedical research"


def submit():
    st.session_state.input = st.session_state.widget
    st.session_state.widget = ""


if st.session_state.input:
    if st.session_state.mode == "name":
        st.session_state.user_name = st.session_state.input
        st.session_state.mode = "topic"
        msg = f"Hi {st.session_state.user_name}, what is the context of your inquiry?"
        st.session_state["history"].append(msg)
        st.write(msg)

    elif st.session_state.mode == "topic":
        st.session_state.context = st.session_state.input
        st.session_state.mode = "chat"
        msg = f"You have selected {st.session_state.context} as your context. You can now ask questions."
        st.session_state["history"].append(msg)
        st.write(msg)

    elif st.session_state.mode == "chat":
        prompt = _render_prompt(
            st.session_state.input, st.session_state.user_name
        )
        st.session_state["history"].append(prompt)
        st.write(prompt)
        response = _render_response(prompt, st.session_state.context)
        st.session_state["history"].append(response)
        st.write(response)

st.text_input(
    "Input:",
    on_change=submit,
    key="widget",
    placeholder="Enter text here.",
)
