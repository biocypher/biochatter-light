import neo4j_utils as nu

import streamlit as st

ss = st.session_state
import json

import os

from components.constants import (
    SUMMARY_QUERY,
    SUMMARY_QUERY_INDIVIDUAL,
    TASKS_QUERY,
    TASKS_QUERY_INDIVIDUAL,
)

ss["summary_query"] = SUMMARY_QUERY
ss["summary_query_individual"] = SUMMARY_QUERY_INDIVIDUAL
ss["tasks_query"] = TASKS_QUERY
ss["tasks_query_individual"] = TASKS_QUERY_INDIVIDUAL


def _connect_to_neo4j():
    """
    Connect to the Neo4j database.
    """
    _determine_neo4j_connection()
    db_uri = "bolt://" + ss.get("db_ip", "localhost") + ":" + ss.get("db_port")
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


def _determine_neo4j_connection():
    """
    Determine the connection details for the Neo4j database.
    """
    if ss.get("db_ip") is None:
        if os.getenv("DOCKER_COMPOSE", "false") == "true":
            ss["db_ip"] = "deploy"
        else:
            ss["db_ip"] = "localhost"
    if ss.get("db_port") is None:
        ss["db_port"] = "7687"
    if ss.get("db_name") is None:
        ss["db_name"] = "neo4j"


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


def _summarise():
    _connect_to_neo4j()
    result = ss.neodriver.query(ss.get("summary_query", SUMMARY_QUERY))

    ss["summary_query_result"] = result


def _summarise_individual(person):
    _connect_to_neo4j()
    result = ss.neodriver.query(
        ss.get("summary_query_individual", SUMMARY_QUERY_INDIVIDUAL).format(
            person=person
        )
    )

    ss["summary_query_result_individual"] = result


def _plan_tasks():
    _connect_to_neo4j()
    result = ss.neodriver.query(ss.get("tasks_query", TASKS_QUERY))

    ss["tasks_query_result"] = result


def _plan_tasks_individual(person):
    _connect_to_neo4j()
    result = ss.neodriver.query(
        ss.get("tasks_query_individual", TASKS_QUERY_INDIVIDUAL).format(
            person=person
        )
    )

    ss["tasks_query_result_individual"] = result


def _run_neo4j_query(query):
    """
    Run cypher query against the Neo4j database.
    """
    _connect_to_neo4j()

    result = ss.neodriver.query(query)

    return result
