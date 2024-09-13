import streamlit as st

ss = st.session_state

import os

from biochatter_light._interface import BioChatterLight
from biochatter_light._interface import community_possible
from biochatter.llm_connect import (
    OPENAI_MODELS,
    HUGGINGFACE_MODELS,
    XINFERENCE_MODELS,
)

from .config import TABS_TO_SHOW
from components.constants import (
    DEV_FUNCTIONALITY,
    OFFLINE_FUNCTIONALITY,
    PRIMARY_MODEL_PROMPTS,
    CORRECTING_AGENT_PROMPTS,
    TOOL_PROMPTS,
    RAG_PROMPTS,
    SCHEMA_PROMPTS,
)

from .handlers import (
    refresh,
    autofocus_line,
    autofocus_area,
    update_api_keys,
)

from .static import (
    app_header,
    app_info,
)

from .buttons import (
    reset_button,
    mode_select,
    data_input_buttons,
    demo_next_button,
    download_chat_history,
    download_complete_history,
    community_select,
)

from .display import (
    remaining_tokens,
    display_token_usage,
    show_about_section,
    waiting_for_rag_agent,
)

from .input import (
    openai_key_chat_box,
    huggingface_key_chat_box,
    file_uploader,
    chat_line,
    chat_box,
)

from .dropdown import model_select

from .panels import (
    rag_agent_panel,
    correcting_agent_panel,
    genetics_panel,
    kg_panel,
    summary_panel,
    tasks_panel,
    task_settings_panel,
)

from .prompts import (
    prompt_save_button,
    prompt_save_load_reset,
    show_primary_model_prompts,
    show_correcting_agent_prompts,
    show_tool_prompts,
    show_rag_agent_prompts,
)


def main_logic():
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
    tabs_to_show = [tab for tab, show in TABS_TO_SHOW.items() if show]
    tabs = st.tabs(tabs_to_show)
    tab_dict = dict(zip(tabs_to_show, tabs))

    if "Chat" in tabs_to_show:
        with tab_dict["Chat"]:
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
                if not os.getenv("OLLAMA_MODEL") and not os.getenv(
                    "XINFERENCE_MODEL"
                ):
                    model_select()

            # CHAT BOX

            if ss.mode == "getting_key":
                if ss.primary_model in OPENAI_MODELS:
                    openai_key_chat_box()
                elif ss.primary_model in HUGGINGFACE_MODELS:
                    huggingface_key_chat_box()
                elif os.getenv("OLLAMA_MODEL") or os.getenv("XINFERENCE_MODEL"):
                    bcl._ask_for_user_name()
                    ss.mode = "getting_name"
                    refresh()
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

    if "Retrieval-Augmented Generation" in tabs_to_show:
        with tab_dict["Retrieval-Augmented Generation"]:
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

    if "Cell Type Annotation" in tabs_to_show:
        with tab_dict["Cell Type Annotation"]:
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

    if "Experimental Design" in tabs_to_show:
        with tab_dict["Experimental Design"]:
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
                f"`📎 Assistant`: Experimental design {OFFLINE_FUNCTIONALITY}"
            )

    if "Prompt Engineering" in tabs_to_show:
        with tab_dict["Prompt Engineering"]:
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

    if "Correcting Agent" in tabs_to_show:
        with tab_dict["Correcting Agent"]:
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
            correcting_agent_panel()

    if "Genetics Annotation" in tabs_to_show:
        with tab_dict["Genetics Annotation"]:
            if ss.get("online"):
                st.markdown(
                    f"`📎 Assistant`: Genetics annotation {OFFLINE_FUNCTIONALITY}"
                )
            else:
                genetics_panel()

    if "Knowledge Graph" in tabs_to_show:
        with tab_dict["Knowledge Graph"]:
            if ss.get("online"):
                st.markdown(
                    f"`📎 Assistant`: Knowledge graph {OFFLINE_FUNCTIONALITY}"
                )
            else:
                kg_panel()

    if "Last Week's Summary" in tabs_to_show:
        with tab_dict["Last Week's Summary"]:
            summary_panel()

    if "This Week's Tasks" in tabs_to_show:
        with tab_dict["This Week's Tasks"]:
            tasks_panel()

    if "Task Settings" in tabs_to_show:
        with tab_dict["Task Settings"]:
            task_settings_panel()


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
    if not os.getenv("XINFERENCE_MODEL") and not os.getenv("OLLAMA_MODEL"):
        ss.correct = True
    else:
        ss.correct = False
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
