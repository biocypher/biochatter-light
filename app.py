# app.py: streamlit chat app for contextualisation of biomedical results
import streamlit as st
from _llm_connect import Conversation


def _render_msg(role: str, msg: str):
    return f"`{role}`: {msg}"


def _get_user_name():
    st.session_state.mode = "context"
    st.session_state["conversation"] = Conversation(
        user_name=st.session_state.input
    )
    msg = f"Thank you, `{st.session_state.conversation.user_name}`! What is the context of your inquiry? For instance, this could be a disease, an experimental design, or a research area."
    st.markdown(_render_msg("Assistant", msg))
    st.session_state.conversation.history.append({"Assistant": msg})


def _get_context():
    st.session_state.mode = "chat"
    st.session_state.conversation.setup(st.session_state.input)
    context_response = f"You have selected `{st.session_state.conversation.context}` as your context. The model will be with you shortly. Please enter your questions below."
    st.session_state.conversation.history.append(
        {"Assistant": context_response}
    )
    st.markdown(f"`Assistant`: {context_response}")


def _get_response():
    prompt = _render_msg(
        st.session_state.conversation.user_name, st.session_state.input
    )
    response = _render_msg(
        "ChatGSE",
        st.session_state.conversation.query(st.session_state.input),
    )
    st.markdown(prompt)
    st.markdown(response)


def submit():
    st.session_state.input = st.session_state.widget
    st.session_state.widget = ""


st.set_page_config(
    page_title="ChatGSE",
    page_icon=":robot_face:",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("ChatGSE")


if "conversation" not in st.session_state:
    st.markdown(
        """
        `Assistant`: Welcome to `ChatGSE`. I am the model's assistant, and we will be performing some initial setup. To get started, could you please tell me your name?
        """
    )
else:
    for item in st.session_state.conversation.history:
        for role, msg in item.items():
            st.write(_render_msg(role, msg))

if "input" not in st.session_state:
    st.session_state.input = ""

if "mode" not in st.session_state:
    st.session_state.mode = "name"

if st.session_state.input:
    if st.session_state.mode == "name":
        _get_user_name()

    elif st.session_state.mode == "context":
        _get_context()

    elif st.session_state.mode == "chat":
        _get_response()

st.text_input(
    "Input:",
    on_change=submit,
    key="widget",
    placeholder="Enter text here.",
)
