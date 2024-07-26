from biochatter.vectorstore import (
    DocumentEmbedder,
    DocumentReader,
)
from biochatter.rag_agent import RagAgent
from biochatter.prompts import BioCypherPromptEngine
from pymilvus.exceptions import MilvusException
from langchain.embeddings import OpenAIEmbeddings
import streamlit as st
import yaml
import json

ss = st.session_state
import os

from .handlers import (
    _get_gene_data,
    toggle_rag_agent_prompt,
    toggle_split_by_characters,
    _regenerate_query,
    _rerun_query,
)

from .kg import (
    _summarise_individual,
    _summarise,
    _plan_tasks,
    _plan_tasks_individual,
    _run_neo4j_query,
    _connect_to_neo4j,
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
        if os.getenv("DOCKER_COMPOSE", "false") == "true":
            host = "deploy"
        else:
            host = "localhost"
        with ip:
            st.text_input("Database IP address:", value=host, key="db_ip")
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
                "Please upload a schema configuration or info file to continue "
                "or provide a graph with a schema info node."
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


def summary_panel():
    st.markdown(
        """
        ### Last Week's Summary

        Here, we provide a summary of last week's activities from the project
        database. The database is built from the [GitHub
        Project](https://github.com/orgs/biocypher/projects/6/views/1) as a
        BioCypher knowledge graph and serves as a demonstration of the flexible
        BioChatter workflow. This BioChatter Light application is a stand-in for
        demonstration purposes, since the workflow presented here would ideally
        be integrated into a messaging platform such as Zulip or Slack via a web
        hook / bot. For instance, this summary would be generated for the entire
        group, but also for each individual project group and member, and sent
        to the appropriate channels automatically.

        Together with the recommendations generated for the next week (see
        second tab), this provides a demonstration of a project management
        system that has fair and sustainable data collection via a BioCypher
        KG built from a GitHub project, and a conversational AI that can
        summarise and recommend actions based on the live data.

        Further, the system can be used to modify the project via the respective
        API calls, e.g., to add tasks, or move tasks between status columns. For
        the demonstration purposes of this use case, this functionality is not
        implemented.
        
        """
    )
    # create two buttons spanning the entire screen
    group, individual = st.columns(2)
    with group:
        summarise = st.button(
            "Summarise for the Group",
            on_click=_summarise,
            use_container_width=True,
        )
        if summarise:
            with st.spinner("Summarising ..."):
                conv = ss.get("conversation")
                conv.reset()
                conv.correct = False
                conv.append_system_message(
                    "You will receive a collection of projects, and your task is to "
                    "summarise them for the group. Explain what was done in the last "
                    "project iteration at a high level, including the size of the "
                    "task (XS to XL) and the participating team members. Distinguish "
                    "between completed and ongoing tasks."
                )
                query_return = ss.get("summary_query", "")
                if query_return:
                    msg, _, _ = conv.query(json.dumps(query_return[0]))
                    ss["summary"] = msg

        if ss.get("summary"):
            st.markdown("## Group summary\n\n" f'{ss.get("summary")}')

    with individual:
        summarise = st.button(
            "Summarise for *slobentanzer*",
            on_click=_summarise_individual("slobentanzer"),
            use_container_width=True,
        )
        if summarise:
            with st.spinner("Summarising ..."):
                conv = ss.get("conversation")
                conv.reset()
                conv.correct = False
                conv.append_system_message(
                    "You will receive a collection of projects led by one team "
                    "member, and your task is to summarise them for the group. "
                    "Explain what was done in the last project iteration at a high "
                    "level, including the size of the task (XS to XL). Distinguish "
                    "between completed and ongoing tasks."
                )
                query_return = ss.get("summary_query_individual", "")
                if query_return:
                    msg, _, _ = conv.query(json.dumps(query_return[0]))
                    ss["summary_individual"] = msg

        if ss.get("summary_individual"):
            st.markdown(
                "## Individual summary\n\n" f'{ss.get("summary_individual")}'
            )


def tasks_panel():
    st.markdown(
        """
        
        In this panel, we give a demonstration of the task management system to
        plan tasks for the next project iteration. The tasks are taken from the
        project database, which is built from the [GitHub
        Project](https://github.com/orgs/biocypher/projects/6/views/1), as
        described in the summary panel. The open tasks are summarised and
        interpreted by the LLM assistant, providing a prioritisation and
        recommendation for the next steps, including collaborations that should
        be considered in the coming iteration.

        As with the summary panel, this system would ideally be integrated into
        a messaging platform such as Zulip or Slack via a web hook / bot; and
        the bot would ideally have write access to the GitHub Project to modify
        the individual tasks based on priorities and feedback from the team
        members.

        """
    )

    # create two buttons spanning the entire screen
    group, individual = st.columns(2)
    with group:
        tasks = st.button(
            "Plan Tasks for the Group",
            on_click=_plan_tasks,
            use_container_width=True,
        )
        if tasks:
            with st.spinner("Planning ..."):
                conv = ss.get("conversation")
                conv.append_system_message(
                    "You will receive a collection of tasks, and your task is "
                    "to plan them for the group. Prioritise the tasks "
                    "according to their size, priority, and assigned members, "
                    "and suggest potentially useful collaborations. Dedicate a "
                    "section in the beginning to who should talk to whom."
                )
                query_return = ss.get("tasks_query", "")
                if query_return:
                    msg, _, _ = conv.query(json.dumps(query_return[0]))
                    ss["tasks"] = msg

        if ss.get("tasks"):
            st.markdown("## Group tasks\n\n" f'{ss.get("tasks")}')
    with individual:
        tasks = st.button(
            "Plan Tasks for *slobentanzer*",
            on_click=_plan_tasks_individual("slobentanzer"),
            use_container_width=True,
        )
        if tasks:
            with st.spinner("Planning ..."):
                conv = ss.get("conversation")
                conv.append_system_message(
                    "You will receive a collection of tasks of an individual "
                    "member of a group, and your task is to plan the next project "
                    "phase. Prioritise the tasks according to their size / "
                    "priority, and suggest potentially useful collaborations."
                )
                query_return = ss.get("tasks_query_individual", "")
                if query_return:
                    msg, _, _ = conv.query(json.dumps(query_return[0]))
                    ss["tasks_individual"] = msg

        if ss.get("tasks_individual"):
            st.markdown(
                "## Individual tasks\n\n" f'{ss.get("tasks_individual")}'
            )
