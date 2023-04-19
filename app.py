# app.py: streamlit chat app for contextualisation of biomedical results
import streamlit as st
from chatgse._interface import ChatGSE


def main():
    # Setup
    if not st.session_state.get("cg"):
        st.session_state.cg = ChatGSE()
    cg = st.session_state.cg
    cg._display_init()
    cg._display_history()

    with st.sidebar:
        st.file_uploader(
            "Upload tool data",
            type=["csv", "tsv", "txt"],
            key="tool_data",
            accept_multiple_files=True,
        )

    # Logic
    if not st.session_state.get("mode"):
        st.session_state.mode = cg._check_for_api_key()
        with open("chatgse-logs.txt", "a") as f:
            f.write("--- NEW SESSION ---\n")

    if st.session_state.input:
        if st.session_state.mode == "key":
            st.session_state.mode = cg._get_api_key()

        elif st.session_state.mode == "name":
            st.session_state.mode = cg._get_user_name()

        elif st.session_state.mode == "context":
            st.session_state.mode = cg._get_context()
            st.session_state.mode = cg._ask_for_data_input()

        elif st.session_state.mode == "data_input":
            st.session_state.mode = cg._get_data_input()

        elif st.session_state.mode == "data_input_tool_additional":
            st.session_state.mode = cg._get_data_input_tool_additional()

        elif st.session_state.mode == "data_input_manual":
            st.session_state.mode = cg._get_data_input_manual()

        elif st.session_state.mode == "chat":
            cg._get_response()

    # Chat box
    cg._text_input()


if __name__ == "__main__":
    main()
