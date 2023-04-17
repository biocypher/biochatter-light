# app.py: streamlit chat app for contextualisation of biomedical results
import streamlit as st

TOPIC = ""
USER_NAME = "User"


# dummy
def generate_prompt(input_text):
    prompt = USER_NAME + ": " + input_text
    return prompt


def generate_response(prompt):
    response = "Bot: " + prompt
    return response


st.set_page_config(
    page_title="ChatGSE",
    page_icon=":robot_face:",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("ChatGSE")


if "history" not in st.session_state:
    st.markdown(
        """
        Welcome to ChatGSE. What is your name?
        """
    )
    st.session_state.history = []
else:
    for msg in st.session_state.history:
        st.write(msg)

if "input" not in st.session_state:
    st.session_state.input = ""

if "mode" not in st.session_state:
    st.session_state.mode = "name"


def submit():
    st.session_state.input = st.session_state.widget
    st.session_state.widget = ""


if st.session_state.input:
    if st.session_state.mode == "name":
        USER_NAME = st.session_state.input
        st.session_state.mode = "topic"
        msg = f"Hi {USER_NAME}, what is the context of your inquiry?"
        st.session_state["history"].append(msg)
        st.write(msg)

    elif st.session_state.mode == "topic":
        TOPIC = st.session_state.input
        st.session_state.mode = "chat"
        msg = f"You have selected {TOPIC} as your context. You can now ask questions."
        st.session_state["history"].append(msg)
        st.write(msg)

    elif st.session_state.mode == "chat":
        prompt = generate_prompt(st.session_state.input)
        st.session_state["history"].append(prompt)
        st.write(prompt)
        response = generate_response(prompt)
        st.session_state["history"].append(response)
        st.write(response)

st.text_input(
    "Input:",
    on_change=submit,
    key="widget",
    placeholder="Enter text here.",
)
