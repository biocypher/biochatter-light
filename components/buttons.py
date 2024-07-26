from biochatter_light._interface import BioChatterLight
from .handlers import (
    reset_app,
    data_input_yes,
    data_input_no,
    use_community_key,
    demo_mode,
    demo_next,
    get_remaining_tokens,
    community_tokens_refresh_in,
    set_both_mode,
    set_data_mode,
    set_papers_mode,
)

import streamlit as st

ss = st.session_state


def download_chat_history(bcl: BioChatterLight):
    """
    Button to download the chat history as a JSON file.

    Args:
        bcl: current biochatter-light instance
    """
    bcl.update_json_history()
    st.download_button(
        label="Download Chat History",
        data=ss.json_history,
        file_name="chat_history.json",
        mime="application/json",
        use_container_width=True,
    )


def download_complete_history(bcl: BioChatterLight):
    """
    Button to download the complete message history (i.e., including the
    system prompts) as a JSON file.

    Args:
        bcl: current biochatter-light instance
    """
    d = bcl.complete_history()

    if d == "{}":
        st.download_button(
            label="Download Message History",
            data="",
            use_container_width=True,
            disabled=True,
        )
        return

    st.download_button(
        label="Download Message History",
        data=d,
        file_name="complete_history.json",
        mime="application/json",
        use_container_width=True,
    )


def reset_button():
    """
    Button to reset the entire app.
    """
    st.button(
        "♻️ Reset App",
        on_click=reset_app,
        use_container_width=True,
    )


def demo_next_button():
    """
    Show the "Next Step" button for the demo mode.
    """
    st.button("Next Step", on_click=demo_next, use_container_width=True)


def community_select():
    """
    Show buttons to select the community key or the demo mode (which also
    uses the community key).
    """
    if not get_remaining_tokens() > 0:
        st.warning(
            "No community tokens remaining for the day. "
            f"Refreshes in {community_tokens_refresh_in()}."
        )
        return

    b1, b2 = st.columns([1, 1])
    with b1:
        st.button("Use Community Key", on_click=use_community_key)
    with b2:
        st.button("Show Demonstration", on_click=demo_mode)


def data_input_buttons():
    """
    Buttons for asking the user if they want to upload a file containing their
    tool data.
    """
    c1, c2 = st.columns([1, 1])
    with c1:
        st.button(
            "Yes",
            on_click=data_input_yes,
            use_container_width=True,
        )
    with c2:
        st.button(
            "No",
            on_click=data_input_no,
            use_container_width=True,
        )


def mode_select():
    data, papers, both = st.columns(3)

    ss.mode = "getting_context"

    with data:
        st.button(
            "Talk about data.",
            use_container_width=True,
            on_click=set_data_mode,
        )

    with papers:
        st.button(
            "Talk about papers / notes.",
            use_container_width=True,
            on_click=set_papers_mode,
            disabled=ss.online,
        )

    with both:
        st.button(
            "Talk about data and papers / notes.",
            use_container_width=True,
            on_click=set_both_mode,
            disabled=ss.online,
        )

    if ss.online:
        st.info(
            "Retrieval-Augmented Generation is currently not available in the "
            "online version. Please use the Docker Compose setup in our "
            "[GitHub repository](https://github.com/biocypher/biochatter-light#-retrieval-augmented-generation--in-context-learning) "
            "to run BioChatter Light locally and use this feature."
        )
