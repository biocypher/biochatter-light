import streamlit as st

ss = st.session_state


def correcting_agent_panel():
    ss.correct = st.checkbox(
        "Use the correcting agent to catch and correct false information",
        value=ss.correct,
    )
    ss.split_correction = st.checkbox(
        "Split the response into sentences for correction",
        value=ss.split_correction,
    )

    if ss.get("conversation"):
        if ss.split_correction != ss.conversation.split_correction:
            ss.conversation.split_correction = ss.split_correction
        if ss.correct != ss.conversation.correct:
            ss.conversation.correct = ss.correct

    test_correct = st.text_area(
        "Test correction functionality here:",
        placeholder=(
            "Enter a false statement to prompt a correction. Press [Enter] for "
            "a new line, and [CTRL+Enter] or [⌘+Enter] to submit."
        ),
    )

    if test_correct:
        if not ss.get("conversation"):
            st.write("No model loaded. Please load a model first.")
            return

        correction = ss.conversation._correct_response(test_correct)

        if str(correction).lower() in ["ok", "ok."]:
            st.success("The model found no correction to be required.")
        else:
            st.error(
                f"The model found the following correction: `{correction}`"
            )
