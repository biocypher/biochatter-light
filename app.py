# app.py: streamlit chat app for contextualisation of biomedical results
from loguru import logger
import os
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from chatgse._llm_connect import Conversation

PLEASE_ENTER_QUESTIONS = (
    "The model will be with you shortly. "
    "Please enter your questions below. "
    "These can be general, such as 'explain these results', or specific. "
    "General questions will yield more general answers, while specific "
    "questions go into more detail. You can follow up on the answers with "
    "more questions."
)
ALLOWED_TOOLS = ["decoupler", "progeny", "corneto", "gsea"]
HIDE_MENU_STYLE = """
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
        st.set_page_config(
            page_title="ChatGSE",
            page_icon=":robot_face:",
            layout="wide",
            initial_sidebar_state="expanded",
        )

        st.title("ChatGSE")
        st.markdown(HIDE_MENU_STYLE, unsafe_allow_html=True)

        st.markdown(
            """

            `Assistant`: Welcome to ``ChatGSE``, a tool to rapidly contextualise common
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
                Please enter your OpenAI API key. You can get one by signing up
                [here](https://platform.openai.com/). We will not store your
                key, and only use it for the requests made in this session. To
                prevent this message, you can set the environment variable
                `OPENAI_API_KEY` to your key.
                """
            self._write_and_history("Assistant", msg)

            return "key"

        msg = """
            As mentioned, I am the model's assistant, and we will be going
            through some initial setup steps. To get started, could you please tell me
            your name?
            """
        self._write_and_history("Assistant", msg)

        return "name"

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

            return "key"

        msg = """
            Thank you! As mentioned, I am the model's assistant, and we will be going
            through some initial setup steps. To get started, could you please tell me
            your name?
            """
        self._write_and_history("Assistant", msg)
        return "name"

    def _get_user_name(self):
        logger.info("Getting user name.")
        st.session_state.conversation.set_user_name(st.session_state.input)
        msg = (
            f"Thank you, `{st.session_state.conversation.user_name}`! "
            "What is the context of your inquiry? For instance, this could be a "
            "disease, an experimental design, or a research area."
        )
        self._write_and_history("Assistant", msg)

        return "context"

    def _get_context(self):
        logger.info("Getting context.")
        st.session_state.conversation.setup(st.session_state.input)
        context_response = (
            f"You have selected `{st.session_state.conversation.context}` "
            "as your context. Do you want to provide input files from analytic "
            "methods? If so, please provide the file names as a comma-separated "
            "list. The files should be in the `input/` folder in commonly used "
            "text file formats. If not, please enter 'no'."
        )
        self._write_and_history("Assistant", context_response)

        return "data_input"

    def _ask_for_data_input(self):
        logger.info(
            "--- Biomedical data input --- "
            "looking for structured and unstructured information."
        )

        files = st.session_state.input.split(",")
        files = [f.strip() for f in files]
        if "no" in files:
            logger.info("No tool data provided.")
            msg = (
                "Please provide a list of biological data points (activities of "
                "pathways or transcription factors, expression of transcripts or "
                "proteins), optionally with directional information and/or a "
                "contrast."
            )
            self._write_and_history("Assistant", msg)
            return "data_input_manual"

        else:
            logger.info("Tool data provided.")
            return self._get_data_input_tool(files)

    def _get_data_input_tool(self, files: list) -> dict:
        """
        Methods to detect various inputs from analytic tools; decoupler, PROGENy,
        CORNETO, GSEA, etc. Flat files on disk; what else?
        """
        logger.info("Tool data provided.")
        dfs = {}
        for fl in files:
            tool = fl.split(".")[0]
            if not any([tool in fl for tool in ALLOWED_TOOLS]):
                self._write_and_history(
                    "Assistant",
                    f"Sorry, `{tool}` is not among the supported tools "
                    f"({ALLOWED_TOOLS}). Please check the spelling and try again.",
                )
                continue

            if not os.path.exists(f"input/{fl}"):
                self._write_and_history(
                    "Assistant",
                    f"Sorry, I could not find the file `{fl}` in the `input/` "
                    "folder. Please check the spelling and try again.",
                )
                continue

            logger.info(f"Reading {fl}")
            with open(f"input/{fl}") as f:
                df = pd.read_csv(f)
                dfs[tool] = df

        self._write_and_history(
            "Assistant",
            f"I have detected input from {len(dfs)} supported analytic tool(s).",
        )

        for tool, df in dfs.items():
            self._write_and_history(
                "Assistant",
                f"{tool} results",
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
            st.session_state.conversation.setup_data_input_tool(
                df.to_json(), tool
            )

        self._write_and_history(
            "Assistant",
            "Would you like to provide additional information, for instance on a "
            "contrast or experimental design? If so, please enter it below; if "
            "not, please enter 'no'.",
        )

        return "data_input_tool_additional"

    def _get_data_input_tool_additional(self):
        logger.info("Asking for additional data input info.")

        if str(st.session_state.input).lower() in ["n", "no", "no."]:
            logger.info("No additional data input provided.")
            msg = (
                "Okay, I will use the information from the tool. "
                f"{PLEASE_ENTER_QUESTIONS}"
            )
            self._write_and_history("Assistant", msg)
            return "chat"

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
        self._write_and_history("Assistant", data_input_response)

        return "chat"

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

    def _text_input(self):
        st.text_input(
            "Input:",
            on_change=submit,
            key="widget",
            placeholder="Enter text here.",
        )
        if "counter" not in st.session_state:
            st.session_state["counter"] = 0
        components.html(
            f"""
            <div></div>
            <p>{st.session_state.counter}</p>
            <script>
                var input = window.parent.document.querySelectorAll("input[type=text]");
                for (var i = 0; i < input.length; ++i) {{
                    input[i].focus();
                }}
            </script>
            """,
            height=15,
        )


def submit():
    st.session_state.input = st.session_state.widget
    st.session_state.widget = ""


def main():
    # Setup
    if not st.session_state.get("cg"):
        st.session_state.cg = ChatGSE()
    cg = st.session_state.cg
    cg._display_init()
    cg._display_history()

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

        elif st.session_state.mode == "data_input":
            st.session_state.mode = cg._ask_for_data_input()

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
