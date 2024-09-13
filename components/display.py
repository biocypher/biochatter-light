import streamlit as st

ss = st.session_state

from .handlers import get_remaining_tokens, shuffle_messages

from components.constants import (
    WHAT_MESSAGES,
    HOW_MESSAGES,
)


def remaining_tokens():
    """
    Display remaining community tokens for the day coloured by percentage.
    """
    rt = get_remaining_tokens()
    col = ":green" if rt > 25 else ":orange" if rt > 0 else ":red"
    pct = f"{rt:.1f}"
    st.markdown(f"Daily community tokens remaining: {col}[{pct}%]")
    st.progress(rt / 100)


def display_token_usage():
    """
    Display the token usage for the current conversation.
    """
    with st.expander("Token usage", expanded=True):
        maximum = ss.get("token_limit", 0)

        if not ss.get("token_usage"):
            ss.token_usage = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }
        elif isinstance(ss.token_usage, int):
            ss.token_usage = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": ss.token_usage,
            }

        st.markdown(
            f"""
            Last query: {ss.token_usage["prompt_tokens"]}

            Last response: {ss.token_usage["completion_tokens"]}

            Total usage: {ss.token_usage["total_tokens"]}

            Model maximum: {maximum}
            """
        )

        # display warning within 20% of maximum
        if ss.token_usage["total_tokens"] > maximum * 0.8:
            st.warning(
                "You are approaching the maximum number of tokens allowed by "
                "the model. Please consider using a different model or "
                "reducing the number of queries. You can reset the app to "
                "start over the conversation."
            )


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
