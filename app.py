# app.py: streamlit chat app for contextualisation of biomedical results
app_name = "chatgse"
__version__ = "0.2.12"

# BOILERPLATE
import streamlit as st
import streamlit.components.v1 as components
from streamlit.runtime.uploaded_file_manager import (
    UploadedFile,
    UploadedFileRec,
)

st.set_page_config(
    page_title="ChatGSE",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)
ss = st.session_state


# IMPORTS
import os
import datetime
from chatgse._interface import ChatGSE
from chatgse._stats import get_community_usage_cost

OPENAI_MODELS = [
    "gpt-3.5-turbo",
    "gpt-4",
    "davinci",
]


# HANDLERS
def update_api_keys():
    """
    Looks for API keys of supported services in the environment variables and
    updates the session state accordingly.
    """
    if "OPENAI_API_KEY" in os.environ:
        ss["openai_api_key"] = os.environ["OPENAI_API_KEY"]
    if "HUGGINGFACEHUB_API_TOKEN" in os.environ:
        ss["huggingfacehub_api_key"] = os.environ["HUGGINGFACEHUB_API_TOKEN"]


def on_submit():
    ss.input = ss.widget
    ss.widget = ""


def autofocus_line():
    if "counter" not in ss:
        ss["counter"] = 0
    components.html(
        f"""
        <div></div>
        <p>{ss.counter}</p>
        <script>
            var input = window.parent.document.querySelectorAll("input[type=text]");
            for (var i = 0; i < input.length; ++i) {{
                input[i].focus();
            }}
        </script>
        """,
        height=15,
    )


def autofocus_area():
    if "counter" not in ss:
        ss["counter"] = 0
    components.html(
        f"""
        <div></div>
        <p>{ss.counter}</p>
        <script>
            var input = window.parent.document.querySelectorAll("textarea[type=textarea]");
            for (var i = 0; i < input.length; ++i) {{
                input[i].focus();
            }}
        </script>
        """,
        height=15,
    )


# COMPONENTS
def chat_line():
    st.text_input(
        "Input:",
        on_change=on_submit,
        key="widget",
        placeholder="Write here. Press [Enter] to submit.",
        label_visibility="collapsed",
    )


def chat_box():
    st.text_area(
        "Input:",
        on_change=on_submit,
        key="widget",
        placeholder=(
            "Write here. Press [Enter] for a new line, and [CTRL+Enter] or "
            "[⌘+Enter] to submit."
        ),
        label_visibility="collapsed",
    )


def openai_key_chat_box():
    st.text_input(
        "OpenAI API Key:",
        on_change=on_submit,
        key="widget",
        placeholder="(sk-...)",
    )


def huggingface_key_chat_box():
    st.text_input(
        "Hugging Face Hub API Token:",
        on_change=on_submit,
        key="widget",
        placeholder="(hf_...)",
    )


def file_uploader():
    st.file_uploader(
        "Upload tool data",
        type=["csv", "tsv", "txt"],
        key="tool_data",
        accept_multiple_files=True,
    )


def data_input_buttons():
    c1, c2 = st.columns([1, 1])
    with c1:
        st.button(
            "Yes",
            on_click=data_input_yes,
            use_container_width=True,
        )
    with c2:
        st.button(
            "No",
            on_click=data_input_no,
            use_container_width=True,
        )


def data_input_yes():
    ss.mode = "getting_data_file_input"
    ss.input = "done"


def data_input_no():
    ss.mode = "asking_for_manual_data_input"
    ss.input = "no"


def app_header():
    st.markdown(
        f"""
        # 💬🧬 :red[ChatGSE] `{__version__}`
        For a new session, please refresh the page.
        """
    )


def get_remaining_tokens():
    """
    Fetch the percentage of remaining tokens for the day from the _stats module.
    """
    used = get_community_usage_cost()
    limit = float(99 / 30)
    pct = (100.0 * (limit - used) / limit) if limit else 0
    pct = max(0, pct)
    pct = min(100, pct)
    return pct


def community_tokens_refresh_in():
    x = datetime.datetime.now()
    dt = (x.replace(hour=23, minute=59, second=59) - x).seconds
    h = dt // 3600
    m = dt % 3600 // 60
    return f"{h} h {m} min"


def remaining_tokens():
    """
    Display remaining community tokens for the day coloured by percentage.
    """
    rt = get_remaining_tokens()
    col = ":green" if rt > 25 else ":orange" if rt > 0 else ":red"
    pct = f"{rt:.1f}"
    st.markdown(f"Daily community tokens remaining: {col}[{pct}%]")
    st.progress(rt / 100)


def display_token_usage():
    with st.expander("Token usage", expanded=True):
        if ss.primary_model == "gpt-3.5-turbo":
            maximum = 4097  # TODO get this programmatically
        elif ss.primary_model == "bigscience/bloom":
            maximum = 1000

        st.markdown(
            f"""
            Last query: {ss.token_usage["prompt_tokens"]}

            Last response: {ss.token_usage["completion_tokens"]}

            Total usage: {ss.token_usage["total_tokens"]}

            Model maximum: {maximum}
            """
        )

        # display warning within 20% of maximum
        if ss.token_usage["total_tokens"] > maximum * 0.8:
            st.warning(
                "You are approaching the maximum number of tokens allowed by "
                "the model. Please consider using a different model or "
                "reducing the number of queries. You can reset the app to "
                "start over the conversation."
            )


def model_select():
    with st.expander("Model selection", expanded=False):
        if not ss.mode == "getting_key":
            st.markdown("Please reload the app to change the model.")
            return

        models = [
            "gpt-3.5-turbo",
            "bigscience/bloom",
        ]
        st.selectbox(
            "Primary model",
            models,
            key="primary_model",
            help=(
                "This is the model you will be talking to. "
                "Caution: changing the model will reset your conversation."
            ),
        )

        if ss.primary_model == "bigscience/bloom":
            st.warning(
                "BLOOM support is currently experimental. Queries may return "
                "unexpected results."
            )


def community_select():
    if not get_remaining_tokens() > 0:
        st.warning(
            "No community tokens remaining for the day. "
            f"Refreshes in {community_tokens_refresh_in()}."
        )
        return

    b1, b2 = st.columns([1, 1])
    with b1:
        st.button("Use Community Key", on_click=use_community_key)
    with b2:
        st.button("Show Demonstration", on_click=demo_mode)


def use_community_key():
    ss.openai_api_key = os.environ["OPENAI_COMMUNITY_KEY"]
    ss.cg._history_only("Assistant", "Using community key!")
    ss.user = "community"
    ss.mode = "using_community_key"
    ss.show_community_select = False
    ss.input = "done"  # just to enter main logic; more elegant solution?


def demo_mode():
    ss.openai_api_key = os.environ["OPENAI_COMMUNITY_KEY"]
    ss.cg._history_only("Assistant", "Using community key!")
    ss.user = "community"
    ss.show_community_select = False
    ss.input = "Demo User"
    ss.mode = "demo_key"


def demo_next_button():
    st.button("Next Step", on_click=demo_next)


def demo_next():
    if ss.mode == "demo_key":
        ss.input = "Demo User"
        ss.mode = "demo_start"

    elif ss.mode == "demo_start":
        ss.input = (
            "Immunity; single-cell sequencing of PBMCs of a healthy donor, "
            "3000 cells; followed by pathway activity analysis."
        )
        ss.mode = "demo_context"

    elif ss.mode == "demo_context":
        # create UploadedFile from "input/progeny.csv"
        with open("input/progeny.csv", "rb") as f:
            data = f.read()

        uploaded_file = UploadedFileRec(
            id=1,
            name="progeny.csv",
            type="text/csv",
            data=data,
        )

        ss.demo_tool_data = [UploadedFile(record=uploaded_file)]
        ss.mode = "demo_tool"
        ss.input = "done"

    elif ss.mode == "demo_tool":
        ss.input = "no"
        ss.mode = "demo_manual"

    elif ss.mode == "demo_manual":
        ss.input = "Please explain my findings."
        ss.mode = "demo_chat"


def app_info():
    st.markdown(
        """
        
        ChatGSE is a tool to rapidly contextualise common end results of
        biomedical analyses. It works by setting up a topic-constrained
        conversation with a pre-trained language model. The main benefits of
        this approach are:

        - Integration with popular bioinformatics tools (e.g. progeny,
        decoupler)

        - Prompts tuned to biomedical research and your specific queries

        - Integrated safeguards to prevent false information and comparison to
        curated prior knowledge

        - Confidentiality of the shared data (as opposed to the ChatGPT
        interface, which allows storage and reuse of the user's prompts by
        OpenAI)
        
        The agents you will be talking to are an `Assistant` (a pre-programmed
        conversational algorithm), a `ChatGSE` model, which is a pre-trained
        language model with instructions aimed at specifically improving the
        quality of biomedical answers, and a `Correcting agent`, which is a
        separate pre-trained language model with the task of catching and
        correcting false information conveyed by the primary model. You will
        only see the `Correcting agent` if it detects that the `ChatGSE` model
        has made a mistake. In general, even though we try our best to avoid
        mistakes using the correcting agent and internal safeguards, the general
        limitations of the used Large Language Model apply, which means that the
        statements made can sometimes be incorrect or misleading.

        ChatGSE is developed by [Sebastian
        Lobentanzer](https://slobentanzer.github.io); you can find the source
        code on [GitHub](https://github.com/biocypher/chatgse).

        """
    )


def spacer(n=2, line=False, next_n=0):
    for _ in range(n):
        st.write("")
    if line:
        st.tabs([" "])
    for _ in range(next_n):
        st.write("")


def main():
    # NEW SESSION
    if not ss.get("mode"):
        with open("chatgse-logs.txt", "a") as f:
            f.write("--- NEW SESSION ---\n")

        ss.user = "default"

    # SETUP
    # check for API keys
    if not ss.get("primary_model"):
        # default model
        ss["primary_model"] = "gpt-3.5-turbo"
        update_api_keys()

    # instantiate interface
    if not ss.get("cg"):
        ss.cg = ChatGSE()
    cg = ss.cg
    if ss.get("active_model") != ss.primary_model:
        cg.set_model(ss.primary_model)
        ss.active_model = ss.primary_model
        ss.mode = cg._check_for_api_key(write=False)
        # TODO: warn user that we are resetting?

    # instantiate token usage
    if not ss.get("token_usage"):
        ss.token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }

    chat_tab, annot_tab, prompts_tab = st.tabs(
        ["Gene Sets and Pathways", "Cell Type Annotation", "Prompt Engineering"]
    )

    with chat_tab:
        # WELCOME MESSAGE AND CHAT HISTORY
        cg._display_init()
        cg._display_history()

        # CHAT BOT LOGIC
        if ss.input:
            if ss.mode == "getting_key":
                ss.mode = cg._get_api_key(ss.input)

            elif ss.mode == "using_community_key":
                ss.input = ""  # ugly
                ss.mode = cg._check_for_api_key()

            elif ss.mode == "getting_name":
                ss.mode = cg._get_user_name()

            elif ss.mode == "getting_context":
                ss.mode = cg._get_context()
                ss.mode = cg._ask_for_data_input()

            elif ss.mode == "getting_data_file_input":
                ss.mode = cg._get_data_input()

            elif ss.mode == "getting_data_file_description":
                ss.mode = cg._get_data_file_description()

            elif ss.mode == "asking_for_manual_data_input":
                ss.mode = cg._ask_for_manual_data_input()

            elif ss.mode == "getting_manual_data_input":
                ss.mode = cg._get_data_input_manual()

            elif ss.mode == "chat":
                with st.spinner("Thinking..."):
                    ss.response, ss.token_usage = cg._get_response()

            # DEMO LOGIC
            elif ss.mode == "demo_key":
                ss.input = ""  # ugly
                cg._check_for_api_key()

            elif ss.mode == "demo_start":
                cg._get_user_name()

            elif ss.mode == "demo_context":
                cg._get_context()
                cg._ask_for_data_input()

            elif ss.mode == "demo_tool":
                cg._get_data_input()

            elif ss.mode == "demo_manual":
                cg._get_data_input_manual()

            elif ss.mode == "demo_chat":
                with st.spinner("Thinking..."):
                    ss.response, ss.token_usage = cg._get_response()
                cg._write_and_history(
                    "Assistant",
                    "🎉 This concludes the demonstration. You can chat with the "
                    "model now, or start your own inquiry! Please always keep "
                    "in mind that Large Language Models can sometimes be "
                    "incorrect or misleading, and depending on the complexity "
                    "of the task may not yield the desired results. They are "
                    "however very good at synthesising information from their "
                    "training set, and thus can be useful to explain the "
                    "biological context of a particular gene set or cell "
                    "type. For instance, you could ask what a particular "
                    "pathway does in a particular cell type, or which drugs "
                    "could be used to target it.",
                )
                ss.mode = "chat"

        # RESET INPUT
        ss.input = ""

        # SIDEBAR
        with st.sidebar:
            app_header()
            file_uploader()
            with st.expander("About"):
                app_info()
            remaining_tokens()
            if (
                ss.get("show_community_select", False)
                and ss.get("primary_model") in OPENAI_MODELS
            ):
                community_select()
            display_token_usage()
            model_select()

        # CHAT BOX

        if ss.mode == "getting_key":
            if ss.primary_model == "gpt-3.5-turbo":
                openai_key_chat_box()
            elif ss.primary_model == "bigscience/bloom":
                huggingface_key_chat_box()
        elif ss.mode == "getting_data_file_input":
            data_input_buttons()
        elif ss.mode in ["getting_name", "getting_context"]:
            chat_line()
            autofocus_line()
        elif "demo" in ss.mode:
            demo_next_button()
        else:
            chat_box()
            autofocus_area()

    with annot_tab:
        st.markdown(
            "`Assistant`: Cell type annotation functionality is currently "
            "under development. Please check back later."
        )

    with prompts_tab:
        st.markdown(
            "`Assistant`: Prompt engineering functionality is currently "
            "under development. Please check back later."
        )


if __name__ == "__main__":
    main()
