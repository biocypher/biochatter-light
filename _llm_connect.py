import os
import openai


class Conversation:
    def __init__(self, user_name: str):
        self.user_name = user_name

        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError(
                "Please set the OPENAI_API_KEY environment variable to provide a valid OpenAI API key."
            )

        openai.api_key = os.getenv("OPENAI_API_KEY")

        self.model = "gpt-3.5-turbo"

        self.messages = [
            {
                "role": "system",
                "content": "You are an assistant to a biomedical researcher.",
            },
            {
                "role": "system",
                "content": "Your role is to contextualise the user's findings with biomedical background knowledge. If provided with a list, please give granular feedback about the individual entities, your knowledge about them, and what they may mean in the context of the research.",
            },
            {
                "role": "system",
                "content": "You can ask the user to provide explanations and more background at any time, for instance on the treatment a patient has received, or the experimental background. But for now, wait for the user to ask a question.",
            },
        ]

        self.history = []

    def setup(self, context: str):
        self.context = context
        self.messages.append(
            {
                "role": "system",
                "content": f"The topic of the research is {context}.",
            },
        )

    def setup_perturbation(self, perturbation: str):
        self.perturbation = perturbation
        self.perturbation_unstructured = True
        self.messages.append(
            {
                "role": "system",
                "content": f"The user has given information on the perturbation: {perturbation}.",
            },
        )

    def query(self, text: str):
        self.messages.append(
            {
                "role": "user",
                "content": text,
            }
        )
        self.history.append({self.user_name: text})

        response = openai.ChatCompletion.create(
            model=self.model,
            messages=self.messages,
            temperature=0,
        )
        self.messages.append(
            {
                "role": "assistant",
                "content": response["choices"][0]["message"]["content"],
            },
        )
        self.history.append(
            {"ChatGSE": response["choices"][0]["message"]["content"]}
        )
        return response["choices"][0]["message"]["content"]
