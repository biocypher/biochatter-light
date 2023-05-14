# ChatGSE user interface class
# manage the different roles / stages of conversation

import json
import os
from loguru import logger
import pandas as pd
import streamlit as st
from chatgse._llm_connect import GptConversation, BloomConversation

ss = st.session_state


# ENVIRONMENT VARIABLES
def community_possible():
    return "OPENAI_COMMUNITY_KEY" in os.environ and "REDIS_PW" in os.environ


API_KEY_REQUIRED = "The currently selected model requires an API key."
COMMUNITY_SELECT = (
    "You can use your own [OpenAI API "
    "key](https://platform.openai.com/account/api-keys), or try the platform "
    "using our community key by pressing the `Use The Community Key` button."
)
DEMO_MODE = (
    "You can also try a `Demonstration` setup with toy data by pressing the "
    "first button below. After guiding you through the initial steps, this "
    "will also take you to a functional chat using the community key."
)
API_KEY_SUCCESS = (
    "Hello! I am the model's assistant. For more explanation, "
    "please see the :red[About] text in the sidebar. We will now "
    "be going through some initial setup steps together. To get "
    "started, could you please tell me your name?"
)
PLEASE_ENTER_QUESTIONS = (
    "The model will be with you shortly. "
    "Please enter your questions below. "
    "These can be general, such as 'explain these results', or specific. "
    "General questions will yield more general answers, while specific "
    "questions go into more detail. You can follow up on the answers with "
    "more questions."
)
KNOWN_TOOLS = ["progeny", "dorothea", "gsea"]


class ChatGSE:
    def __init__(self):
        if "input" not in ss:
            ss.input = ""

        if "history" not in ss:
            ss.history = []

        if "setup_messages" not in ss:
            ss.setup_messages = []

    def _display_setup(self):
        """
        Renders setup messages on each reload. Conditionally shown only at setup
        stage.
        """
        for item in ss.setup_messages:
            for role, msg in item.items():
                st.markdown(self._render_msg(role, msg))

    def _display_history(self):
        """
        Renders the history of the conversation on each reload. Also saves a
        JSON to the session state for download.
        """
        for item in ss.history:
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

    def update_json_history(self):
        """
        Write ss.history to JSON and put it into session state.
        """
        ss.json_history = json.dumps(ss.history)

    @staticmethod
    def _render_msg(role: str, msg: str):
        return f"`{role}`: {msg}"

    def _history_only(self, role: str, msg: str):
        ss.history.append({role: msg})

    def _setup_only(self, role: str, msg: str):
        ss.setup_messages.append({role: msg})

    def _write_and_history(self, role: str, msg: str):
        logger.info(f"Writing message from {role}: {msg}")
        st.markdown(self._render_msg(role, msg))
        ss.history.append({role: msg})

    def _write_and_setup(self, role: str, msg: str):
        logger.info(f"Writing message from {role}: {msg}")
        st.markdown(self._render_msg(role, msg))
        ss.setup_messages.append({role: msg})

    def set_model(self, model_name: str):
        """
        Set the LLM model to use for the conversation.
        """
        if ss.get("conversation"):
            logger.warning("Conversation already exists, overwriting.")

        if model_name == "gpt-3.5-turbo":
            ss.conversation = GptConversation()
        elif model_name == "bigscience/bloom":
            ss.conversation = BloomConversation()

    def _check_for_api_key(self, write: bool = True):
        """
        Upon app start, check for the validity of any API key in the session
        state. If there is none, or the given is invalid, ask again.

        Args:
            write: Whether to write the message or only append it to the
            history (for app logic reasons).

        Returns:
            The next state to go to (either "getting_key" or "getting_name")
        """
        if ss.primary_model == "gpt-3.5-turbo":
            key = ss.get("openai_api_key")
            ss.token_limit = 4097
        elif ss.primary_model == "bigscience/bloom":
            key = ss.get("huggingfacehub_api_key")
            ss.token_limit = 1000

        if not key:
            if ss.primary_model == "gpt-3.5-turbo":
                msg = f"{API_KEY_REQUIRED} "
                if community_possible():
                    msg += f"{COMMUNITY_SELECT} "
                msg += (
                    "You can get a key by signing up "
                    "[here](https://platform.openai.com/) and enabling "
                    "billing. We will not store your key, and only use it for "
                    "the requests made in this session. "
                )
                if community_possible():
                    msg += (
                        "If you use community credits, please be considerate of "
                        "other users; if you use the platform extensively, "
                        "please use your own key. "
                    )
                msg += (
                    "Using GPT-3.5-turbo, a full conversation (4000 tokens) "
                    f"costs about 0.01 USD. "
                )
                if community_possible():
                    msg += f"{DEMO_MODE}"
                self._setup_only("📎 Assistant", msg)
                ss.show_community_select = True

            elif ss.primary_model == "bigscience/bloom":
                msg = (
                    f"{API_KEY_REQUIRED} Please enter your [HuggingFace Hub "
                    "API key](https://huggingface.co/settings/token). You "
                    "can get one by signing up "
                    "[here](https://huggingface.co/). We will not store your "
                    "key, and only use it for the requests made in this "
                    "session. If you run the app locally, you can prevent "
                    "this message by setting the environment variable "
                    "`HUGGINGFACEHUB_API_TOKEN` to your key."
                )
                self._setup_only("📎 Assistant", msg)

            return "getting_key"

        success = self._try_api_key(key)

        if not success:
            msg = (
                "The API key in your environment is not valid. Please enter a "
                "valid key."
            )
            self._setup_only("📎 Assistant", msg)

            return "getting_key"

        if not ss.get("asked_for_name"):
            ss.asked_for_name = True
            msg = f"{API_KEY_SUCCESS}"
            if write:
                self._write_and_history("📎 Assistant", msg)
            else:
                self._history_only("📎 Assistant", msg)

        ss.show_community_select = False

        return "getting_name"

    def _try_api_key(self, key: str = None):
        success = ss.conversation.set_api_key(
            key,
            ss.user,
        )
        if not success:
            return False
        return True

    def _get_api_key(self, key: str = None):
        logger.info("Getting API Key.")
        sucess = self._try_api_key(key)
        if not sucess:
            msg = (
                "The API key you entered is not valid. Please enter a valid "
                "key."
            )
            self._write_and_setup("📎 Assistant", msg)

            return "getting_key"

        if not ss.get("asked_for_name"):
            ss.asked_for_name = True
            msg = f"{API_KEY_SUCCESS}"
            self._write_and_history("📎 Assistant", msg)

        ss.show_community_select = False

        return "getting_name"

    def _ask_for_user_name(self):
        msg = f"{API_KEY_SUCCESS}"
        self._write_and_history("📎 Assistant", msg)

        return "getting_name"

    def _get_user_name(self):
        logger.info("Getting user name.")
        name = ss.input
        ss.conversation.set_user_name(name)
        self._write_and_history(
            name,
            name,
        )
        msg = (
            f"Thank you, `{name}`! "
            "What is the context of your inquiry? For instance, this could be a "
            "disease, an experimental design, or a research area."
        )
        self._write_and_history("📎 Assistant", msg)

        return "getting_context"

    def _get_context(self):
        logger.info("Getting context.")
        self._write_and_history(
            ss.conversation.user_name,
            ss.input,
        )
        ss.conversation.setup(ss.input)

    def _ask_for_data_input(self):
        if not ss.get("tool_data"):
            msg1 = (
                f"You have selected `{ss.conversation.context}` as your "
                "context. Do you want to provide input files from analytic "
                "methods? They will not be stored or analysed beyond your "
                "queries. If so, please provide the files by uploading them in "
                "the sidebar and press 'Yes' once you are finished. I will "
                "recognise methods if their names are mentioned in the file "
                "name. These are the tools I am familiar with: "
                f"{', '.join([f'`{name}`' for name in KNOWN_TOOLS])}. Please "
                "keep in mind that all data you provide will count towards the "
                f"token usage of your conversation prompt. The limit of the "
                f"currently active model is {ss.token_limit}."
            )
            self._write_and_history("📎 Assistant", msg1)
            msg2 = (
                "If you don't want to provide any files, please press 'No'. "
                "You will still be able to provide free text information about "
                "your results later. Any free text you provide will also not "
                "be stored or analysed beyond your queries."
            )
            self._write_and_history("📎 Assistant", msg2)
            return "getting_data_file_input"

        file_names = [f"`{f.name}`" for f in ss.tool_data]

        msg1 = (
            f"You have selected `{ss.conversation.context}` as your context. "
            "I see you have already uploaded some data files: "
            f"{', '.join(file_names)}. If you wish to add more, please do so "
            "now. Once you are done, please press 'Yes'."
        )
        self._write_and_history("📎 Assistant", msg1)

        return "getting_data_file_input"

    def _get_data_input(self):
        logger.info("--- Biomedical data input ---")

        if not ss.get("tool_data") and not "demo" in ss.get("mode"):
            msg = (
                "No files detected. Please upload your files in the sidebar, "
                "or press 'No' to continue without providing any files."
            )
            self._write_and_history("📎 Assistant", msg)
            return "getting_data_file_input"

        if not ss.get("started_tool_input"):
            ss.started_tool_input = True

            logger.info("Tool data provided.")

            # mock for demo mode
            if "demo" in ss.get("mode"):
                ss.tool_list = ss.demo_tool_data
            else:
                ss.tool_list = ss.tool_data

            msg = (
                "Thank you! I have read the following "
                f"{len(ss.tool_list)} files: "
                f"{', '.join([f'`{f.name}`' for f in ss.tool_list])}."
            )
            self._write_and_history("📎 Assistant", msg)

        if not ss.get("read_tools"):
            ss.read_tools = []

        if len(ss.read_tools) == len(ss.tool_list):
            msg = (
                "I have read all the files you provided. "
                f"{PLEASE_ENTER_QUESTIONS}"
            )
            self._write_and_history("📎 Assistant", msg)
            return "chat"

        for fl in ss.tool_list:
            tool = fl.name.split(".")[0].lower()
            if tool in ss.read_tools:
                continue

            if "tsv" in fl.name:
                df = pd.read_csv(fl, sep="\t")
            else:
                df = pd.read_csv(fl)
            ss.read_tools.append(tool)

            self._write_and_history(
                "📎 Assistant",
                f"`{tool}` results",
            )
            st.markdown(
                f"""
                ```
                {df.to_markdown()}
                """
            )

            ss.history.append({"tool": df.to_markdown()})
            logger.info("<Tool data displayed.>")

            if not any([tool in fl.name for tool in KNOWN_TOOLS]):
                self._write_and_history(
                    "📎 Assistant",
                    f"Sorry, `{tool}` is not among the tools I know "
                    f"({KNOWN_TOOLS}). Please provide information about the "
                    "data below (what are rows and columns, what are the "
                    "values, etc.). Please try to be as specific as possible.",
                )
                return "getting_data_file_description"

            ss.conversation.setup_data_input_tool(df.to_json(), tool)

            self._write_and_history(
                "📎 Assistant",
                "Would you like to provide additional information, for instance "
                "on a contrast or experimental design? If so, please enter it "
                "below; if not, please enter 'no'.",
            )

            return "getting_data_file_description"

    def _get_data_file_description(self):
        logger.info("Asking for additional data input info.")

        response = str(ss.input)
        ss.input = ""

        self._write_and_history(
            ss.conversation.user_name,
            response,
        )

        if response.lower() in ["n", "no", "no."]:
            logger.info("No additional data input provided.")
            msg = (
                "Okay, I will use the information from the tool without "
                "further specification."
            )
            self._write_and_history("📎 Assistant", msg)
            return self._get_data_input()

        logger.info("Additional data input provided.")
        ss.conversation.append_user_message(response)
        data_input_response = "Thank you for the input!"
        self._write_and_history("📎 Assistant", data_input_response)
        return self._get_data_input()

    def _ask_for_manual_data_input(self):
        logger.info("Asking for manual data input.")
        msg = (
            "Please provide a list of biological data points (activities of "
            "pathways or transcription factors, expression of transcripts or "
            "proteins), optionally with directional information and/or a "
            "contrast. Since you did not provide any tool data, please try to "
            "be as specific as possible. You can also paste `markdown` tables "
            "or other structured data here."
        )
        self._write_and_history("📎 Assistant", msg)
        return "getting_manual_data_input"

    def _get_data_input_manual(self):
        logger.info("No tool info provided. Getting manual data input.")

        ss.conversation.setup_data_input_manual(ss.input)

        self._write_and_history(
            ss.conversation.user_name,
            ss.input,
        )

        data_input_response = (
            "Thank you for the input. " f"{PLEASE_ENTER_QUESTIONS}"
        )
        self._write_and_history("📎 Assistant", data_input_response)

        return "chat"

    def _get_response(self):
        logger.info("Getting response from LLM.")

        response, token_usage, correction = ss.conversation.query(ss.input)

        if not token_usage:
            # indicates error
            msg = "The model appears to have encountered an error. " + response
            self._write_and_history("📎 Assistant", msg)
            ss.error = True

            token_usage = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }

            return response, token_usage

        self._write_and_history(ss.conversation.user_name, ss.input)

        if correction:
            self._write_and_history("💬🧬 ChatGSE", response)
            self._write_and_history("🕵️ Correcting agent", correction)

        else:
            self._write_and_history("💬🧬 ChatGSE", response)

        return response, token_usage
