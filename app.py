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


def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


local_css("style.css")

ss = st.session_state

OPENAI_MODELS = [
    "gpt-3.5-turbo",
    "gpt-4",
    "davinci",
]

DEV_FUNCTIONALITY = (
    "This functionality is not available when using the community API key, as "
    "it can involve many requests to the API."
)

OFFLINE_FUNCTIONALITY = (
    "functionality is currently under development and not yet available in the "
    "online version of ChatGSE. Please check back later or check the [GitHub "
    "Repository](https://github.com/biocypher/ChatGSE) for running the app "
    "locally."
)

# IMPORTS
import os
import datetime
from chatgse._interface import ChatGSE
from chatgse._stats import get_community_usage_cost


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
    demo, community, field = st.columns([1, 1, 3])

    with demo:
        st.button("Show A Demonstration", on_click=demo_mode)

    with community:
        st.button("Use The Community Key", on_click=use_community_key)

    with field:
        st.text_input(
            "OpenAI API Key:",
            on_change=on_submit,
            key="widget",
            placeholder="(sk-...) Press [Enter] to submit.",
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
    st.warning(
        """
        Please note that on
        streamlit cloud, the app may reload automatically after a period of
        inactivity, which may lead to inconsistencies in the app state or
        uploaded files. For this reason, it is recommended to go through an
        individual conversation without interruptions. We are looking into more
        persistent solutions for hosting the app.
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
        maximum = ss.get("token_limit", 0)

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

        - Integration with the low-dimensional outputs of popular bioinformatics
        tools (e.g. gsea, progeny, decoupler)

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
        limitations of the used Large Language Model apply: their statements can
        sometimes be incorrect or misleading, and depending on the complexity of
        the task may not yield the desired results. They are however very good
        at synthesising information from their training set, and thus can be
        useful to explain the biological context of, for instance, a particular
        gene set or cell type.

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

    (
        chat_tab,
        annot_tab,
        exp_design_tab,
        prompts_tab,
        correct_tab,
        docsum_tab,
    ) = st.tabs(
        [
            "Gene Sets and Pathways",
            "Cell Type Annotation",
            "Experimental Design",
            "Prompt Engineering",
            "Correcting Agent",
            "Document Summarisation",
        ]
    )

    with chat_tab:
        # WELCOME MESSAGE AND CHAT HISTORY
        st.markdown("Welcome to ``ChatGSE``!")
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
                st.write("(Here, we simulate the upload of a data file.)")
                cg._get_data_input()

            elif ss.mode == "demo_manual":
                cg._get_data_input_manual()
                st.write(
                    "(The next step will involve sending a basic query to the "
                    "model. This may take a few seconds.)"
                )

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
            if not ss.get("error"):
                chat_box()
                autofocus_area()

    with annot_tab:
        if ss.user == "community":
            st.markdown(f"{DEV_FUNCTIONALITY}")
        else:
            st.markdown(
                "A common repetitive task in bioinformatics is to annotate "
                "single-cell datasets with cell type labels. This task is usually "
                "performed by a human expert, who will look at the expression of "
                "marker genes and assign a cell type label based on their "
                "knowledge of the cell types present in the tissue of interest. "
                "Large Language Models have been shown to be able to perform this "
                "task with high accuracy, and can be used to automate cell type "
                "annotation with minimal human input (see e.g. [this arXiv "
                "preprint](https://www.biorxiv.org/content/10.1101/2023.04.16.537094v1))."
            )
            st.markdown(
                f"`Assistant`: Cell type annotation {OFFLINE_FUNCTIONALITY}"
            )

    with exp_design_tab:
        st.markdown(
            "Experimental design is a crucial step in any biological experiment. "
            "However, it can be a subtle and complex task, requiring a deep "
            "understanding of the biological system under study as well as "
            "statistical and computational expertise. Large Language Models "
            "can potentially fill the gaps that exist in most research groups, "
            "which traditionally focus on either the biological or the "
            "statistical aspects of experimental design."
        )
        st.markdown(
            f"`Assistant`: Experimental design functionality {OFFLINE_FUNCTIONALITY}"
        )

    with prompts_tab:
        st.markdown(
            "The construction of prompts is a crucial step in the use of "
            "Large Language Models. However, it can be a subtle and complex "
            "task, often requiring empirical testing on prompt composition "
            "due to the black-box nature of the models. We provide composable "
            "prompts and prompt templates (which can include variables), as "
            "well as save and load functionality for prompt sets to facilitate "
            "testing, reproducibility, and sharing."
        )
        st.markdown(
            f"`Assistant`: Prompt engineering functionality {OFFLINE_FUNCTIONALITY}"
        )

    with correct_tab:
        st.markdown(
            "Large Language Models are very good at synthesising information "
            "from their training set, and thus can be useful to explain the "
            "biological context of a particular gene set or cell type. "
            "However, they can sometimes be incorrect or misleading, and "
            "have been known to occasionally hallucinate while being very "
            "convinced of their answer. To ameliorate this issue, we include "
            "a correcting agent that automatically checks the validity of the "
            "primary model's statements, and corrects them if necessary."
        )
        st.markdown(
            f"`Assistant`: Correction agent functionality {OFFLINE_FUNCTIONALITY}"
        )

    with docsum_tab:
        if ss.user == "community":
            st.markdown(f"{DEV_FUNCTIONALITY}")
        else:
            st.markdown(
                "While Large Language Models have access to vast amounts of "
                "knowledge, this knowledge only includes what was present in "
                "their training set, and thus excludes very current research "
                "as well as research articles that are not open access. To "
                "fill in the gaps of the model's knowledge, we include a "
                "document summarisation approach that stores knowledge from "
                "user-provided documents in a vector database, which can be "
                "used to supplement the model prompt by retrieving the most "
                "relevant contents of the provided documents. This process "
                "builds on the unique functionality of vector databases to "
                "perform similarity search on the embeddings of the documents' "
                "contents."
            )
            st.markdown(
                f"`Assistant`: Document summarisation functionality {OFFLINE_FUNCTIONALITY}"
            )


if __name__ == "__main__":
    main()
