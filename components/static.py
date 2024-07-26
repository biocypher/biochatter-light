import streamlit as st

ss = st.session_state

__version__ = "0.6.1"


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
