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
    st.session_state.mode = "perturbation"
    st.session_state.conversation.setup(st.session_state.input)
    context_response = f"You have selected `{st.session_state.conversation.context}` as your context."
    st.session_state.conversation.history.append(
        {"Assistant": context_response}
    )
    st.markdown(_render_msg("Assistant", context_response))


def _tool_input():
    return False


def _ask_for_perturbation():
    st.session_state.mode = "perturbation"
    if not _tool_input():
        msg = "I am not detecting input from an analytic tool. Please provide a list of biological entities (activities of pathways or transcription factors, expression of transcripts or proteins), optionally with directional information and/or a contrast."
        st.markdown(_render_msg("Assistant", msg))
        st.session_state.conversation.history.append({"Assistant": msg})


def _get_perturbation():
    st.session_state.mode = "chat"
    st.session_state.conversation.setup_perturbation(st.session_state.input)
    perturbation_response = (
        "Thank you! You have provided unstructured perturbation information:\n"
        f"`{st.session_state.conversation.perturbation}`\n"
        "The model will be with you shortly. Please enter your questions below."
    )
    st.session_state.conversation.history.append(
        {"Assistant": perturbation_response}
    )
    st.markdown(_render_msg("Assistant", perturbation_response))


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


st.markdown(
    """
    `Assistant`: Welcome to `ChatGSE`. I am the model's assistant, and we will be performing some initial setup. To get started, could you please tell me your name?
    """
)

if st.session_state.get("conversation"):
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
        _ask_for_perturbation()

    elif st.session_state.mode == "perturbation":
        _get_perturbation()

    elif st.session_state.mode == "chat":
        _get_response()

st.text_input(
    "Input:",
    on_change=submit,
    key="widget",
    placeholder="Enter text here.",
)
