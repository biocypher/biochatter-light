# app.py: streamlit chat app for contextualisation of biomedical results
import os
import pandas as pd
import streamlit as st
from _llm_connect import Conversation


def _render_msg(role: str, msg: str):
    return f"`{role}`: {msg}"


def _write_and_history(role: str, msg: str):
    st.markdown(_render_msg(role, msg))
    st.session_state.conversation.history.append({role: msg})


def _get_user_name():
    st.session_state.mode = "context"
    st.session_state["conversation"] = Conversation(
        user_name=st.session_state.input
    )
    msg = f"Thank you, `{st.session_state.conversation.user_name}`! What is the context of your inquiry? For instance, this could be a disease, an experimental design, or a research area."
    _write_and_history("Assistant", msg)


def _get_context():
    st.session_state.mode = "perturbation"
    st.session_state.conversation.setup(st.session_state.input)
    context_response = f"You have selected `{st.session_state.conversation.context}` as your context."
    _write_and_history("Assistant", context_response)


def _tool_input() -> pd.DataFrame:
    """
    Methods to detect various inputs from analytic tools; decoupler, PROGENy,
    CORNETO, GSEA, etc. Flat files on disk; what else?
    """
    if not os.path.exists("progeny.csv"):
        # return empty dataframe
        return pd.DataFrame()

    with open("progeny.csv") as f:
        df = pd.read_csv(f)

    return df


def _ask_for_perturbation():
    df = _tool_input()

    if df.empty:
        st.session_state.mode = "perturbation_manual"
        msg = "I am not detecting input from an analytic tool. Please provide a list of biological entities (activities of pathways or transcription factors, expression of transcripts or proteins), optionally with directional information and/or a contrast."
        _write_and_history("Assistant", msg)
        return

    else:
        st.session_state.mode = "perturbation_tool"

        _write_and_history(
            "Assistant",
            "I have detected input from an analytic tool. Here it is:",
        )

        st.markdown(df.to_markdown())
        st.session_state.conversation.history.append({"tool": df.to_markdown()})

        _write_and_history(
            "Assistant",
            "Would you like to provide additional information, for instance on a contrast or experimental design? If so, please enter it below; if not, please enter 'no'.",
        )

        st.session_state.conversation.setup_perturbation_tool(df.to_json())


def _get_perturbation_tool():
    st.session_state.mode = "chat"

    if str(st.session_state.input).lower() in ["n", "no", "no."]:
        msg = "Okay, I will use the information from the tool. Please enter your questions below."
        _write_and_history("Assistant", msg)
        return

    st.session_state.conversation.messages.append(
        {
            "role": "user",
            "content": st.session_state.input,
        }
    )
    perturbation_response = (
        "Thank you! You have provided additional perturbation information:\n"
        f"`{st.session_state.input}`\n"
        "The model will be with you shortly. Please enter your questions below."
    )
    _write_and_history("Assistant", perturbation_response)


def _get_perturbation_manual():
    st.session_state.mode = "chat"

    st.session_state.conversation.setup_perturbation_manual(
        st.session_state.input
    )
    perturbation_response = (
        "Thank you! You have provided unstructured perturbation information:\n"
        f"`{st.session_state.conversation.perturbation}`\n"
        "The model will be with you shortly. Please enter your questions below."
    )
    _write_and_history("Assistant", perturbation_response)


def _get_response():
    _write_and_history(
        st.session_state.conversation.user_name, st.session_state.input
    )

    response, correction = st.session_state.conversation.query(
        st.session_state.input
    )

    if correction:
        _write_and_history("ChatGSE", response)
        _write_and_history("Correcting agent", correction)

    else:
        _write_and_history("ChatGSE", response)


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

    `Assistant`: Welcome to `ChatGSE`, a tool to rapidly contextualise common
    end results of biomedical analyses. It works by setting up a
    topic-constrained conversation with a pre-trained language model. The agents
    you will be talking to are an `Assistant` (which is me, a pre-programmed
    conversational algorithm), a `ChatGSE` model, which is a pre-trained
    language model with instructions aimed at specifically improving the quality
    of biomedical answers, and a `Correcting agent`, which is a separate
    pre-trained language model with the task of catching and correcting false
    information conveyed by the primary model. You will only see the `Correcting
    agent` if it detects that the `ChatGSE` model has made a mistake. In
    general, even though we try our best to avoid mistakes using the
    correctional agent and internal safeguards, the general limitations of the
    used language model apply, which means that the statements made can
    sometimes be incorrect or misleading.
    
    `Assistant`: As mentioned, I am the model's assistant, and we will be going
    through some initial setup steps. To get started, could you please tell me
    your name?
    
    """
)

if st.session_state.get("conversation"):
    for item in st.session_state.conversation.history:
        for role, msg in item.items():
            if role == "tool":
                st.markdown(msg)
            else:
                st.markdown(_render_msg(role, msg))

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

    elif st.session_state.mode == "perturbation_tool":
        _get_perturbation_tool()

    elif st.session_state.mode == "perturbation_manual":
        _get_perturbation_manual()

    elif st.session_state.mode == "chat":
        _get_response()

st.text_input(
    "Input:",
    on_change=submit,
    key="widget",
    placeholder="Enter text here.",
)
