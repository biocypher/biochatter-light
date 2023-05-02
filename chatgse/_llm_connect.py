from abc import ABC, abstractmethod
import openai

from langchain.chat_models import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.llms import HuggingFaceHub


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

        self.messages.append(
            SystemMessage(
                content="You are an assistant to a biomedical researcher."
            )
        )
        self.messages.append(
            SystemMessage(
                content="Your role is to contextualise the user's findings "
                "with biomedical background knowledge. If provided with a "
                "list, please give granular feedback about the individual "
                "entities, your knowledge about them, and what they may mean "
                "in the context of the research."
            ),
        )
        self.messages.append(
            SystemMessage(
                content="You can ask the user to provide explanations and more "
                "background at any time, for instance on the treatment a "
                "patient has received, or the experimental background. But "
                "for now, wait for the user to ask a question."
            ),
        )

        self.ca_messages = [
            SystemMessage(
                content="You are a biomedical researcher.",
            ),
            SystemMessage(
                content="Your task is to check for factual correctness and "
                "consistency of the statements of another agent.",
            ),
            SystemMessage(
                content="Please correct the following message. Ignore "
                "references to previous statements, only correct the current "
                "input. If there is nothing to correct, please respond with "
                "just 'OK', and nothing else!",
            ),
        ]

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
            msg = (
                "The user has provided information in the form of a table. "
                "The rows refer to biological entities (patients, samples, "
                "cell types, or the like), and the columns refer to pathways. "
                "The values are pathway activities derived using the "
                f"bioinformatics method progeny. Here are the data: {df}"
            )
            self.append_system_message(msg)

        elif "dorothea" in tool:
            msg = (
                "The user has provided information in the form of a table. "
                "The rows refer to biological entities (patients, samples, "
                "cell types, or the like), and the columns refer to "
                "transcription factors. The values are transcription factor "
                "activities derived using the bioinformatics method dorothea. "
                f"Here are the data: {df}"
            )
            self.append_system_message(msg)

        elif "gsea" in tool:
            msg = (
                "The user has provided information in the form of a table. "
                "The first column refers to biological entities (samples, "
                "cell types, or the like), and the individual columns refer "
                "to the enrichment of individual gene sets, such as hallmarks, "
                "derived using the bioinformatics method gsea. Here are the "
                f"data: {df}"
            )
            self.append_system_message(msg)

        elif "decoupler" in tool:
            msg = (
                "The user has provided information in the form of a table. "
                "The first column refers to biological entities "
                "(transcription factors, or the like), and the other "
                "columns refer to their activity, derived using the "
                f"bioinformatics method decoupler. Here are the data: {df}"
            )

    def query(self, text: str):
        self.append_user_message(text)

        msg, token_usage = self._primary_query()

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

    def set_api_key(self, api_key: str):
        openai.api_key = api_key

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
            return True
        except openai.error.AuthenticationError as e:
            return False

    def _primary_query(self):
        response = self.chat.generate([self.messages])

        msg = response.generations[0][0].text
        token_usage = response.llm_output.get("token_usage")

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

        response = self.ca_chat(ca_messages)

        correction = response.content

        return correction


class BloomConversation(Conversation):
    def __init__(self):
        super().__init__()
        self.messages = []

    def set_api_key(self, api_key: str):
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
