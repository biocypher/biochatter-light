import openai


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
            {
                "role": "system",
                "content": "You are an assistant to a biomedical researcher.",
            },
            {
                "role": "system",
                "content": "Your role is to contextualise the user's findings "
                "with biomedical background knowledge. If provided with a "
                "list, please give granular feedback about the individual "
                "entities, your knowledge about them, and what they may mean "
                "in the context of the research.",
            },
            {
                "role": "system",
                "content": "You can ask the user to provide explanations and "
                "more background at any time, for instance on the treatment a "
                "patient has received, or the experimental background. But "
                "for now, wait for the user to ask a question.",
            },
        ]

        self.ca_messages = [
            {
                "role": "system",
                "content": "You are a biomedical researcher.",
            },
            {
                "role": "system",
                "content": "Your task is to check for factual correctness and "
                "consistency of the statements of another agent.",
            },
            {
                "role": "system",
                "content": "Please correct the following message. Ignore "
                "references to previous statements, only correct the current "
                "input. If there is nothing to correct, please respond with "
                "just 'OK', and nothing else!",
            },
        ]

        self.history = []

    def set_user_name(self, user_name: str):
        self.user_name = user_name

    def set_api_key(self, api_key: str):
        openai.api_key = api_key

        try:
            openai.Model.list()
            return True
        except openai.error.AuthenticationError as e:
            return False

    def setup(self, context: str):
        self.context = context
        self.messages.append(
            {
                "role": "system",
                "content": f"The topic of the research is {context}.",
            },
        )

    def setup_data_input_manual(self, data_input: str):
        self.data_input = data_input
        self.messages.append(
            {
                "role": "system",
                "content": "The user has given information on the data "
                f"input: {data_input}.",
            },
        )

    def setup_data_input_tool(self, df, tool: str):
        self.data_input_tool = df
        if tool == "progeny":
            self.messages.append(
                {
                    "role": "system",
                    "content": "The user has provided information in the "
                    "form of a table. The rows refer to biological entities "
                    "(samples, cell types, or the like), and the columns refer "
                    "to pathways. The values are pathway activities derived "
                    "using the bioinformatics method progeny. Here are the "
                    f"data: {df}",
                },
            )
        elif tool == "decoupler":
            self.messages.append(
                {
                    "role": "system",
                    "content": "The user has provided information in the "
                    "form of a table. The `Name` column refers to biological "
                    "entities (transcription factors, or the like), and the "
                    "`Activity` column refers to their activity, derived using "
                    "the bioinformatics method decoupler. Here are the "
                    f"data: {df}",
                },
            )

    def query(self, text: str):
        self.messages.append(
            {
                "role": "user",
                "content": text,
            }
        )

        response = openai.ChatCompletion.create(
            model=self.model,
            messages=self.messages,
            temperature=0,
        )

        msg = response["choices"][0]["message"]["content"]
        self.messages.append(
            {
                "role": "assistant",
                "content": msg,
            },
        )

        correction = self._correct_response(msg)

        if str(correction).lower() in ["ok", "ok."]:
            return (msg, None)

        return (msg, correction)

    def _correct_response(self, msg: str):
        ca_messages = self.ca_messages.copy()
        ca_messages.append(
            {
                "role": "user",
                "content": msg,
            },
        )
        ca_messages.append(
            {
                "role": "system",
                "content": "If there is nothing to correct, please respond "
                "with just 'OK', and nothing else!",
            },
        )

        response = openai.ChatCompletion.create(
            model=self.ca_model,
            messages=ca_messages,
            temperature=0,
        )

        correction = response["choices"][0]["message"]["content"]

        return correction
