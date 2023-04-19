# app.py: streamlit chat app for contextualisation of biomedical results
from loguru import logger
import os
import pandas as pd
import streamlit as st
from chatgse._llm_connect import Conversation

PLEASE_ENTER_QUESTIONS = "The model will be with you shortly. Please enter your questions below. These can be general ('explain these results') or specific."


def _render_msg(role: str, msg: str):
    return f"`{role}`: {msg}"


def _write_and_history(role: str, msg: str):
    logger.info(f"Writing message from {role}: {msg}")
    st.markdown(_render_msg(role, msg))
    st.session_state.conversation.history.append({role: msg})
    with open("chatgse-logs.txt", "a") as f:
        f.write(f"{role}: {msg}\n")


def _get_user_name():
    logger.info("Getting user name.")
    st.session_state.mode = "context"
    st.session_state["conversation"] = Conversation(
        user_name=st.session_state.input
    )
    msg = f"Thank you, `{st.session_state.conversation.user_name}`! What is the context of your inquiry? For instance, this could be a disease, an experimental design, or a research area."
    _write_and_history("Assistant", msg)


def _get_context():
    logger.info("Getting context.")
    st.session_state.mode = "data_input"
    st.session_state.conversation.setup(st.session_state.input)
    context_response = f"You have selected `{st.session_state.conversation.context}` as your context. Do you want to provide input files from analytic methods? If so, please provide the file names as a comma-separated list. The files should be in the `input/` folder in commonly used text file formats. If not, please enter 'no'."
    _write_and_history("Assistant", context_response)


ALLOWED_TOOLS = ["decoupler", "progeny", "corneto", "gsea"]


def _ask_for_data_input():
    logger.info(
        "--- Biomedical data input --- looking for structured and unstructured information."
    )

    files = st.session_state.input.split(",")
    files = [f.strip() for f in files]
    if "no" in files:
        logger.info("No tool data provided.")
        st.session_state.mode = "data_input_manual"
        msg = "Please provide a list of biological data points (activities of pathways or transcription factors, expression of transcripts or proteins), optionally with directional information and/or a contrast."
        _write_and_history("Assistant", msg)
        return

    else:
        logger.info("Tool data provided.")
        _get_data_input_tool(files)


def _get_data_input_tool(files: list) -> dict:
    """
    Methods to detect various inputs from analytic tools; decoupler, PROGENy,
    CORNETO, GSEA, etc. Flat files on disk; what else?
    """
    logger.info("Tool data provided.")
    st.session_state.mode = "data_input_tool_additional"
    dfs = {}
    for fl in files:
        tool = fl.split(".")[0]
        if not any([tool in fl for tool in ALLOWED_TOOLS]):
            _write_and_history(
                "Assistant",
                f"Sorry, `{tool}` is not among the supported tools ({ALLOWED_TOOLS}). Please check the spelling and try again.",
            )
            continue

        if not os.path.exists(f"input/{fl}"):
            _write_and_history(
                "Assistant",
                f"Sorry, I could not find the file `{fl}` in the `input/` folder. Please check the spelling and try again.",
            )
            continue

        logger.info(f"Reading {fl}")
        with open(f"input/{fl}") as f:
            df = pd.read_csv(f)
            dfs[tool] = df

    _write_and_history(
        "Assistant",
        f"I have detected input from {len(dfs)} supported analytic tools.",
    )

    for tool, df in dfs.items():
        _write_and_history(
            "Assistant",
            f"### {tool}:",
        )
        st.markdown(
            f"""
            ```
            {df.to_markdown()}
            """
        )
        st.session_state.conversation.history.append({"tool": df.to_markdown()})
        logger.info("<Tool data displayed.>")
        st.session_state.conversation.setup_data_input_tool(df.to_json(), tool)

    _write_and_history(
        "Assistant",
        "Would you like to provide additional information, for instance on a contrast or experimental design? If so, please enter it below; if not, please enter 'no'.",
    )


def _get_data_input_tool_additional():
    logger.info("Asking for additional data input info.")
    st.session_state.mode = "chat"

    if str(st.session_state.input).lower() in ["n", "no", "no."]:
        logger.info("No additional data input provided.")
        msg = f"Okay, I will use the information from the tool. {PLEASE_ENTER_QUESTIONS}"
        _write_and_history("Assistant", msg)
        return

    logger.info("Additional data input provided.")
    st.session_state.conversation.messages.append(
        {
            "role": "user",
            "content": st.session_state.input,
        }
    )
    data_input_response = (
        "Thank you! You have provided additional data input:\n"
        f"`{st.session_state.input}`\n"
        f"{PLEASE_ENTER_QUESTIONS}"
    )
    _write_and_history("Assistant", data_input_response)


def _get_data_input_manual():
    logger.info("No tool info provided. Getting manual data input.")
    st.session_state.mode = "chat"

    st.session_state.conversation.setup_data_input_manual(
        st.session_state.input
    )
    data_input_response = (
        "Thank you! You have provided unstructured data input:\n"
        f"`{st.session_state.conversation.data_input}`\n"
        f"{PLEASE_ENTER_QUESTIONS}"
    )
    _write_and_history("Assistant", data_input_response)


def _get_response():
    logger.info("Getting response from LLM.")
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
    correcting agent and internal safeguards, the general limitations of the
    used Large Language Model apply, which means that the statements made can
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
                st.markdown(
                    f"""
                    ```
                    {msg}
                    """
                )
            else:
                st.markdown(_render_msg(role, msg))

if "input" not in st.session_state:
    st.session_state.input = ""

if "mode" not in st.session_state:
    st.session_state.mode = "name"

if st.session_state.input:
    if st.session_state.mode == "name":
        with open("chatgse-logs.txt", "a") as f:
            f.write("--- NEW SESSION ---\n")
        _get_user_name()

    elif st.session_state.mode == "context":
        _get_context()

    elif st.session_state.mode == "data_input":
        st.session_state.files = _ask_for_data_input()

    elif st.session_state.mode == "data_input_tool_additional":
        _get_data_input_tool_additional()

    elif st.session_state.mode == "data_input_manual":
        _get_data_input_manual()

    elif st.session_state.mode == "chat":
        _get_response()

st.text_input(
    "Input:",
    on_change=submit,
    key="widget",
    placeholder="Enter text here.",
)
