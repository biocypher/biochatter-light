# user interface class for ChatGSE
from loguru import logger
import os
import pandas as pd
import streamlit as st
from chatgse._llm_connect import Conversation


PLEASE_ENTER_QUESTIONS = (
    "The model will be with you shortly. "
    "Please enter your questions below. "
    "These can be general, such as 'explain these results', or specific. "
    "General questions will yield more general answers, while specific "
    "questions go into more detail. You can follow up on the answers with "
    "more questions."
)
KNOWN_TOOLS = ["decoupler", "progeny", "corneto", "gsea"]
HIDE_MENU_MOD_FOOTER = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
footer:after {
    content:'Made with Streamlit by Sebastian Lobentanzer, Copyright 2023, Heidelberg University';
    visibility: visible;
    display: block;
    height: 50px;
    clear: both;
    color: darkgrey;
    }
</style>
"""


class ChatGSE:
    def __init__(self):
        if "input" not in st.session_state:
            st.session_state.input = ""

        if "conversation" not in st.session_state:
            st.session_state.conversation = Conversation()

    def _display_init(self):
        st.markdown(HIDE_MENU_MOD_FOOTER, unsafe_allow_html=True)

        st.markdown(
            """

            `Assistant`: Welcome to ``ChatGSE``!
            
            """
        )

    def _display_history(self):
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
                    st.markdown(self._render_msg(role, msg))

    @staticmethod
    def _render_msg(role: str, msg: str):
        return f"`{role}`: {msg}"

    def _write_and_history(self, role: str, msg: str):
        logger.info(f"Writing message from {role}: {msg}")
        st.markdown(self._render_msg(role, msg))
        st.session_state.conversation.history.append({role: msg})
        with open("chatgse-logs.txt", "a") as f:
            f.write(f"{role}: {msg}\n")

    def _check_for_api_key(self):
        key = os.getenv("OPENAI_API_KEY")

        if not key:
            msg = """
                Please enter your [OpenAI API
                key](https://platform.openai.com/account/api-keys). You can get
                one by signing up [here](https://platform.openai.com/). We will
                not store your key, and only use it for the requests made in
                this session. To prevent this message, you can set the
                environment variable `OPENAI_API_KEY` to your key.
                """
            self._write_and_history("Assistant", msg)

            return "getting_key"

        msg = """
            I am the model's assistant. For more explanation, please see the 
            :red[About] text in the sidebar. We will now be going through some
            initial setup steps together. To get started, could you please tell
            me your name?
            """
        self._write_and_history("Assistant", msg)

        return "getting_name"

    def _get_api_key(self):
        logger.info("Getting API Key.")
        sucess = st.session_state.conversation.set_api_key(
            st.session_state.input
        )
        if not sucess:
            msg = """
                The API key you entered is not valid. Please try again.
                """
            self._write_and_history("Assistant", msg)

            return "getting_key"

        msg = """
            Thank you! As mentioned, I am the model's assistant, and we will be going
            through some initial setup steps. To get started, could you please tell me
            your name?
            """
        self._write_and_history("Assistant", msg)
        return "getting_name"

    def _get_user_name(self):
        logger.info("Getting user name.")
        st.session_state.conversation.set_user_name(st.session_state.input)
        msg = (
            f"Thank you, `{st.session_state.conversation.user_name}`! "
            "What is the context of your inquiry? For instance, this could be a "
            "disease, an experimental design, or a research area."
        )
        self._write_and_history("Assistant", msg)

        return "getting_context"

    def _get_context(self):
        logger.info("Getting context.")
        st.session_state.conversation.setup(st.session_state.input)

    def _ask_for_data_input(self):
        if not st.session_state.tool_data:
            msg = f"""
                You have selected `{st.session_state.conversation.context}` as
                your context. Do you want to provide input files from analytic
                methods? If so, please provide the files by uploading them in
                the sidebar and press 'Yes' once you are finished. If not, 
                please press 'No'. You will still be able to provide free text
                information about your results later.
                """
            self._write_and_history("Assistant", msg)
            return "getting_data_file_input"

        file_names = [f.name for f in st.session_state.tool_data]

        msg = f"""
            You have selected `{st.session_state.conversation.context}` as
            your context. I see you have already uploaded some data files:
            {', '.join(file_names)}. If you wish to add
            more, please do so now. Once you are done, please press 'Yes'.
            """
        self._write_and_history("Assistant", msg)

        return "getting_data_file_input"

    def _get_data_input(self):
        logger.info("--- Biomedical data input ---")

        if not st.session_state.get("tool_data"):
            msg = """
                No files detected. Please upload your files in the sidebar, or
                press 'No' to continue without providing any files.
                """
            self._write_and_history("Assistant", msg)
            return "getting_data_file_input"

        if not st.session_state.get("started_tool_input"):
            st.session_state.started_tool_input = True

            logger.info("Tool data provided.")

            st.session_state.tool_list = st.session_state.tool_data

            msg = f"""
                Thank you! I have read the following 
                {len(st.session_state.tool_list)} files:
                {', '.join([f.name for f in st.session_state.tool_list])}.
                """
            self._write_and_history("Assistant", msg)

        if not st.session_state.get("read_tools"):
            st.session_state.read_tools = []

        if len(st.session_state.read_tools) == len(st.session_state.tool_list):
            msg = f"""
                I have read all the files you provided.
                {PLEASE_ENTER_QUESTIONS}
                """
            self._write_and_history("Assistant", msg)
            return "chat"

        for fl in st.session_state.tool_list:
            tool = fl.name.split(".")[0].lower()
            if tool in st.session_state.read_tools:
                continue

            if "tsv" in fl.name:
                df = pd.read_csv(fl, sep="\t")
            else:
                df = pd.read_csv(fl)
            st.session_state.read_tools.append(tool)

            self._write_and_history(
                "Assistant",
                f"""
                `{tool}` results
                """,
            )
            st.markdown(
                f"""
                ```
                {df.to_markdown()}
                """
            )

            st.session_state.conversation.history.append(
                {"tool": df.to_markdown()}
            )
            logger.info("<Tool data displayed.>")

            if not any([tool in fl.name for tool in KNOWN_TOOLS]):
                self._write_and_history(
                    "Assistant",
                    f"""
                    Sorry, `{tool}` is not among the tools I know 
                    ({KNOWN_TOOLS}). Please provide information about the data
                    below (what are rows and columns, what are the values, 
                    etc.).
                    """,
                )
                return "getting_data_file_description"

            st.session_state.conversation.setup_data_input_tool(
                df.to_json(), tool
            )

            self._write_and_history(
                "Assistant",
                """
                Would you like to provide additional information, for instance
                on a contrast or experimental design? If so, please enter it
                below; if not, please enter 'no'.
                """,
            )

            return "getting_data_file_description"

    def _get_data_file_description(self):
        logger.info("Asking for additional data input info.")

        response = str(st.session_state.input)
        st.session_state.input = ""

        if response.lower() in ["n", "no", "no."]:
            logger.info("No additional data input provided.")
            msg = """
                Okay, I will use the information from the tool without further
                specification.
                """
            self._write_and_history("Assistant", msg)
            return self._get_data_input()

        logger.info("Additional data input provided.")
        st.session_state.conversation.messages.append(
            {
                "role": "user",
                "content": response,
            }
        )
        data_input_response = (
            "Thank you! You have provided additional data input:\n"
            f"`{response}`\n"
        )
        self._write_and_history("Assistant", data_input_response)
        return self._get_data_input()

    def _ask_for_manual_data_input(self):
        logger.info("Asking for manual data input.")
        msg = """
            Please provide a list of biological data points (activities of
            pathways or transcription factors, expression of transcripts or
            proteins), optionally with directional information and/or a
            contrast. Since you did not provide any tool data, please try to be
            as specific as possible.
            """
        self._write_and_history("Assistant", msg)
        return "getting_manual_data_input"

    def _get_data_input_manual(self):
        logger.info("No tool info provided. Getting manual data input.")

        st.session_state.conversation.setup_data_input_manual(
            st.session_state.input
        )
        data_input_response = (
            "Thank you! You have provided unstructured data input:\n"
            f"`{st.session_state.conversation.data_input}`\n"
            f"{PLEASE_ENTER_QUESTIONS}"
        )
        self._write_and_history("Assistant", data_input_response)

        return "chat"

    def _get_response(self):
        logger.info("Getting response from LLM.")
        self._write_and_history(
            st.session_state.conversation.user_name, st.session_state.input
        )

        response, correction = st.session_state.conversation.query(
            st.session_state.input
        )

        if correction:
            self._write_and_history("ChatGSE", response)
            self._write_and_history("Correcting agent", correction)

        else:
            self._write_and_history("ChatGSE", response)
