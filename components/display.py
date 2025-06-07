import streamlit as st

ss = st.session_state

from components.constants import (
    HOW_MESSAGES,
    WHAT_MESSAGES,
)

from .handlers import shuffle_messages


def show_about_section():
    if not ss.get("what_messages"):
        ss.what_messages = WHAT_MESSAGES

    if not ss.get("how_messages"):
        ss.how_messages = HOW_MESSAGES

    what, how = st.columns(2)
    with what:
        st.markdown(
            "### "
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "ℹ️ What"
        )
        for i in range(3):
            msg = ss.what_messages[i]
            st.button(
                msg,
                use_container_width=True,
                on_click=shuffle_messages,
                args=(ss.what_messages, i),
            )
    with how:
        st.markdown(
            "### "
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "🔧 How"
        )
        for i in range(3):
            msg = ss.how_messages[i]
            st.button(
                msg,
                use_container_width=True,
                on_click=shuffle_messages,
                args=(ss.how_messages, i),
            )

    st.info(
        "This is the lightweight frontend for BioChatter in pure Python. "
        "For more information on the platform, please see [our preprint](https://arxiv.org/abs/2305.06488)! "
        "If you'd like to contribute to the project, please find us on "
        "[GitHub](https://github.com/biocypher) or "
        "[Zulip](https://biocypher.zulipchat.com). We'd love to hear from you!"
    )


def waiting_for_rag_agent():
    st.info("Use the 'Retrieval-Augmented Generation' tab to embed documents.")


def display_token_usage():
    """Display current token usage without limits."""

    # Always display the token usage section
    st.markdown("### 📊 Token Usage")

    current_tokens = ss.get("token_usage", 0)
    ss.cumulative_tokens += current_tokens
    ss.token_usage = 0

    # Always display the metrics (even if 0)
    col1, col2 = st.columns(2)

    with col1:
        st.metric(label="Last Query", value=f"{current_tokens}", help="Tokens used in the most recent query")

    with col2:
        st.metric(
            label="Session Total",
            value=f"{ss.cumulative_tokens}",
            help="Total tokens used in this session",
        )
