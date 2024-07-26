from biochatter.vectorstore import (
    DocumentEmbedder,
    DocumentReader,
)
from biochatter.rag_agent import RagAgent
from pymilvus.exceptions import MilvusException
from langchain.embeddings import OpenAIEmbeddings
import streamlit as st

ss = st.session_state
import os

from components.handlers import (
    toggle_rag_agent_prompt,
    toggle_split_by_characters,
)


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
        if os.getenv("DOCKER_COMPOSE", "false") == "true":
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
