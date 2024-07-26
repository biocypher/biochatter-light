import streamlit as st

ss = st.session_state
import json
import datetime


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
