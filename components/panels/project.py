import streamlit as st
import json

ss = st.session_state

from components.kg import (
    _summarise_individual,
    _summarise,
    _plan_tasks,
    _plan_tasks_individual,
)


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
