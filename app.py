# BioChatter Light: lightweight pure Python frontend for BioChatter
app_name = "biochatter-light"
__version__ = "0.4.3"

# BOILERPLATE
import json
import streamlit as st
import streamlit.components.v1 as components
from streamlit.runtime.uploaded_file_manager import (
    UploadedFile,
    UploadedFileRec,
    FileURLsProto,
)
import yaml

st.set_page_config(
    page_title="BioChatter Light",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)


def local_css(file_name):
    """
    Load local CSS file.
    """
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


local_css("style.css")

ss = st.session_state

# GLOBALS

DEV_FUNCTIONALITY = (
    "This functionality is not available when using the community API key, as "
    "it can involve many requests to the API."
)

OFFLINE_FUNCTIONALITY = (
    "functionality is not available in the online version of BioChatter Light. "
    "Please check the [GitHub Repository](https://github.com/biocypher/biochatter-light) "
    "for instructions on running the app locally."
)

PRIMARY_MODEL_PROMPTS = [
    "You are an assistant to a biomedical researcher.",
    "Your role is to contextualise the user's findings with biomedical "
    "background knowledge. If provided with a list, please give granular "
    "feedback about the individual entities, your knowledge about them, and "
    "what they may mean in the context of the research.",
    "You can ask the user to provide explanations and more background at any "
    "time, for instance on the treatment a patient has received, or the "
    "experimental background. But for now, wait for the user to ask a "
    "question.",
]

CORRECTING_AGENT_PROMPTS = [
    "You are a biomedical researcher.",
    "Your task is to check for factual correctness and consistency of the "
    "statements of another agent.",
    "Please correct the following message. Ignore references to previous "
    "statements, only correct the current input. If there is nothing to "
    "correct, please respond with just 'OK', and nothing else!",
]

TOOL_PROMPTS = {
    "progeny": (
        "The user has provided information in the form of a table. The rows "
        "refer to biological entities (patients, samples, cell types, or the "
        "like), and the columns refer to pathways. The values are pathway "
        "activities derived using the bioinformatics method progeny. Here are "
        "the data: {df}"
    ),
    "dorothea": (
        "The user has provided information in the form of a table. The rows "
        "refer to biological entities (patients, samples, cell types, or the "
        "like), and the columns refer to transcription factors. The values are "
        "transcription factor activities derived using the bioinformatics "
        "method dorothea. Here are the data: {df}"
    ),
    "gsea": (
        "The user has provided information in the form of a table. The first "
        "column refers to biological entities (samples, cell types, or the "
        "like), and the individual columns refer to the enrichment of "
        "individual gene sets, such as hallmarks, derived using the "
        "bioinformatics method gsea. Here are the data: {df}"
    ),
}
RAG_PROMPTS = [
    "The user has provided additional background information from scientific "
    "articles.",
    "Take the following statements into account and specifically comment on "
    "consistencies and inconsistencies with all other information available to "
    "you: {statements}",
]
SCHEMA_PROMPTS = [
    "The user has provided database access. The database contents are "
    "detailed in the following YAML config.",
    "The top-level entries in the YAML config refer to the types of "
    "entities included in the database. Entities can additionally have a "
    "`properties` attribute that informs of their attached information. Here "
    "is the config: {config}",
]

WHAT_MESSAGES = [
    "A platform for the application of Large Language Models (LLMs) in biomedical research.",
    "A way to make LLMs more __useful__ and __trustworthy__.",
    "A means to make biomedical research more reproducible.",
    "A platform for contextualisation of biomedical results.",
    "An interface for the intuitive interaction with current cutting-edge AI.",
    "An __open-source__ project.",
    "A way to make biomedical research more efficient.",
    "A time-saver.",
]

HOW_MESSAGES = [
    "Building wrappers around LLMs to tune their responses and ameliorate their shortcomings.",
    "Connecting to complementary technology, such as (vector) databases and model chaining.",
    "Being playful and experimental, and having fun!",
    "Coming together as a community and being communicative.",
    "Collaborating on the future of biomedical research.",
    "Engineering prompts to make LLMs more useful.",
    "Following open science principles.",
    "Being transparent about the limitations of the technology.",
    "Being modular and extensible.",
    "Injecting prior knowledge into LLM queries.",
]

# IMPORTS
import os
import datetime
import pandas as pd
from biochatter_light._interface import BioChatterLight
from biochatter_light._interface import community_possible
from biochatter._stats import get_community_usage_cost
from biochatter.vectorstore import (
    DocumentEmbedder,
    DocumentReader,
)
from biochatter.rag_agent import RagAgent
from biochatter.llm_connect import (
    OPENAI_MODELS,
    HUGGINGFACE_MODELS,
    XINFERENCE_MODELS,
)
from biochatter.prompts import BioCypherPromptEngine
from pymilvus.exceptions import MilvusException
from langchain.embeddings import OpenAIEmbeddings
import neo4j_utils as nu


# HANDLERS
def update_api_keys():
    """
    Looks for API keys of supported services in the environment variables and
    updates the session state accordingly.
    """
    if "OPENAI_API_KEY" in os.environ:
        ss.openai_api_key = os.environ["OPENAI_API_KEY"]
    if "HUGGINGFACEHUB_API_TOKEN" in os.environ:
        ss.huggingfacehub_api_key = os.environ["HUGGINGFACEHUB_API_TOKEN"]

    if "OPENAI_API_TYPE" in os.environ:
        if os.environ["OPENAI_API_TYPE"] == "azure":
            set_azure_mode()


def set_azure_mode():
    if not "OPENAI_DEPLOYMENT_NAME" in os.environ:
        raise ValueError(
            "OPENAI_DEPLOYMENT_NAME must be set to use Azure API. Please use it to "
            "set the deployment name, e.g. OPENAI_DEPLOYMENT_NAME=your-deployment-name"
        )

    if not "OPENAI_MODEL_NAME" in os.environ:
        raise ValueError(
            "OPENAI_MODEL_NAME must be set to use Azure API. Please use it to set "
            "the model name, e.g. OPENAI_MODEL_NAME=gpt-35-turbo"
        )

    if not "OPENAI_API_VERSION" in os.environ:
        raise ValueError(
            "OPENAI_API_VERSION must be set to use Azure API. Please use it to "
            "set the API version, e.g. OPENAI_API_VERSION=2023-03-15-preview"
        )

    if not "OPENAI_API_BASE" in os.environ:
        raise ValueError(
            "OPENAI_API_BASE must be set to use Azure API. Please use it to "
            "set the API base, e.g. "
            "OPENAI_API_BASE=https://your-resource-name.openai.azure.com"
        )

    if not "OPENAI_API_KEY" in os.environ:
        raise ValueError(
            "OPENAI_API_KEY must be set to use Azure API, e.g. "
            "OPENAI_API_KEY=sk-1234567890abcdef1234567890abcdef"
        )

    ss.openai_api_type = "azure"
    ss.openai_deployment_name = os.environ["OPENAI_DEPLOYMENT_NAME"]
    ss.openai_api_version = os.environ["OPENAI_API_VERSION"]
    ss.openai_api_base = os.environ["OPENAI_API_BASE"]
    ss.openai_api_key = os.environ["OPENAI_API_KEY"]
    # check for key validity?
    ss.mode = "getting_name"


def on_submit():
    """
    Handles the submission of the input text.
    """
    ss.input = ss.get("widget")
    ss.widget = ""


def autofocus_line():
    """
    Autofocuses the input line. A bit hacky, but works.
    """
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
    """
    Autofocuses the input area. A bit hacky, but works.
    """
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
    """
    Renders a chat line for smaller inputs.
    """
    st.text_input(
        "Input:",
        on_change=on_submit,
        key="widget",
        placeholder="Write here. Press [Enter] to submit.",
        label_visibility="collapsed",
    )


def chat_box():
    """
    Renders a chat box for larger inputs. Used for all main chat functionality.
    """
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
    if ss.get("conversation_mode") == "both" and not ss.get("embedder_used"):
        st.warning(
            "You have selected 'data and papers' as the conversation mode, but "
            "have not yet embedded any documents. Prompt injection will only "
            "be performed if you upload at least one document (in the "
            "'Retrieval-Augmented Generation' tab)."
        )


def openai_key_chat_box():
    """
    Field for entering the OpenAI API key. Not shown if the key is found in
    the environment variables. If the community key is available (i.e., we
    are running on self-hosted, connected to Redis, and have credits remaining)
    we show a button to use the community key and a button to show a demo.
    """
    if community_possible():
        demo, community, field = st.columns([1, 1, 3])

        with demo:
            st.button(
                "Show A Demonstration",
                on_click=demo_mode,
                use_container_width=True,
            )

        with community:
            st.button(
                "Use The Community Key",
                on_click=use_community_key,
                use_container_width=True,
            )

        with field:
            st.text_input(
                "OpenAI API Key:",
                on_change=on_submit,
                key="widget",
                placeholder="(sk-...) Press [Enter] to submit.",
            )

    else:
        st.text_input(
            "OpenAI API Key:",
            on_change=on_submit,
            key="widget",
            placeholder="(sk-...) Press [Enter] to submit.",
        )


def huggingface_key_chat_box():
    """
    Field for entering the Hugging Face Hub API key. Not shown if the key is
    found in the environment variables.
    """
    st.text_input(
        "Hugging Face Hub API Token:",
        on_change=on_submit,
        key="widget",
        placeholder="(hf_...)",
    )


def file_uploader():
    """
    File uploader for uploading a CSV, TSV, or TXT file containing the user's
    tool data to be used for the prompt.
    """
    st.file_uploader(
        "Upload tool data",
        type=["csv", "tsv", "txt"],
        key="tool_data",
        accept_multiple_files=True,
    )


def data_input_buttons():
    """
    Buttons for asking the user if they want to upload a file containing their
    tool data.
    """
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
    """
    Handles the user clicking the "Yes" button for uploading a file containing
    their tool data.
    """
    ss.mode = "getting_data_file_input"
    ss.input = "done"


def data_input_no():
    """
    Handles the user clicking the "No" button for uploading a file containing
    their tool data.
    """
    ss.mode = "asking_for_manual_data_input"
    ss.input = "no"


def app_header():
    """
    Renders the app header and a warning conditional on whether we are running
    on streamlit cloud.
    """
    st.markdown(
        f"""
        # 💬🧬 :red[BioChatter Light] `{__version__}`
        """
    )
    if ss.get("on_streamlit"):
        st.warning(
            "Please note that, on streamlit cloud, the app may reload "
            "automatically after a period of inactivity, which may lead to "
            "inconsistencies in the app state or uploaded files. For this "
            "reason, it is recommended to go through an individual "
            "conversation without interruptions. Please visit our [self-hosted "
            "instance](https://chat.biocypher.org) to prevent this."
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
    """
    Display the time remaining until the community tokens refresh.
    """
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
    """
    Display the token usage for the current conversation.
    """
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
    """
    Select the primary model to use for the conversation.
    """
    with st.expander("Model selection", expanded=False):
        if not ss.mode in ["getting_key", "getting_name"]:
            st.markdown("Please reload the app to change the model.")
            return

        if ss.user == "community":
            st.warning(
                "You are currently using the community key. Please reload the "
                "app to change the model."
            )
            return

        # concatenate OPENAI_MODELS and HUGGINGFACE_MODELS
        models = OPENAI_MODELS  # + HUGGINGFACE_MODELS  + XINFERENCE_MODELS
        st.selectbox(
            "Primary model",
            options=models,
            index=0,
            on_change=_change_model,
            key="_primary_model",
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
        elif ss.primary_model == "custom-endpoint":
            # ask for base url of endpoint, target is ss.xinference_base_url,
            # default value is also ss.xinference_base_url
            ss.xinference_base_url = st.text_input(
                "Base URL:",
                value=ss.xinference_base_url,
                help=(
                    "Please enter the base URL of your custom XInference "
                    "endpoint."
                ),
            )


def _change_model():
    """
    Handles the user changing the primary model.
    """
    if ss.primary_model == ss._primary_model:
        return

    ss.primary_model = ss._primary_model
    ss.mode = ""
    ss.input = ""


def community_select():
    """
    Show buttons to select the community key or the demo mode (which also
    uses the community key).
    """
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
    """
    Use the community key for the conversation.
    """
    ss.openai_api_key = os.environ["OPENAI_COMMUNITY_KEY"]
    ss.bcl._history_only("📎 Assistant", "Using community key!")
    ss.user = "community"
    ss.mode = "using_community_key"
    ss.show_community_select = False
    ss.input = "done"  # just to enter main logic; more elegant solution?


def demo_mode():
    """
    Enter the demo mode for the conversation.
    """
    ss.openai_api_key = os.environ["OPENAI_COMMUNITY_KEY"]
    ss.bcl._history_only("📎 Assistant", "Using community key!")
    ss.user = "community"
    ss.show_community_select = False
    ss.input = "Demo User"
    ss.mode = "demo_key"


def demo_next_button():
    """
    Show the "Next Step" button for the demo mode.
    """
    st.button("Next Step", on_click=demo_next, use_container_width=True)


def demo_next():
    """
    Handle demo mode logic.
    """
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
            file_id=1,
            name="progeny.csv",
            type="text/csv",
            data=data,
        )

        ss.demo_tool_data = [
            UploadedFile(record=uploaded_file, file_urls=FileURLsProto())
        ]
        ss.mode = "demo_tool"
        ss.input = "done"

    elif ss.mode == "demo_tool":
        ss.input = "no"
        ss.mode = "demo_manual"

    elif ss.mode == "demo_manual":
        ss.input = "Please explain my findings."
        ss.mode = "demo_chat"


def app_info():
    """
    Display the app information.
    """
    st.markdown(
        """
        
        BioChatter Light is developed by [Sebastian
        Lobentanzer](https://slobentanzer.github.io); you can find the source
        code on [GitHub](https://github.com/biocypher/biochatter-light). Read a
        more in-depth discussion of the approach in the
        [preprint](https://arxiv.org/abs/2305.06488).

        BioChatter Light is a lightweight frontend for the BioChatter library.
        BioChatter works by setting up a topic-constrained conversation with a
        pre-trained language model, and includes additional functionalities to
        include prior knowledge from knowledge graphs or literature databases.
        The main benefits of this approach are:

        - Integration with the low-dimensional outputs of popular bioinformatics
        tools (e.g. gsea, progeny, decoupler)

        - Prompts tuned to biomedical research and your specific queries

        - Integrated safeguards to prevent false information and comparison to
        curated prior knowledge

        - Confidentiality of the shared data (as opposed to the ChatGPT
        interface, which allows storage and reuse of the user's prompts by
        OpenAI)
        
        The agents you will be talking to are an `📎 Assistant` (a
        pre-programmed conversational algorithm), a `💬🧬 BioChatter Light` model, which
        is a pre-trained language model with instructions aimed at specifically
        improving the quality of biomedical answers, and a `️️️️️️️️️️️🕵️ Correcting agent`,
        which is a separate pre-trained language model with the task of catching
        and correcting false information conveyed by the primary model. You will
        only see the `🕵️ Correcting agent` if it detects that the `💬🧬 BioChatter Light`
        model has made a mistake. In general, even though we try our best to
        avoid mistakes using the correcting agent and internal safeguards, the
        general limitations of the used Large Language Model apply: their
        statements can sometimes be incorrect or misleading, and depending on
        the complexity of the task may not yield the desired results. They are
        however very good at synthesising information from their training set,
        and thus can be useful to explain the biological context of, for
        instance, a particular gene set or cell type.

        ## About the models
        The default model loaded is OpenAIs `gpt-3.5-turbo` model, which in the
        standard version has a token limit of 4000 per conversation. This model
        currently comes in two versions, `0301` and `0613`. The latter is the
        more recent one with improved interpretation of system messages and
        capabilities to handle functions (returning attribute values of a given
        function as JSON). Additionally, OpenAI provide a `gpt-3.5-turbo-16k`
        model with increased token limit of 16000 per conversation. This model
        is slightly more expensive, but can be useful for longer conversations,
        particularly when including the Retrieval-Augmented Generation / prompt
        injection feature.

        """
    )


def download_chat_history(bcl: BioChatterLight):
    """
    Button to download the chat history as a JSON file.

    Args:
        bcl: current biochatter-light instance
    """
    bcl.update_json_history()
    st.download_button(
        label="Download Chat History",
        data=ss.json_history,
        file_name="chat_history.json",
        mime="application/json",
        use_container_width=True,
    )


def download_complete_history(bcl: BioChatterLight):
    """
    Button to download the complete message history (i.e., including the
    system prompts) as a JSON file.

    Args:
        bcl: current biochatter-light instance
    """
    d = bcl.complete_history()

    if d == "{}":
        st.download_button(
            label="Download Message History",
            data="",
            use_container_width=True,
            disabled=True,
        )
        return

    st.download_button(
        label="Download Message History",
        data=d,
        file_name="complete_history.json",
        mime="application/json",
        use_container_width=True,
    )


def spacer(n=2, line=False, next_n=0):
    """
    Insert a spacer between two elements.
    """
    for _ in range(n):
        st.write("")
    if line:
        st.tabs([" "])
    for _ in range(next_n):
        st.write("")


def show_primary_model_prompts():
    """
    Prompt engineering panel: primary model.
    """
    st.markdown(
        "`📎 Assistant`: Here you can edit the prompts used to set up the primary "
        "LLM. You can modify or remove the existing prompts, as well as add new "
        "ones. They will be used in the order they are listed in here."
    )

    for num, msg in enumerate(ss.prompts["primary_model_prompts"]):
        field, button = st.columns([4, 1])
        with field:
            ss.prompts["primary_model_prompts"][num] = st.text_area(
                label=str(num + 1),
                value=msg,
                label_visibility="collapsed",
                placeholder="Enter your prompt here.",
            )
        with button:
            st.button(
                f"Remove prompt {num + 1}",
                on_click=remove_prompt,
                args=(ss.prompts["primary_model_prompts"], num),
                key=f"remove_primary_prompt_{num}",
                use_container_width=True,
            )

    st.button(
        "Add New Primary Model Prompt",
        on_click=add_prompt,
        args=(ss.prompts["primary_model_prompts"],),
    )


def show_correcting_agent_prompts():
    """
    Prompt engineering panel: correcting agent.
    """
    st.markdown(
        "`📎 Assistant`: Here you can edit the prompts used to set up the "
        "correcting agent. You can modify or remove the existing prompts, as "
        "well as add new ones. They will be used in the order they are listed "
        "in here."
    )

    for num, msg in enumerate(ss.prompts["correcting_agent_prompts"]):
        field, button = st.columns([4, 1])
        with field:
            ss.prompts["correcting_agent_prompts"][num] = st.text_area(
                label=str(num + 1),
                value=msg,
                label_visibility="collapsed",
                placeholder="Enter your prompt here.",
            )
        with button:
            st.button(
                f"Remove prompt {num + 1}",
                on_click=remove_prompt,
                args=(ss.prompts["correcting_agent_prompts"], num),
                key=f"remove_prompt_{num}",
                use_container_width=True,
            )

    st.button(
        "Add New Correcting Agent Prompt",
        on_click=add_prompt,
        args=(ss.prompts["correcting_agent_prompts"],),
    )


def show_rag_agent_prompts():
    """
    Prompt engineering panel: Retrieval-Augmented Generation.
    """
    st.markdown(
        "`📎 Assistant`: Here you can edit the prompts used to set up the "
        "Retrieval-Augmented Generation task. Text passages from any uploaded "
        "documents will be passed on to the primary model using these prompts. "
        "The placeholder `{statements}` will be replaced by the text passages. "
        "Upload documents and edit vector database settings in the "
        "`Retrieval-Augmented Generation` tab."
    )

    for num, msg in enumerate(ss.prompts["rag_agent_prompts"]):
        field, button = st.columns([4, 1])
        with field:
            ss.prompts["rag_agent_prompts"][num] = st.text_area(
                label=str(num + 1),
                value=msg,
                label_visibility="collapsed",
                placeholder="Enter your prompt here.",
            )
        with button:
            st.button(
                f"Remove prompt {num + 1}",
                on_click=remove_prompt,
                args=(ss.prompts["rag_agent_prompts"], num),
                key=f"remove_prompt_{num}",
                use_container_width=True,
            )

    st.button(
        "Add New Prompt",
        on_click=add_prompt,
        args=(ss.prompts["rag_agent_prompts"],),
    )


def show_tool_prompts():
    """
    Prompt engineering panel: tool-specific.
    """
    st.markdown(
        "`📎 Assistant`: Here you can edit the tool-specific prompts given to the "
        "primary LLM. You can modify the names as well as the prompts "
        "themselves. The names are what is used to automatically select the "
        "prompt based on the filename of the uploaded file (the name of the "
        "prompt should be a substring of the filename). You can also add new "
        "prompts here. Please note that the order of the prompts is neither "
        "relevant nor preserved. Also note that the `{df}` placeholder is used "
        "to insert the uploaded data into the prompt, and thus should always be "
        "included."
    )

    for nam in list(ss.prompts["tool_prompts"].keys()):
        msg = ss.prompts["tool_prompts"][nam]
        label, field, fill = st.columns([3, 21, 6])
        with label:
            st.write("Name:")
        with field:
            nunam = st.text_input(
                label="Name",
                value=nam,
                label_visibility="collapsed",
                placeholder="Enter a name for your prompt.",
            )
        with fill:
            st.write("")

        area, button = st.columns([4, 1])
        with area:
            numsg = st.text_area(
                label=nam,
                value=msg,
                label_visibility="collapsed",
                placeholder="Enter your prompt here.",
            )
        with button:
            st.button(
                f"Remove prompt `{nam}`",
                on_click=remove_tool_prompt,
                args=(nam,),
                key=f"remove_prompt_{nam}",
                use_container_width=True,
            )

        if nunam != nam:
            ss.prompts["tool_prompts"][nunam] = ss.prompts["tool_prompts"].pop(
                nam
            )
            st.experimental_rerun()
        elif numsg != msg:
            ss.prompts["tool_prompts"][nunam] = numsg

    st.button(
        "Add New Tool Prompt",
        on_click=add_tool_prompt,
    )


def add_prompt(prompt_list):
    """
    Add a new prompt to the given list.
    """
    prompt_list.append("")


def remove_prompt(prompt_list, num):
    """
    Remove the prompt with the given number from the given list.
    """
    del prompt_list[num]


def add_tool_prompt():
    """
    Add a new tool prompt.
    """
    ss.prompts["tool_prompts"][""] = ""


def remove_tool_prompt(nam):
    """
    Remove the tool prompt with the given name.
    """
    ss.prompts["tool_prompts"].pop(nam)


def prompt_save_load_reset():
    """
    Prompt engineering panel: save and load prompt set JSON files. Reset not
    implemented yet.
    """
    save, load = st.columns(2)
    with save:
        prompt_save_button()
    with load:
        uploaded_file = st.file_uploader(
            "Load",
            type="json",
            label_visibility="collapsed",
            accept_multiple_files=False,
            key="load_prompt_set",
        )
        if uploaded_file:
            load_prompt_set(uploaded_file)


def prompt_save_button():
    """
    Save the current prompt set as a JSON file.
    """
    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d_%H-%M-%S")
    st.download_button(
        "Save Full Prompt Set (JSON)",
        data=save_prompt_set(),
        use_container_width=True,
        file_name=f"biochatter-light_prompt_set-{date}.json",
    )


def save_prompt_set():
    """
    Return JSON serialisation of the current prompt set.

    Returns:
        str: JSON serialisation of the current prompt set.
    """
    return json.dumps(ss.prompts)


def load_prompt_set(uploaded_file):
    """
    Given an uploaded JSON file, load the prompts from it.

    Args:
        uploaded_file (FileUploader): The uploaded JSON file.
    """
    ss.prompts = json.load(uploaded_file)


def reset_button():
    """
    Button to reset the entire app.
    """
    st.button(
        "♻️ Reset App",
        on_click=reset_app,
        use_container_width=True,
    )


def reset_app():
    """
    Reset the app to its initial state.
    """
    ss.clear()
    ss._primary_model = "gpt-3.5-turbo"


def show_about_section():
    if not ss.get("what_messages"):
        ss.what_messages = WHAT_MESSAGES

    if not ss.get("how_messages"):
        ss.how_messages = HOW_MESSAGES

    what, how = st.columns(2)
    with what:
        st.markdown(
            "### "
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "ℹ️ What"
        )
        for i in range(3):
            msg = ss.what_messages[i]
            st.button(
                msg,
                use_container_width=True,
                on_click=shuffle_messages,
                args=(ss.what_messages, i),
            )
    with how:
        st.markdown(
            "### "
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "🔧 How"
        )
        for i in range(3):
            msg = ss.how_messages[i]
            st.button(
                msg,
                use_container_width=True,
                on_click=shuffle_messages,
                args=(ss.how_messages, i),
            )

    st.info(
        "This is the lightweight frontend for BioChatter in pure Python. "
        "For more information on the platform, please see [our preprint](https://arxiv.org/abs/2305.06488)! "
        "If you'd like to contribute to the project, please find us on "
        "[GitHub](https://github.com/biocypher) or "
        "[Zulip](https://biocypher.zulipchat.com). We'd love to hear from you!"
    )


def shuffle_messages(l: list, i: int):
    """Replaces the message at position i with the message at position 3, and
    moves the replaced message to the end of the list."""
    l[i], l[3] = (
        l[3],
        l[i],
    )
    l.append(l.pop(3))


def rag_agent_panel():
    """

    Upload files for Retrieval-Augmented Generation, one file at a time. Upon
    upload, document is split and embedded into a connected vector DB using the
    `vectorstore.py` module of biochatter. The top k results of similarity
    search of the user's query will be injected into the prompt to the primary
    model (only once per query). The panel displays a file_uploader panel,
    settings for the text splitter (chunk size and overlap, separators), and a
    slider for the number of results to return. Also displays the list of
    closest matches to the last executed query.

    """

    if ss.use_rag_agent:
        if os.getenv("DOCKER_COMPOSE"):
            # running in same docker compose as biochatter-light
            connection_args = {"host": "milvus-standalone", "port": "19530"}
        else:
            # running on host machine from the milvus docker compose
            connection_args = {"host": "localhost", "port": "19530"}

        embedding_func = OpenAIEmbeddings(
            api_key=ss.get("openai_api_key"),
            model="text-embedding-ada-002",
        )

        ss.conversation.set_rag_agent(
            RagAgent(
                mode="vectorstore",
                model_name="gpt-3.5-turbo",
                connection_args=connection_args,
                use_prompt=True,
                embedding_func=embedding_func,
                n_results=3,
            )
        )

        if not ss.get("embedder"):
            ss.embedder = DocumentEmbedder(
                connection_args=connection_args,
            )
            ss.embedder.connect()

    disabled = ss.online or (not ss.use_rag_agent)

    uploader, settings = st.columns(2)

    with uploader:
        st.markdown(
            "### "
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "📄 Upload Document"
        )
        if disabled:
            st.warning(
                "To use the feature, please enable it in the settings panel. →"
            )
        if ss.get("online"):
            st.warning(
                "This feature is currently not available in online mode, as it "
                "requires connection to a vector database. Please run the app "
                "locally to use this feature. See the [README]("
                "https://github.com/biocypher/biochatter-light#-retrieval-augmented-generation--in-context-learning)"
                " for more info."
            )
        st.info(
            "Upload documents one at a time. Upon upload, the document is "
            "split according to the settings and the embeddings are stored in "
            "the connected vector database."
        )
        with st.form("Upload Document", clear_on_submit=True):
            uploaded_file = st.file_uploader(
                "Upload a document for Retrieval-Augmented Generation",
                type=["txt", "pdf"],
                label_visibility="collapsed",
                disabled=disabled,
            )
            submitted = st.form_submit_button(
                "Upload", use_container_width=True
            )
        if submitted and uploaded_file is not None:
            if not ss.get("uploaded_files"):
                ss.uploaded_files = []

            ss.uploaded_files.append(uploaded_file.name)

            with st.spinner("Saving embeddings ..."):
                val = uploaded_file.getvalue()
                reader = DocumentReader()
                if uploaded_file.type == "application/pdf":
                    doc = reader.document_from_pdf(val)
                elif uploaded_file.type == "text/plain":
                    doc = reader.document_from_txt(val)
                try:
                    ss.embedder.save_document(doc)
                    ss.upload_success = True
                    if not ss.get("embedder_used"):
                        ss.embedder_used = True
                        ss.first_document_uploaded = True
                except MilvusException as e:
                    st.error(
                        "An error occurred while saving the embeddings. Please "
                        "check if Milvus is running. For information on the "
                        "Docker Compose setup, see the [README]("
                        "https://github.com/biocypher/biochatter-light#-retrieval-augmented-generation--in-context-learning)."
                    )
                    st.error(e)
                    return

        if ss.get("upload_success"):
            st.success("Embeddings saved!")

        if ss.get("conversation"):
            if ss.conversation.current_statements:
                st.markdown(
                    "### "
                    "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                    "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                    "🔍 Search Results"
                )
                st.info(
                    "The following are the closest matches to the last executed "
                    "query."
                )
                out = ""
                for s in ss.conversation.current_statements:
                    out += f"- {s}\n"
                st.markdown(out)
            else:
                st.info(
                    "The search results will be displayed here once you've executed "
                    "a query."
                )

    with settings:
        st.markdown(
            "### "
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "🔧 Settings"
        )

        # checkbox for whether to use the rag_agent prompt
        st.checkbox(
            "Use Retrieval-Augmented Generation to inject search results into the prompt",
            value=ss.use_rag_agent,
            on_change=toggle_rag_agent_prompt,
            disabled=ss.online,
        )

        # only show those if we have a rag_agent
        if len(ss.conversation.rag_agents) > 0:
            st.checkbox(
                "Split by characters (instead of tokens)",
                ss.embedder.split_by_characters,
                on_change=toggle_split_by_characters,
                disabled=disabled,
                help=(
                    "Deactivate this to split the input text by tokens instead of "
                    "characters. Be mindful that this results in much longer "
                    "fragments, so it could be useful to reduce the chunk size."
                ),
            )

            ss.embedder.chunk_size = st.slider(
                label=(
                    "Chunk size: how large should the embedded text fragments be?"
                ),
                min_value=100,
                max_value=5000,
                value=1000,
                step=1,
                disabled=disabled,
                help=(
                    "The larger the chunk size, the more context is provided to "
                    "the model. The lower the chunk size, the more individual "
                    "chunks can be used inside the token length limit of the "
                    "model. While the value can be changed at any time, it is "
                    "recommended to set it before uploading documents."
                ),
            )
            ss.embedder.chunk_overlap = st.slider(
                label="Overlap: should the chunks overlap, and by how much?",
                min_value=0,
                max_value=1000,
                value=0,
                step=1,
                disabled=disabled,
            )
            # ss.rag_agent.separators = st.multiselect(
            #     "Separators (defaults: new line, comma, space)",
            #     options=ss.rag_agent.separators,
            #     default=ss.rag_agent.separators,
            #     disabled=disabled,
            # )
            ss.conversation.rag_agents[0].n_results = st.slider(
                label=(
                    "Number of results: how many chunks should be used to "
                    "supplement the prompt?"
                ),
                min_value=1,
                max_value=20,
                value=3,
                step=1,
                disabled=disabled,
            )

        if ss.get("uploaded_files"):
            st.markdown(
                "### "
                "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                "📄 Uploaded Documents"
            )
            st.info(
                "The following documents have been uploaded for "
                "embedding / prompt injection. Only the current session is "
                "captured; the connected vector database currently needs to "
                "be manually maintained."
            )
            s = ""
            for f in ss.uploaded_files:
                s += "- " + f + "\n"
            st.markdown(s)
        else:
            st.info(
                "Uploaded documents will be displayed here once you have "
                "uploaded them."
            )


def toggle_rag_agent_prompt():
    """Toggles the use of the rag_agent prompt."""
    ss.use_rag_agent = not ss.use_rag_agent


def toggle_split_by_characters():
    """Toggles the splitting of the input text by characters vs tokens."""
    ss.rag_agent.split_by_characters = not ss.rag_agent.split_by_characters


def correcting_agent_panel():
    ss.correct = st.checkbox(
        "Use the correcting agent to catch and correct false information",
        value=ss.correct,
    )
    ss.split_correction = st.checkbox(
        "Split the response into sentences for correction",
        value=ss.split_correction,
    )

    if ss.get("conversation"):
        if ss.split_correction != ss.conversation.split_correction:
            ss.conversation.split_correction = ss.split_correction
        if ss.correct != ss.conversation.correct:
            ss.conversation.correct = ss.correct

    test_correct = st.text_area(
        "Test correction functionality here:",
        placeholder=(
            "Enter a false statement to prompt a correction. Press [Enter] for "
            "a new line, and [CTRL+Enter] or [⌘+Enter] to submit."
        ),
    )

    if test_correct:
        if not ss.get("conversation"):
            st.write("No model loaded. Please load a model first.")
            return

        correction = ss.conversation._correct_response(test_correct)

        if str(correction).lower() in ["ok", "ok."]:
            st.success("The model found no correction to be required.")
        else:
            st.error(
                f"The model found the following correction: `{correction}`"
            )


def genetics_panel():
    gene, patient = st.tabs(["Gene view", "Patient view"])

    with gene:
        gene_panel()

    with patient:
        st.text_input("Enter patient ID:", key="patient_id")


def gene_panel():
    gene_name = st.text_input("Enter gene name (case-insensitive):")

    # if input, show table
    if gene_name:
        # get data
        cn_df, vn_df = _get_gene_data(gene_name.upper())

        cnas = 0
        vnas = 0

        cna_text = "CNAs"
        if cn_df is not None:
            cnas = cn_df.shape[0]
            if cnas == 1:
                cna_text = "CNA"

        vna_text = "variants"
        if vn_df is not None:
            vnas = vn_df.shape[0]
            if vnas == 1:
                vna_text = "variant"

        # genomespy link
        st.markdown(
            f"{cnas} {cna_text}, {vnas} {vna_text}. Links: "
            f"[GenomeSpy](https://genomespy.app/decider/gene/{gene_name}) "
        )

        if cn_df is None and vn_df is None:
            st.write("No data found for this gene.")

        if cn_df is not None:
            st.markdown("#### Copy Number Alterations")
            st.dataframe(cn_df, hide_index=False)

        if vn_df is not None:
            st.markdown("#### Sequence Variants")
            st.dataframe(vn_df, hide_index=False)


def _get_gene_data(gene_name):
    """
    Get gene data from the API.
    """
    _connect_to_neo4j()

    gene_id = "hgnc:" + gene_name

    result = ss.neodriver.query(
        "MATCH (g:Gene) "
        "WHERE g.id = $gene_id "
        "OPTIONAL MATCH (g)<-[cn:SampleToGeneCopyNumberAlteration]-(cns:Sample)"
        "OPTIONAL MATCH (g)<-[vn:VariantToGeneAssociation]-(v:SequenceVariant)<-[ss:SampleToVariantAssociation]-(vns:Sample)"
        "RETURN g, cns, v, vns, "
        "cn.id, cn.breaksInGene, cn.nMajor, cn.nMinor, cn.purifiedBaf, cn.purifiedLogR, cn.minPurifiedLogR, cn.maxPurifiedLogR, cn.purifiedLoh, "
        "vn.id, "
        "ss.id ",
        gene_id=gene_id,
    )

    if not result[0]:
        return None, None

    patterns = result[0]
    # header: gene information (should be the same gene in all rows)
    gene = patterns[0]["g"]
    read_name = str(gene["id"]).replace("hgnc:", "")
    st.markdown(
        f"""
                ### Gene: {read_name} ({gene['ID']})
                chr: {gene['chr']}, start: {gene['start']}, end: {gene['end']}
                """
    )
    # format result as dataframe
    # for each pattern, create row(s) in dataframe
    cn_df = pd.DataFrame(
        columns=[
            "alteration_id",
            "breaks_in_gene",
            "n_major",
            "n_minor",
            "purified_baf",
            "purified_logr",
            "min_purified_logr",
            "max_purified_logr",
            "purified_loh",
            "sample_id",
        ]
    )
    vn_df = pd.DataFrame(
        columns=[
            "alteration_id",
            "mane",
            "cadd_phred",
            "aa_mane",
            "func_mane",
            "ex_func_mane",
            "clnsig",
            "clnrevstat",
            "gnomad_max",
            "ref",
            "alt",
            "pos",
            "cosmic_total_occ",
            "sample_id",
        ]
    )
    for pattern in patterns:
        # get copy numbers
        if pattern.get("cn.id") is not None:
            if pattern["cn.id"] in cn_df["alteration_id"]:
                pass
            else:
                cn_id = pattern["cn.id"]
                cn_breaks = pattern["cn.breaksInGene"]
                cn_n_major = pattern["cn.nMajor"]
                cn_n_minor = pattern["cn.nMinor"]
                cn_purified_baf = pattern["cn.purifiedBaf"]
                cn_purified_logr = pattern["cn.purifiedLogR"]
                cn_min_purified_logr = pattern["cn.minPurifiedLogR"]
                cn_max_purified_logr = pattern["cn.maxPurifiedLogR"]
                cn_purified_loh = pattern["cn.purifiedLoh"]
                cns = pattern["cns"]["id"]
                cn_df = cn_df.append(
                    {
                        "alteration_id": cn_id,
                        "breaks_in_gene": cn_breaks,
                        "n_major": cn_n_major,
                        "n_minor": cn_n_minor,
                        "purified_baf": cn_purified_baf,
                        "purified_logr": cn_purified_logr,
                        "min_purified_logr": cn_min_purified_logr,
                        "max_purified_logr": cn_max_purified_logr,
                        "purified_loh": cn_purified_loh,
                        "sample_id": cns,
                    },
                    ignore_index=True,
                )
        # get variants
        if pattern.get("vn.id") is not None:
            if pattern["vn.id"] in list(vn_df["alteration_id"]):
                pass
            else:
                vn_id = pattern["vn.id"]
                v_mane = pattern["v"]["Gene.MANE"]
                v_cadd = pattern["v"]["CADD_phred"]
                aa_mane = pattern["v"]["AAChange.MANE"]
                func_mane = pattern["v"]["Func.MANE"]
                ex_func_mane = pattern["v"]["ExonicFunc.MANE"]
                v_clnsig = pattern["v"]["CLNSIG"]
                v_clnrevstat = pattern["v"]["CLNREVSTAT"]
                v_gnomad_max = pattern["v"]["gnomAD_genome_max"]
                v_ref = pattern["v"]["REF"]
                v_alt = pattern["v"]["ALT"]
                v_pos = pattern["v"]["POS"]
                v_totocc = pattern["v"]["COSMIC_TOTAL_OCC"]
                vns = pattern["vns"]["id"]
                vn_df = vn_df.append(
                    {
                        "alteration_id": vn_id,
                        "mane": v_mane,
                        "cadd_phred": v_cadd,
                        "aa_mane": aa_mane,
                        "func_mane": func_mane,
                        "ex_func_mane": ex_func_mane,
                        "clnsig": v_clnsig,
                        "clnrevstat": v_clnrevstat,
                        "gnomad_max": v_gnomad_max,
                        "ref": v_ref,
                        "alt": v_alt,
                        "pos": v_pos,
                        "cosmic_total_occ": v_totocc,
                        "sample_id": vns,
                    },
                    ignore_index=True,
                )

    # aggregate cn_df grouping samples in new column "sample_ids", drop
    # "sample_id" and duplicate rows
    cn_df["sample_ids"] = cn_df.groupby("alteration_id")["sample_id"].transform(
        lambda x: ",".join(x)
    )
    cn_df = cn_df.drop(columns=["sample_id"])
    cn_df = cn_df.drop_duplicates()

    return cn_df, vn_df


def kg_panel():
    """
    Allow connecting to a BioCypher knowledge graph and querying by asking the
    LLM to answer questions about the graph.
    """
    # Short info
    st.markdown(
        "This section allows connecting to a DBMS and querying it by asking "
        "natural language questions about the knowledge graph. It works by "
        "sharing some information about the [BioCypher](https://biocypher.org) "
        "KG with the LLM in "
        "the form of a schema configuration, which can be enriched by "
        "information gained in building the graph. In the former case, this "
        "is achieved by using the `schema_config.yaml` file used to "
        "configure BioCypher, while the latter uses the `schema_info.yaml` "
        "that can be generated by BioCypher after the KG has been built. "
        "Using the `schema_info.yaml` file is recommended, as it contains "
        "more information about the graph. "
    )

    dbms_select, connection, upload = st.columns([1, 2, 2])

    with dbms_select:
        # drop down: select DBMS type
        dbms_type = st.selectbox(
            "Database type:",
            options=["Neo4j", "PostgreSQL", "ArangoDB"],
            index=0,
            on_change=_regenerate_query,
        )

    with connection:
        ip, port = st.columns(2)
        with ip:
            st.text_input(
                "Database IP address:", value="localhost", key="db_ip"
            )
        with port:
            st.text_input("Database port:", value="7687", key="db_port")

        # try connecting (only neo4j for now)
        if dbms_type == "Neo4j":
            success = _connect_to_neo4j()
        elif dbms_type == "PostgreSQL":
            success = False
        elif dbms_type == "ArangoDB":
            success = False

        if not success:
            if dbms_type == "Neo4j":
                st.error(
                    "Could not connect to the database. Please check your "
                    "connection settings."
                )
                st.button(
                    "Retry",
                    on_click=_connect_to_neo4j,
                    use_container_width=True,
                )
            else:
                st.error(
                    "This database type is not yet supported. Please select "
                    "Neo4j."
                )
        else:
            st.success(f"Connected to Neo4j database at {ss.get('db_ip')}.")

    with upload:
        schema_file = st.file_uploader(
            "Upload schema configuration or info file",
            type=["yaml"],
        )
        if schema_file:
            try:
                ss.schema_dict = yaml.safe_load(schema_file)
                ss.schema_from = "file"
                st.success("File uploaded!")
            except yaml.YAMLError as e:
                st.error("Could not load file. Please try again.")
                st.error(e)

        if ss.get("schema_dict"):
            st.success(
                f"Schema configuration loaded from {ss.get('schema_from')}!"
            )
        else:
            st.error(
                "Please upload a schema configuration or info file to continue."
            )

    if success and ss.get("schema_dict"):
        question = st.text_input(
            "Enter your question here:",
            on_change=_regenerate_query,
            # value="How many people named Donald are in the database?",
        )

        # TODO get schema from graph (when connecting) or upload
        # TODO ask about the schema more generally, without generating a query?

        if question:
            # manual schema info file
            prompt_engine = BioCypherPromptEngine(
                schema_config_or_info_dict=ss.schema_dict,
            )

            # generate query if not modified
            if ss.get("generate_query"):
                with st.spinner("Generating query ..."):
                    if dbms_type == "Neo4j":
                        ss.current_query = prompt_engine.generate_query(
                            question, dbms_type
                        )

            if dbms_type == "Neo4j":
                result = _run_neo4j_query(ss.current_query)

            elif dbms_type == "PostgreSQL":
                result = [
                    (
                        "Here would be a result if we had a PostgreSQL "
                        "implementation."
                    )
                ]

            elif dbms_type == "ArangoDB":
                result = [
                    (
                        "Here would be a result if we had an ArangoDB "
                        "implementation."
                    )
                ]

            st.text_area(
                "Generated query (modify to rerun):",
                key="current_query",
                height=200,
                on_change=_rerun_query,
            )

            st.markdown("### Results")
            if result[0]:
                st.write(result[0])

        if ss.get("schema_dict"):
            st.markdown("### Schema Info")
            st.write(ss.schema_dict)


def _rerun_query():
    """
    Rerun the query using the modified query.
    """
    ss.generate_query = False


def _regenerate_query():
    """
    Regenerate the query using the new question.
    """
    ss.generate_query = True


def _connect_to_neo4j():
    """
    Connect to the Neo4j database.
    """
    db_uri = "bolt://" + ss.get("db_ip") + ":" + ss.get("db_port")
    ss.neodriver = nu.Driver(
        db_name=ss.get("db_name") or "neo4j",
        db_uri=db_uri,
    )

    # return True if connected, False if no DB found
    if ss.get("neodriver").status == "no connection":
        return False
    else:
        _find_schema_info_node()
        return True


def _find_schema_info_node():
    """
    Look for a schema info node in the connected BioCypher graph and load the
    schema info if present.
    """
    result = ss.neodriver.query("MATCH (n:Schema_info) RETURN n LIMIT 1")

    if result[0]:
        schema_info_node = result[0][0]["n"]
        ss.schema_dict = json.loads(schema_info_node["schema_info"])
        ss.schema_from = "graph"


def _run_neo4j_query(query):
    """
    Run cypher query against the Neo4j database.
    """
    _connect_to_neo4j()

    result = ss.neodriver.query(query)

    return result


def refresh():
    ss.input = ""
    st.experimental_rerun()


def _startup():
    # USER
    ss.user = "default"

    # SETTINGS
    ss.use_rag_agent = False
    # TODO these are for testing, change later
    ss.xinference_base_url = "http://llm.biocypher.org"
    ss.xinference_api_key = "none"

    # PROMPTS
    ss.prompts = {
        "primary_model_prompts": PRIMARY_MODEL_PROMPTS,
        "correcting_agent_prompts": CORRECTING_AGENT_PROMPTS,
        "tool_prompts": TOOL_PROMPTS,
        "rag_agent_prompts": RAG_PROMPTS,
        "schema_prompts": SCHEMA_PROMPTS,
    }
    ss.correct = True
    ss.split_correction = False
    ss.generate_query = True

    # CHECK ENVIRONMENT
    if os.getenv("ON_STREAMLIT"):
        ss.on_streamlit = True
        ss.online = True
    elif os.getenv("ON_SELFHOSTED"):
        ss.on_selfhosted = True
        ss.online = True
    else:
        ss.online = False

    # do we have keys in the environment?
    update_api_keys()

    # SHOW INTRO MESSAGE AND SETUP INSTRUCTIONS
    ss.show_intro = True
    ss.show_setup = True


def mode_select():
    data, papers, both = st.columns(3)

    ss.mode = "getting_context"

    with data:
        st.button(
            "Talk about data.",
            use_container_width=True,
            on_click=set_data_mode,
        )

    with papers:
        st.button(
            "Talk about papers / notes.",
            use_container_width=True,
            on_click=set_papers_mode,
            disabled=ss.online,
        )

    with both:
        st.button(
            "Talk about data and papers / notes.",
            use_container_width=True,
            on_click=set_both_mode,
            disabled=ss.online,
        )

    if ss.online:
        st.info(
            "Retrieval-Augmented Generation is currently not available in the "
            "online version. Please use the Docker Compose setup in our "
            "[GitHub repository](https://github.com/biocypher/biochatter-light#-retrieval-augmented-generation--in-context-learning) "
            "to run BioChatter Light locally and use this feature."
        )


def set_data_mode():
    ss.conversation_mode = "data"
    ss.bcl._ask_for_context("data")


def set_papers_mode():
    ss.conversation_mode = "papers"
    ss.bcl._ask_for_context("papers")


def set_both_mode():
    ss.conversation_mode = "both"
    ss.bcl._ask_for_context("data and papers")


def waiting_for_rag_agent():
    st.info("Use the 'Retrieval-Augmented Generation' tab to embed documents.")


def main():
    # NEW SESSION
    if not ss.get("mode"):
        _startup()

    # DEFAULT MODEL
    if not ss.get("primary_model"):
        ss["primary_model"] = "gpt-3.5-turbo"

    # INTERFACE
    if not ss.get("bcl"):
        ss.bcl = BioChatterLight()
    bcl = ss.bcl

    # CHANGE MODEL
    if not ss.get("active_model") == ss.primary_model:
        bcl.set_model(ss.primary_model)
        ss.active_model = ss.primary_model
        ss.mode = bcl._check_for_api_key(write=False, input=ss.input)
        # TODO: warn user that we are resetting?

    # TOKEN USAGE
    if not ss.get("token_usage"):
        ss.token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }

    # UPDATE RAG AGENT
    if ss.get("rag_agent"):
        if ss.rag_agent.use_prompt:
            ss.conversation.set_rag_agent(ss.rag_agent)

    # TABS
    (
        chat_tab,
        prompts_tab,
        rag_agent_tab,
        correct_tab,
        annot_tab,
        exp_design_tab,
        genetics_tab,
        kg_tab,
    ) = st.tabs(
        [
            "Chat",
            "Prompt Engineering",
            "Retrieval-Augmented Generation",
            "Correcting Agent",
            "Cell Type Annotation",
            "Experimental Design",
            "Genetics Annotation",
            "Knowledge Graph",
        ]
    )

    with chat_tab:
        # WELCOME MESSAGE AND CHAT HISTORY
        st.markdown(
            "Welcome to ``BioChatter Light``! "
            ":violet[If you are on a small screen, you may need to "
            "shift-scroll to the right to see all tabs. -->]"
        )

        if ss.show_intro:
            show_about_section()

        if ss.show_setup:
            bcl._display_setup()

        bcl._display_history()

        # CHAT BOT LOGIC
        if ss.input or ss.mode == "waiting_for_rag_agent":
            if ss.mode == "getting_key":
                ss.mode = bcl._get_api_key(ss.input)
                ss.show_intro = False
                refresh()

            elif ss.mode == "using_community_key":
                ss.input = ""  # ugly
                ss.mode = bcl._check_for_api_key()
                ss.show_intro = False
                refresh()

            elif ss.mode == "getting_name":
                ss.mode = bcl._get_user_name()
                ss.show_intro = False

            elif ss.mode == "getting_context":
                # TODO: Sometimes the app goes from mode select straight into
                # context, and then obviously the conversation mode is not set
                # yet. It only happens if this is the first break point. If
                # something is debugged before, or if something is pressed in
                # the app before entering the name (such as one of the panels at
                # the top), it works fine.

                bcl._get_context()
                if ss.conversation_mode in ["data", "both"]:
                    ss.mode = bcl._ask_for_data_input()
                else:
                    if not ss.get("embedder_used"):
                        st.write("Please embed at least one document.")
                        ss.mode = "waiting_for_rag_agent"
                    else:
                        ss.mode = bcl._start_chat()

            elif ss.mode == "waiting_for_rag_agent":
                if ss.get("embedder_used"):
                    ss.mode = bcl._start_chat()

            elif ss.mode == "getting_data_file_input":
                ss.mode = bcl._get_data_input()

            elif ss.mode == "getting_data_file_description":
                ss.mode = bcl._get_data_file_description()

            elif ss.mode == "asking_for_manual_data_input":
                ss.mode = bcl._ask_for_manual_data_input()

            elif ss.mode == "getting_manual_data_input":
                ss.mode = bcl._get_data_input_manual()

            elif ss.mode == "chat":
                with st.spinner("Thinking ..."):
                    ss.response, ss.token_usage = bcl._get_response()

            # DEMO LOGIC
            elif ss.mode == "demo_key":
                ss.input = ""  # ugly
                bcl._check_for_api_key()
                ss.show_intro = False
                refresh()

            elif ss.mode == "demo_start":
                bcl._get_user_name()

            elif ss.mode == "demo_context":
                bcl._get_context()
                bcl._ask_for_data_input()

            elif ss.mode == "demo_tool":
                st.write("(Here, we simulate the upload of a data file.)")
                bcl._get_data_input()

            elif ss.mode == "demo_manual":
                bcl._get_data_input_manual()
                st.write(
                    "(The next step will involve sending a basic query to the "
                    "model. This may take a few seconds.)"
                )

            elif ss.mode == "demo_chat":
                with st.spinner("Thinking ..."):
                    ss.response, ss.token_usage = bcl._get_response()
                bcl._write_and_history(
                    "📎 Assistant",
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
            reset_button()
            if ss.mode == "getting_data_file_input":
                file_uploader()
            with st.expander("About"):
                app_info()
            if (
                ss.get("show_community_select", False)
                and ss.get("primary_model") in OPENAI_MODELS
                and community_possible()
            ):
                remaining_tokens()
                community_select()
            display_token_usage()
            d1, d2 = st.columns(2)
            with d1:
                download_chat_history(bcl)
            with d2:
                download_complete_history(bcl)
            model_select()

        # CHAT BOX

        if ss.mode == "getting_key":
            if ss.primary_model in OPENAI_MODELS:
                openai_key_chat_box()
            elif ss.primary_model in HUGGINGFACE_MODELS:
                huggingface_key_chat_box()
        elif ss.mode == "getting_mode":
            mode_select()
        elif ss.mode == "getting_data_file_input":
            data_input_buttons()
        elif ss.mode in ["getting_name", "getting_context"]:
            chat_line()
            autofocus_line()
        elif ss.mode == "waiting_for_rag_agent":
            waiting_for_rag_agent()
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
                "`📎 Assistant`: Cell type annotation "
                f"{OFFLINE_FUNCTIONALITY}"
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
            f"`📎 Assistant`: Experimental design functionality {OFFLINE_FUNCTIONALITY}"
        )

    with prompts_tab:
        st.markdown(
            "The construction of prompts is a crucial step in the use of "
            "Large Language Models. However, it can be a subtle and complex "
            "task, often requiring empirical testing on prompt composition "
            "due to the black-box nature of the models. We provide composable "
            "prompts and prompt templates (which can include variables), as "
            "well as save and load functionality for full prompt sets to "
            "facilitate testing, reproducibility, and sharing."
        )

        if not ss.mode in [
            "getting_key",
            "using_community_key",
            "getting_name",
            "getting_context",
        ]:
            st.markdown(
                "`📎 Assistant`: Prompt tuning is only available before "
                "initialising the conversation, that is, before giving a "
                "context. Please reset the app to tune the prompt set."
            )
            prompt_save_button()

        else:
            prompt_save_load_reset()
            ss.prompts_box = st.selectbox(
                "Select a prompt set",
                (
                    "Primary Model",
                    "Correcting Agent",
                    "Tools",
                    "Retrieval-Augmented Generation",
                ),
            )

            if ss.prompts_box == "Primary Model":
                show_primary_model_prompts()

            elif ss.prompts_box == "Correcting Agent":
                show_correcting_agent_prompts()

            elif ss.prompts_box == "Tools":
                show_tool_prompts()

            elif ss.prompts_box == "Retrieval-Augmented Generation":
                show_rag_agent_prompts()

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
        if ss.get("online"):
            st.markdown(
                f"`📎 Assistant`: Correction agent functionality {OFFLINE_FUNCTIONALITY}"
            )
        else:
            correcting_agent_panel()

    with rag_agent_tab:
        st.markdown(
            "While Large Language Models have access to vast amounts of "
            "knowledge, this knowledge only includes what was present in "
            "their training set, and thus excludes very current research "
            "as well as research articles that are not open access. To "
            "fill in the gaps of the model's knowledge, we include a "
            "Retrieval-Augmented Generation approach that stores knowledge from "
            "user-provided documents in a vector database, which can be "
            "used to supplement the model prompt by retrieving the most "
            "relevant contents of the provided documents. This process "
            "builds on the unique functionality of vector databases to "
            "perform similarity search on the embeddings of the documents' "
            "contents."
        )
        if ss.get("openai_api_key"):
            rag_agent_panel()
            if ss.get("first_document_uploaded"):
                ss.first_document_uploaded = False
                refresh()
        else:
            st.info(
                "Please enter your OpenAI API key to use the "
                "Retrieval-Augmented Generation functionality."
            )

    with genetics_tab:
        if ss.get("online"):
            st.markdown(
                f"`📎 Assistant`: Genetics annotation functionality {OFFLINE_FUNCTIONALITY}"
            )
        else:
            genetics_panel()

    with kg_tab:
        if ss.get("online"):
            st.markdown(
                f"`📎 Assistant`: Knowledge graph functionality {OFFLINE_FUNCTIONALITY}"
            )
        else:
            kg_panel()


if __name__ == "__main__":
    main()
