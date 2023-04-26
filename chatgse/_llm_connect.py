from abc import ABC, abstractmethod
import openai
import json

from langchain.chat_models import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage

from huggingface_hub import InferenceApi


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

    def set_user_name(self, user_name: str):
        self.user_name = user_name

    @abstractmethod
    def set_api_key(self, api_key: str):
        pass

    @abstractmethod
    def append_ai_message(self, message: str):
        pass

    @abstractmethod
    def append_system_message(self, message: str):
        pass

    @abstractmethod
    def append_user_message(self, message: str):
        pass

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

    @abstractmethod
    def query(self, text: str):
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

    def query(self, text: str):
        self.append_user_message(text)

        response = self.chat.generate([self.messages])

        msg = response.generations[0][0].text
        token_usage = response.llm_output.get("token_usage")

        self.append_ai_message(msg)

        correction = self._correct_response(msg)

        if str(correction).lower() in ["ok", "ok."]:
            return (msg, token_usage, None)

        return (msg, token_usage, correction)

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
        self.inference = InferenceApi("bigscience/bloom", token=api_key)

        test = self._infer("Hello, I am a biomedical researcher.")
        response = json.loads(test.text)
        # TODO text is not always json format
        if response.get("error"):
            return False

    def append_ai_message(self, message: str):
        self.messages.append(message)

    def append_system_message(self, message: str):
        self.messages.append(message)

    def append_user_message(self, message: str):
        self.messages.append(message)

    def query(self, text: str):
        self.append_user_message(text)

        prompt = "\n".join(self.messages)

        response = self._infer(prompt)

        msg = response["result"][0]["generated_text"]

        self.append_ai_message(msg)

        return (msg, None, None)

    def _infer(
        self,
        prompt,
        max_length=32,
        top_k=0,
        num_beams=0,
        no_repeat_ngram_size=2,
        top_p=0.9,
        seed=42,
        temperature=0,
        greedy_decoding=False,
        return_full_text=False,
    ):
        """
        From huggingface BLOOM example jpynb
        (https://github.com/Sentdex/BLOOM_Examples/blob/main/BLOOM_api_example.ipynb)
        """
        top_k = None if top_k == 0 else top_k
        do_sample = False if num_beams > 0 else not greedy_decoding
        num_beams = None if (greedy_decoding or num_beams == 0) else num_beams
        no_repeat_ngram_size = (
            None if num_beams is None else no_repeat_ngram_size
        )
        top_p = None if num_beams else top_p
        early_stopping = None if num_beams is None else num_beams > 0

        params = {
            "max_new_tokens": max_length,
            "top_k": top_k,
            "top_p": top_p,
            "temperature": temperature,
            "do_sample": do_sample,
            "seed": seed,
            "early_stopping": early_stopping,
            "no_repeat_ngram_size": no_repeat_ngram_size,
            "num_beams": num_beams,
            "return_full_text": return_full_text,
        }

        return self.inference(prompt, params=params, raw_response=True)
