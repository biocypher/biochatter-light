# ChatGSE LLM connectivity
# connect to API
# keep track of message history
# query API
# correct response
# update usage stats

import streamlit as st

ss = st.session_state

from abc import ABC, abstractmethod
import openai

from langchain.chat_models import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.llms import HuggingFaceHub

from ._stats import get_stats


class Conversation(ABC):
    """

    Use this class to set up a connection to an LLM API. Can be used to set the
    user name and API key, append specific messages for system, user, and AI
    roles (if available), set up the general context as well as manual and
    tool-based data inputs, and finally to query the API with prompts made by
    the user.

    The conversation class is expected to have a `messages` attribute to store
    the conversation, and a `history` attribute, which is a list of messages in
    a specific format for logging / printing.

    """

    def __init__(self):
        super().__init__()
        self.history = []
        self.messages = []
        self.ca_messages = []

    def set_user_name(self, user_name: str):
        self.user_name = user_name

    @abstractmethod
    def set_api_key(self, api_key: str):
        pass

    def append_ai_message(self, message: str):
        self.messages.append(
            AIMessage(
                content=message,
            ),
        )

    def append_system_message(self, message: str):
        self.messages.append(
            SystemMessage(
                content=message,
            ),
        )

    def append_user_message(self, message: str):
        self.messages.append(
            HumanMessage(
                content=message,
            ),
        )

    def setup(self, context: str):
        """
        Set up the conversation with general prompts and a context.
        """
        for msg in ss.prompts["primary_model_prompts"]:
            if msg:
                self.messages.append(
                    SystemMessage(
                        content=msg,
                    ),
                )

        for msg in ss.prompts["correcting_agent_prompts"]:
            if msg:
                self.ca_messages.append(
                    SystemMessage(
                        content=msg,
                    ),
                )

        self.context = context
        msg = f"The topic of the research is {context}."
        self.append_system_message(msg)

    def setup_data_input_manual(self, data_input: str):
        self.data_input = data_input
        msg = f"The user has given information on the data input: {data_input}."
        self.append_system_message(msg)

    def setup_data_input_tool(self, df, tool: str):
        self.data_input_tool = df

        if "progeny" in tool:
            self.append_system_message(
                ss.prompts["tool_prompts"]["progeny"].format(df=df)
            )

        elif "dorothea" in tool:
            self.append_system_message(
                ss.prompts["tool_prompts"]["dorothea"].format(df=df)
            )

        elif "gsea" in tool:
            self.append_system_message(
                ss.prompts["tool_prompts"]["gsea"].format(df=df)
            )

    def query(self, text: str):
        self.append_user_message(text)

        if ss.get("docsum"):
            if ss.docsum.use_prompt:
                self._inject_context(text)

        msg, token_usage = self._primary_query()

        if not token_usage:
            # indicates error
            return (msg, token_usage, None)

        correction = self._correct_response(msg)

        if str(correction).lower() in ["ok", "ok."]:
            return (msg, token_usage, None)

        return (msg, token_usage, correction)

    @abstractmethod
    def _primary_query(self, text: str):
        pass

    @abstractmethod
    def _correct_response(self, msg: str):
        pass

    def _inject_context(self, text: str):
        if not ss.docsum.used:
            st.info(
                "No document has been analysed yet. To use document "
                "summarisation, please analyse at least one document first."
            )
            return

        with st.spinner("Performing similarity search..."):
            statements = [
                doc.page_content
                for doc in ss.docsum.similarity_search(
                    text,
                    ss.docsum.n_results,
                )
            ]
        prompts = ss.prompts["docsum_prompts"]
        if statements:
            ss.current_statements = statements
            for i, prompt in enumerate(prompts):
                if i == len(prompts) - 1:
                    self.append_system_message(
                        prompt.format(statements=statements)
                    )
                else:
                    self.append_system_message(prompt)


class GptConversation(Conversation):
    def __init__(self):
        """
        Connect to OpenAI's GPT API and set up a conversation with the user.
        Also initialise a second conversational agent to provide corrections to
        the model output, if necessary.
        """
        super().__init__()

        self.model = "gpt-3.5-turbo"
        self.ca_model = "gpt-3.5-turbo"
        # TODO make accessible by drop-down

    def set_api_key(self, api_key: str, user: str):
        """
        Set the API key for the OpenAI API. If the key is valid, initialise the
        conversational agent. Set the user for usage statistics.
        """
        openai.api_key = api_key
        self.user = user

        try:
            openai.Model.list()
            self.chat = ChatOpenAI(
                model_name=self.model,
                temperature=0,
                openai_api_key=api_key,
            )
            self.ca_chat = ChatOpenAI(
                model_name=self.ca_model,
                temperature=0,
                openai_api_key=api_key,
            )
            if user == "community":
                self.usage_stats = get_stats(user=user)
            ss.openai_api_key = api_key
            return True
        except openai.error.AuthenticationError as e:
            return False

    def _primary_query(self):
        try:
            response = self.chat.generate([self.messages])
        except (
            openai.error.InvalidRequestError,
            openai.error.APIConnectionError,
            openai.error.RateLimitError,
            openai.error.APIError,
        ) as e:
            return str(e), None

        msg = response.generations[0][0].text
        token_usage = response.llm_output.get("token_usage")

        self._update_usage_stats(self.model, token_usage)

        self.append_ai_message(msg)

        return msg, token_usage

    def _correct_response(self, msg: str):
        ca_messages = self.ca_messages.copy()
        ca_messages.append(
            HumanMessage(
                content=msg,
            ),
        )
        ca_messages.append(
            SystemMessage(
                content="If there is nothing to correct, please respond "
                "with just 'OK', and nothing else!",
            ),
        )

        response = self.ca_chat.generate([ca_messages])

        correction = response.generations[0][0].text
        token_usage = response.llm_output.get("token_usage")

        self._update_usage_stats(self.ca_model, token_usage)

        return correction

    def _update_usage_stats(self, model: str, token_usage: dict):
        """
        Update redis database with token usage statistics using the usage_stats
        object with the increment method.
        """
        if self.user == "community":
            self.usage_stats.increment(
                f"usage:[date]:[user]",
                {f"{k}:{model}": v for k, v in token_usage.items()},
            )


class BloomConversation(Conversation):
    def __init__(self):
        super().__init__()
        self.messages = []

    def set_api_key(self, api_key: str, user: str):
        self.chat = HuggingFaceHub(
            repo_id="bigscience/bloom",
            model_kwargs={"temperature": 1.0},  # "regular sampling"
            # as per https://huggingface.co/docs/api-inference/detailed_parameters
            huggingfacehub_api_token=api_key,
        )

        try:
            self.chat.generate(["Hello, I am a biomedical researcher."])
            return True
        except ValueError as e:
            return False

    def _cast_messages(self, messages):
        """
        Render the different roles of the chat-based conversation as plain text.
        """
        cast = ""
        for m in messages:
            if isinstance(m, SystemMessage):
                cast += f"System: {m.content}\n"
            elif isinstance(m, HumanMessage):
                cast += f"Human: {m.content}\n"
            elif isinstance(m, AIMessage):
                cast += f"AI: {m.content}\n"
            else:
                raise ValueError(f"Unknown message type: {type(m)}")

        return cast

    def _primary_query(self):
        response = self.chat.generate([self._cast_messages(self.messages)])

        msg = response.generations[0][0].text
        token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }

        self.append_ai_message(msg)

        return msg, token_usage

    def _correct_response(self, msg: str):
        return "ok"
