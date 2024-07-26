import streamlit as st
import json

ss = st.session_state

from components.kg import (
    _summarise_individual,
    _summarise,
    _plan_tasks,
    _plan_tasks_individual,
)

from components.constants import (
    SUMMARY_INSTRUCTION,
    SUMMARY_INSTRUCTION_INDIVIDUAL,
    TASKS_INSTRUCTION,
    TASKS_INSTRUCTION_INDIVIDUAL,
)

ss["summary_instruction"] = SUMMARY_INSTRUCTION
ss["summary_instruction_individual"] = SUMMARY_INSTRUCTION_INDIVIDUAL
ss["tasks_instruction"] = TASKS_INSTRUCTION
ss["tasks_instruction_individual"] = TASKS_INSTRUCTION_INDIVIDUAL
ss["individual"] = "slobentanzer"


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
                    ss.get("summary_instruction", SUMMARY_INSTRUCTION)
                )
                query_return = ss.get("summary_query_result", "")
                if query_return:
                    msg, _, _ = conv.query(json.dumps(query_return[0]))
                    ss["summary"] = msg
                else:
                    st.error(
                        "No results from query. Please check the database or query for errors."
                    )

        if ss.get("summary"):
            st.markdown("## Group summary\n\n" f'{ss.get("summary")}')

    with individual:
        summarise = st.button(
            "Summarise for individual (choose in Settings)",
            on_click=_summarise_individual(
                ss.get("individual", "slobentanzer")
            ),
            use_container_width=True,
        )
        if summarise:
            with st.spinner("Summarising ..."):
                conv = ss.get("conversation")
                conv.reset()
                conv.correct = False
                conv.append_system_message(
                    ss.get(
                        "summary_instruction_individual",
                        SUMMARY_INSTRUCTION_INDIVIDUAL,
                    )
                )
                query_return = ss.get("summary_query_result_individual", "")
                if query_return:
                    msg, _, _ = conv.query(json.dumps(query_return[0]))
                    ss["summary_individual"] = msg
                else:
                    st.error(
                        "No results from query. Please check the database or query for errors."
                    )

        if ss.get("summary_individual"):
            st.markdown(
                "## Individual summary\n\n" f'{ss.get("summary_individual")}'
            )


def tasks_panel():
    st.markdown(
        """
        ### This Week's Tasks
        
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
                    ss.get("tasks_instruction", TASKS_INSTRUCTION)
                )
                query_return = ss.get("tasks_query_result", "")
                if query_return:
                    msg, _, _ = conv.query(json.dumps(query_return[0]))
                    ss["tasks"] = msg
                else:
                    st.error(
                        "No results from query. Please check the database or query for errors."
                    )

        if ss.get("tasks"):
            st.markdown("## Group tasks\n\n" f'{ss.get("tasks")}')
    with individual:
        tasks = st.button(
            "Plan Tasks for individual (choose in Settings)",
            on_click=_plan_tasks_individual(
                ss.get("individual", "slobentanzer")
            ),
            use_container_width=True,
        )
        if tasks:
            with st.spinner("Planning ..."):
                conv = ss.get("conversation")
                conv.append_system_message(
                    ss.get(
                        "tasks_instruction_individual",
                        TASKS_INSTRUCTION_INDIVIDUAL,
                    )
                )
                query_return = ss.get("tasks_query_result_individual", "")
                if query_return:
                    msg, _, _ = conv.query(json.dumps(query_return[0]))
                    ss["tasks_individual"] = msg
                else:
                    st.error(
                        "No results from query. Please check the database or query for errors."
                    )

        if ss.get("tasks_individual"):
            st.markdown(
                "## Individual tasks\n\n" f'{ss.get("tasks_individual")}'
            )


def task_settings_panel():
    """
    Allow the user to modify the Cypher queries and the LLM instructions used
    fror the summary and tasks panels.
    """
    st.markdown(
        """
        ## Settings

        Here, you can modify the Cypher queries and the LLM instructions used
        for the summary and tasks panels.
        """
    )

    llm, neo4j, who = st.tabs(
        ["LLM Instructions", "Neo4j Queries", "Individual"]
    )

    with llm:
        st.markdown(
            """
            Here you can modify the instructions given to the LLM assistant for
            the summary and tasks panels. The instructions are used to guide the
            LLM in generating the summaries and task plans. You can use the text
            fields below to modify the instructions and see the changes in the
            summary and tasks panels.
            """
        )

        with st.expander("Summary Instructions"):
            ss["summary_instruction"] = st.text_area(
                "Group Instruction",
                ss.get("summary_instruction", ""),
                key="summary_instruction_group",
            )
            ss["summary_instruction_individual"] = st.text_area(
                "Individual Instruction",
                ss.get("summary_instruction_individual", ""),
                key="summary_instruction_individual",
            )

        with st.expander("Tasks Instructions"):
            ss["tasks_instruction"] = st.text_area(
                "Grroup Instruction",
                ss.get("tasks_instruction", ""),
                key="task_instruction_group",
            )
            ss["tasks_instruction_individual"] = st.text_area(
                "Individual Instruction",
                ss.get("tasks_instruction_individual", ""),
                key="task_instruction_individual",
            )

    with neo4j:
        st.markdown(
            """

            Here you can modify the Cypher queries used to extract the necessary
            data from the project database. The queries are used to fetch the
            data of the project components (from the [GitHub
            Project](https://github.com/orgs/biocypher/projects/6/views/1)). By
            making them more specific or detailed, you can influence the
            summaries and task plans generated by the LLM assistant. Please be
            aware that modifying these queries requires knowledge of the project
            database schema and the data stored in it; incorrect queries may
            lead to null results.

            """
        )

        with st.expander("Summary Queries"):
            ss["summary_query"] = st.text_area(
                "Group Query",
                ss.get("summary_query", ""),
                key="summary_query_group",
            )
            ss["summary_query_individual"] = st.text_area(
                "Individual Query",
                ss.get("summary_query_individual", ""),
                key="summary_query_individual",
            )

        with st.expander("Tasks Queries"):
            ss["tasks_query"] = st.text_area(
                "Group Query",
                ss.get("tasks_query", ""),
                key="tasks_query_group",
            )
            ss["tasks_query_individual"] = st.text_area(
                "Individual Query",
                ss.get("tasks_query_individual", ""),
                key="tasks_query_individual",
            )

    with who:
        st.markdown(
            """
            Here you can modify the individual for whom the summary and tasks
            are generated. By default, the individual is set to *slobentanzer*.
            In our demo project, we also have *nilskre* and *fengsh27* as team
            members.
            """
        )

        ss["individual"] = st.text_input(
            "Individual", ss.get("individual", "slobentanzer"), key="individual"
        )
