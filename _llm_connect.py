import openai

# read key from key.txt
key = open("key.txt", "r").read()

openai.api_key = key

MODEL = "gpt-3.5-turbo"


def generate_response(text: str, context: str = "biomedical research"):
    messages = [
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
            "content": f"The topic of the research is {context}.",
        },
        {
            "role": "system",
            "content": "You can ask the user to provide explanations and more background, for instance on the treatment a patient has received, or the experimental background.",
        },
        {
            "role": "user",
            "content": text,
        },
    ]

    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=messages,
        temperature=0,
    )

    return response["choices"][0]["message"]["content"]
