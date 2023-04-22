import openai

from langchain.chat_models import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage


class Conversation:
    def __init__(self, user_name: str = "User"):
        """
        Connect to OpenAI's GPT API and set up a conversation with the user.
        Also initialise a second conversational agent to provide corrections to
        the model output, if necessary.
        """
        self.user_name = user_name

        self.model = "gpt-3.5-turbo"
        self.ca_model = "gpt-3.5-turbo"

        self.messages = [
            SystemMessage(
                content="You are an assistant to a biomedical researcher."
            ),
            SystemMessage(
                content="Your role is to contextualise the user's findings "
                "with biomedical background knowledge. If provided with a "
                "list, please give granular feedback about the individual "
                "entities, your knowledge about them, and what they may mean "
                "in the context of the research."
            ),
            SystemMessage(
                content="You can ask the user to provide explanations and more "
                "background at any time, for instance on the treatment a "
                "patient has received, or the experimental background. But "
                "for now, wait for the user to ask a question."
            ),
        ]

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

        self.history = []

    def set_user_name(self, user_name: str):
        self.user_name = user_name

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

    def setup(self, context: str):
        self.context = context

        self.messages.append(
            SystemMessage(
                content=f"The topic of the research is {context}.",
            ),
        )

    def setup_data_input_manual(self, data_input: str):
        self.data_input = data_input

        self.messages.append(
            SystemMessage(
                content=f"The user has given information on the data input: "
                f"{data_input}.",
            ),
        )

    def setup_data_input_tool(self, df, tool: str):
        self.data_input_tool = df
        if "progeny" in tool:
            self.messages.append(
                SystemMessage(
                    content="The user has provided information in the form of "
                    "a table. The rows refer to biological entities "
                    "(patients, samples, cell types, or the like), and the "
                    "columns refer to pathways. The values are pathway "
                    "activities derived using the bioinformatics method "
                    f"progeny. Here are the data: {df}",
                ),
            )
        elif "dorothea" in tool:
            self.messages.append(
                SystemMessage(
                    content="The user has provided information in the form of "
                    "a table. The rows refer to biological entities "
                    "(patients, samples, cell types, or the like), and the "
                    "columns refer to transcription factors. The values are "
                    "transcription factor activities derived using the "
                    f"bioinformatics method dorothea. Here are the data: {df}",
                ),
            )
        elif "gsea" in tool:
            self.messages.append(
                SystemMessage(
                    content="The user has provided information in the form of "
                    "a table. The first column refers to biological entities "
                    "(samples, cell types, or the like), and the individual "
                    "columns refer to the enrichment of individual gene sets, "
                    "such as hallmarks, derived using the bioinformatics "
                    f"method gsea. Here are the data: {df}",
                ),
            )
        elif "decoupler" in tool:
            self.messages.append(
                SystemMessage(
                    content="The user has provided information in the form of "
                    "a table. The first column refers to biological entities "
                    "(transcription factors, or the like), and the other "
                    "columns refer to their activity, derived using the "
                    "bioinformatics method decoupler. Here are the data: {df}",
                ),
            )

    def query(self, text: str):
        self.messages.append(HumanMessage(content=text))

        response = self.chat.generate([self.messages])

        msg = response.generations[0][0].text
        token_usage = response.llm_output.get("token_usage")

        self.messages.append(AIMessage(content=msg))

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
