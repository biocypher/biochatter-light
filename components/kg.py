import json
import os

import neo4j_utils as nu
import streamlit as st

ss = st.session_state


def _connect_to_neo4j():
    """
    Connect to the Neo4j database.
    """
    _determine_neo4j_connection()
    db_uri = (
        "bolt://"
        + ss.get("db_ip", "localhost")
        + ":"
        + ss.get("db_port", "7687")
    )
    ss.neodriver = nu.Driver(
        db_name=ss.get("db_name", "neo4j"),
        db_uri=db_uri,
        db_user=ss.get("db_user", "neo4j"),
        db_passwd=ss.get("db_password", "neo4j"),
    )

    # return True if connected, False if no DB found
    if ss.get("neodriver").status == "no connection":
        return False
    else:
        _find_schema_info_node()
        return True


def _determine_neo4j_connection():
    """
    Determine the connection details for the Neo4j database.
    """
    uri = None
    if os.getenv("NEO4J_URI"):
        uri = os.getenv("NEO4J_URI")
    if ss.get("db_ip") is None:
        if uri:
            ss["db_ip"] = uri.split("//")[1].split(":")[0]
        elif os.getenv("DOCKER_COMPOSE", "false") == "true":
            ss["db_ip"] = "deploy"
        else:
            ss["db_ip"] = "localhost"
    if ss.get("db_port") is None:
        if uri:
            ss["db_port"] = uri.split(":")[2]
        else:
            ss["db_port"] = "7687"
    if ss.get("db_name") is None:
        ss["db_name"] = os.getenv("NEO4J_DBNAME") or "neo4j"

    # If the user has provided a username and password, use them
    if not ss.get("db_user") or not ss.get("db_password"):
        if os.getenv("NEO4J_USER") and os.getenv("NEO4J_PASSWORD"):
            ss["db_user"] = os.getenv("NEO4J_USER")
            ss["db_password"] = os.getenv("NEO4J_PASSWORD")


def _find_schema_info_node():
    """
    Look for a schema info node in the connected BioCypher graph and load the
    schema info if present.
    """
    result = ss.neodriver.query("MATCH (n:Schema_info) RETURN n LIMIT 1")

    if result[0]:
        schema_info_node = result[0][0]["n"]
        ss.schema_dict = json.loads(schema_info_node["schema_info"])


def _summarise():
    _connect_to_neo4j()
    if not ss.get("summary_query"):
        st.error("No summary query found.")
        return

    result = ss.neodriver.query(ss.get("summary_query"))

    ss["summary_query_result"] = result


def _summarise_individual(person):
    _connect_to_neo4j()
    if not ss.get("summary_query_individual"):
        st.error("No individual summary query found.")
        return

    result = ss.neodriver.query(
        ss.get("summary_query_individual").format(person=person)
    )

    ss["summary_query_result_individual"] = result


def _plan_tasks():
    _connect_to_neo4j()
    if not ss.get("tasks_query"):
        st.error("No tasks query found.")
        return

    result = ss.neodriver.query(ss.get("tasks_query"))

    ss["tasks_query_result"] = result


def _plan_tasks_individual(person):
    _connect_to_neo4j()
    if not ss.get("tasks_query_individual"):
        st.error("No individual tasks query found.")
        return

    result = ss.neodriver.query(
        ss.get("tasks_query_individual").format(person=person)
    )

    ss["tasks_query_result_individual"] = result


def _run_neo4j_query(query):
    """
    Run cypher query against the Neo4j database.
    """
    _connect_to_neo4j()

    result = ss.neodriver.query(query)

    return result
