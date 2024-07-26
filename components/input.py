import streamlit as st

ss = st.session_state

from biochatter_light._interface import community_possible
from .handlers import on_submit, use_community_key, demo_mode


def chat_line():
    """
    Renders a chat line for smaller inputs.
    """
    st.text_input(
        "Input:",
        on_change=on_submit,
        key="widget",
        placeholder="Write here. Press [Enter] to submit.",
        label_visibility="collapsed",
    )


def chat_box():
    """
    Renders a chat box for larger inputs. Used for all main chat functionality.
    """
    st.text_area(
        "Input:",
        on_change=on_submit,
        key="widget",
        placeholder=(
            "Write here. Press [Enter] for a new line, and [CTRL+Enter] or "
            "[⌘+Enter] to submit."
        ),
        label_visibility="collapsed",
    )
    if ss.get("conversation_mode") == "both" and not ss.get("embedder_used"):
        st.warning(
            "You have selected 'data and papers' as the conversation mode, but "
            "have not yet embedded any documents. Prompt injection will only "
            "be performed if you upload at least one document (in the "
            "'Retrieval-Augmented Generation' tab)."
        )


def openai_key_chat_box():
    """
    Field for entering the OpenAI API key. Not shown if the key is found in
    the environment variables. If the community key is available (i.e., we
    are running on self-hosted, connected to Redis, and have credits remaining)
    we show a button to use the community key and a button to show a demo.
    """
    if community_possible():
        demo, community, field = st.columns([1, 1, 3])

        with demo:
            st.button(
                "Show A Demonstration",
                on_click=demo_mode,
                use_container_width=True,
            )

        with community:
            st.button(
                "Use The Community Key",
                on_click=use_community_key,
                use_container_width=True,
            )

        with field:
            st.text_input(
                "OpenAI API Key:",
                on_change=on_submit,
                key="widget",
                placeholder="(sk-...) Press [Enter] to submit.",
            )

    else:
        st.text_input(
            "OpenAI API Key:",
            on_change=on_submit,
            key="widget",
            placeholder="(sk-...) Press [Enter] to submit.",
        )


def huggingface_key_chat_box():
    """
    Field for entering the Hugging Face Hub API key. Not shown if the key is
    found in the environment variables.
    """
    st.text_input(
        "Hugging Face Hub API Token:",
        on_change=on_submit,
        key="widget",
        placeholder="(hf_...)",
    )


def file_uploader():
    """
    File uploader for uploading a CSV, TSV, or TXT file containing the user's
    tool data to be used for the prompt.
    """
    st.file_uploader(
        "Upload tool data",
        type=["csv", "tsv", "txt"],
        key="tool_data",
        accept_multiple_files=True,
    )
