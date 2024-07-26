import neo4j_utils as nu

import streamlit as st

ss = st.session_state
import json


def _connect_to_neo4j():
    """
    Connect to the Neo4j database.
    """
    db_uri = "bolt://" + ss.get("db_ip") + ":" + ss.get("db_port")
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
    result = ss.neodriver.query(
        """
        MATCH (person:Person)-[:Leads]->(project:Project)-[:PartOf]->(iteration:Iteration)
        WHERE project.status = 'Done' OR project.status = 'In Progress'
        RETURN person.name, project.status, project.size, project.title, project.description, iteration.title
        """
    )

    ss["summary_query"] = result


def _summarise_individual(person):
    _connect_to_neo4j()
    result = ss.neodriver.query(
        f"""
        MATCH (person:Person {{name: '{person}'}})-[:Leads]->(project:Project)-[:PartOf]->(iteration:Iteration)
        WHERE project.status = 'Done' OR project.status = 'In Progress'
        RETURN person.name, project.status, project.size, project.title, project.description, iteration.title
        """
    )

    ss["summary_query_individual"] = result


def _plan_tasks():
    _connect_to_neo4j()
    result = ss.neodriver.query(
        """
        MATCH (person:Person)-[:Leads]->(project:Project)-[:PartOf]->(iteration:Iteration)
        WHERE project.status = 'Todo' OR project.status = 'In Progress'                                  
        RETURN person.name, project.status, project.size, project.title, project.description, iteration.title
        """
    )

    ss["tasks_query"] = result


def _plan_tasks_individual(person):
    _connect_to_neo4j()
    result = ss.neodriver.query(
        f"""
        MATCH (person:Person {{name: '{person}'}})-[:Leads]->(project:Project)-[:PartOf]->(iteration:Iteration)
        WHERE project.status = 'Todo' OR project.status = 'In Progress'                                  
        RETURN person.name, project.status, project.size, project.title, project.description, iteration.title
        """
    )

    ss["tasks_query_individual"] = result


def _run_neo4j_query(query):
    """
    Run cypher query against the Neo4j database.
    """
    _connect_to_neo4j()

    result = ss.neodriver.query(query)

    return result
