# ChatGSE app.py: streamlit chat app for contextualisation of biomedical results
app_name = "chatgse"
__version__ = "0.2.17"

# BOILERPLATE
import json
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
DOCSUM_PROMPTS = [
    "The user has provided additional background information from scientific "
    "articles.",
    "Take the following statements into account and specifically comment on "
    "consistencies and inconsistencies with all other information available to "
    "you: {statements}",
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
from chatgse._interface import ChatGSE
from chatgse._stats import get_community_usage_cost
from chatgse._interface import community_possible
from chatgse._docsum import (
    DocumentSummariser,
    document_from_pdf,
    document_from_txt,
)


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
        """
    )
    if ss.get("on_streamlit"):
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
    ss.cg._history_only("📎 Assistant", "Using community key!")
    ss.user = "community"
    ss.mode = "using_community_key"
    ss.show_community_select = False
    ss.input = "done"  # just to enter main logic; more elegant solution?


def demo_mode():
    ss.openai_api_key = os.environ["OPENAI_COMMUNITY_KEY"]
    ss.cg._history_only("📎 Assistant", "Using community key!")
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
        
        The agents you will be talking to are an `📎 Assistant` (a
        pre-programmed conversational algorithm), a `💬🧬 ChatGSE` model, which
        is a pre-trained language model with instructions aimed at specifically
        improving the quality of biomedical answers, and a `️️️️️️️️️️️🕵️ Correcting agent`,
        which is a separate pre-trained language model with the task of catching
        and correcting false information conveyed by the primary model. You will
        only see the `🕵️ Correcting agent` if it detects that the `💬🧬 ChatGSE`
        model has made a mistake. In general, even though we try our best to
        avoid mistakes using the correcting agent and internal safeguards, the
        general limitations of the used Large Language Model apply: their
        statements can sometimes be incorrect or misleading, and depending on
        the complexity of the task may not yield the desired results. They are
        however very good at synthesising information from their training set,
        and thus can be useful to explain the biological context of, for
        instance, a particular gene set or cell type.

        ChatGSE is developed by [Sebastian
        Lobentanzer](https://slobentanzer.github.io); you can find the source
        code on [GitHub](https://github.com/biocypher/chatgse).

        """
    )


def download_chat_history(cg: ChatGSE):
    cg.update_json_history()
    st.download_button(
        label="Download Chat History JSON",
        data=ss.json_history,
        file_name="chat_history.json",
        mime="application/json",
        use_container_width=True,
    )


def spacer(n=2, line=False, next_n=0):
    for _ in range(n):
        st.write("")
    if line:
        st.tabs([" "])
    for _ in range(next_n):
        st.write("")


def show_primary_model_prompts():
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


def show_docsum_prompts():
    st.markdown(
        "`📎 Assistant`: Here you can edit the prompts used to set up the "
        "Document Summarisation task. Text passages from any uploaded "
        "documents will be passed on to the primary model using these prompts. "
        "The placeholder `{statments}` will be replaced by the text passages. "
        "Upload documents and edit vector database settings in the "
        "`Document Summarisation` tab."
    )

    for num, msg in enumerate(ss.prompts["docsum_prompts"]):
        field, button = st.columns([4, 1])
        with field:
            ss.prompts["docsum_prompts"][num] = st.text_area(
                label=str(num + 1),
                value=msg,
                label_visibility="collapsed",
                placeholder="Enter your prompt here.",
            )
        with button:
            st.button(
                f"Remove prompt {num + 1}",
                on_click=remove_prompt,
                args=(ss.prompts["docsum_prompts"], num),
                key=f"remove_prompt_{num}",
                use_container_width=True,
            )


def show_tool_prompts():
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
    prompt_list.append("")


def remove_prompt(prompt_list, num):
    del prompt_list[num]


def add_tool_prompt():
    ss.prompts["tool_prompts"][""] = ""


def remove_tool_prompt(nam):
    ss.prompts["tool_prompts"].pop(nam)


def prompt_save_load_reset():
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
    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d_%H-%M-%S")
    st.download_button(
        "Save Full Prompt Set (JSON)",
        data=save_prompt_set(),
        use_container_width=True,
        file_name=f"ChatGSE_prompt_set-{date}.json",
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
        "This app is still in development; you are seeing a preview with "
        "limited functionality. For more information on our vision of the "
        "platform, please see [our preprint](https://arxiv.org/abs/2305.06488)! "
        "If you'd like to contribute to the project, please find us on "
        "[GitHub](https://github.com/biocypher/ChatGSE) or "
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


def docsum_panel():
    """
    Upload files for document summarisation, one file at a time. Upon upload,
    document is split and embedded into a connected vector DB using the
    `_docsum.py` module. The top k results of similarity search of the user's
    query will be injected into the prompt to the primary model (only once per
    query). The panel displays a file_uploader panel, settings for the text
    splitter (chunk size and overlap, separators), and a slider for the number
    of results to return. Also displays the list of closest matches to the last
    executed query.
    """

    uploader, settings = st.columns(2)

    with uploader:
        st.markdown(
            "### "
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "📄 Upload Document"
        )
        st.info(
            "Upload documents one at a time. Upon upload, the document is "
            "split according to the settings and the embeddings are stored in "
            "the connected vector database."
        )
        uploaded_file = st.file_uploader(
            "Upload a document for summarisation",
            type=["txt", "pdf"],
            label_visibility="collapsed",
        )
        if uploaded_file:
            with st.spinner("Saving embeddings..."):
                if not ss.get("docsum"):
                    ss.docsum = DocumentSummariser()
                val = uploaded_file.getvalue()
                if uploaded_file.type == "application/pdf":
                    doc = document_from_pdf(val)
                elif uploaded_file.type == "text/plain":
                    doc = document_from_txt(val)
                ss.docsum.set_document(doc)
                ss.docsum.split_document()
                ss.docsum.store_embeddings()
                st.success("Embeddings saved!")

    with settings:
        if not ss.get("docsum"):
            ss.docsum = DocumentSummariser()

        st.markdown(
            "### "
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "🔧 Settings"
        )

        # checkbox for whether to use the docsum prompt
        st.checkbox(
            "Use document summarisation prompt",
            value=ss.docsum.use_prompt,
        )

        st.slider(
            "Chunk size",
            min_value=100,
            max_value=5000,
            value=ss.docsum.chunk_size,
            step=1,
        )
        st.slider(
            "Overlap",
            min_value=0,
            max_value=1000,
            value=ss.docsum.chunk_overlap,
            step=1,
        )
        st.multiselect(
            "Separators (defaults: new line, comma, space)",
            options=ss.docsum.separators,
            default=ss.docsum.separators,
        )
        st.slider(
            "Number of results to use in the prompt",
            min_value=1,
            max_value=20,
            value=ss.docsum.n_results,
            step=1,
        )


def main():
    # NEW SESSION
    if not ss.get("mode"):
        ss.user = "default"
        ss.prompts = {
            "primary_model_prompts": PRIMARY_MODEL_PROMPTS,
            "correcting_agent_prompts": CORRECTING_AGENT_PROMPTS,
            "tool_prompts": TOOL_PROMPTS,
            "docsum_prompts": DOCSUM_PROMPTS,
        }

        # CHECK ENVIRONMENT
        if os.getenv("ON_STREAMLIT"):
            ss.on_streamlit = True
            ss.online = True
        elif os.getenv("ON_SELFHOSTED"):
            ss.on_selfhosted = True
            ss.online = True
        else:
            ss.online = False

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
        prompts_tab,
        docsum_tab,
        annot_tab,
        exp_design_tab,
        correct_tab,
    ) = st.tabs(
        [
            "Gene Sets and Pathways",
            "Prompt Engineering",
            "Document Summarisation",
            "Cell Type Annotation",
            "Experimental Design",
            "Correcting Agent",
        ]
    )

    with chat_tab:
        # WELCOME MESSAGE AND CHAT HISTORY
        st.markdown(
            "Welcome to ``ChatGSE``! "
            ":violet[If you are on a small screen, you may need to "
            "shift-scroll to the right to see all tabs. -->]"
        )

        if ss.mode == "getting_key":
            show_about_section()
            cg._display_setup()

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
            download_chat_history(cg)
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
                f"`📎 Assistant`: Cell type annotation {OFFLINE_FUNCTIONALITY}"
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
                    "Document Summarisation",
                ),
            )

            if ss.prompts_box == "Primary Model":
                show_primary_model_prompts()

            elif ss.prompts_box == "Correcting Agent":
                show_correcting_agent_prompts()

            elif ss.prompts_box == "Tools":
                show_tool_prompts()

            elif ss.prompts_box == "Document Summarisation":
                show_docsum_prompts()

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
            f"`📎 Assistant`: Correction agent functionality {OFFLINE_FUNCTIONALITY}"
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
            if ss.online:
                st.markdown(
                    f"`📎 Assistant`: Document summarisation functionality {OFFLINE_FUNCTIONALITY}"
                )
            else:
                docsum_panel()


if __name__ == "__main__":
    main()
