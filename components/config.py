# CONFIGURATION

import os


TABS_TO_SHOW = {
    "Chat": os.getenv("CHAT_TAB", "true") == "true",
    "Prompt Engineering": os.getenv("PROMPT_ENGINEERING_TAB", "true") == "true",
    "Retrieval-Augmented Generation": os.getenv("RAG_TAB", "true") == "true",
    "Correcting Agent": os.getenv("CORRECTING_AGENT_TAB", "true") == "true",
    "Cell Type Annotation": os.getenv("CELL_TYPE_ANNOTATION_TAB", "false")
    == "true",
    "Experimental Design": os.getenv("EXPERIMENTAL_DESIGN_TAB", "false")
    == "true",
    "Genetics Annotation": os.getenv("GENETICS_ANNOTATION_TAB", "false")
    == "true",
    "Knowledge Graph": os.getenv("KNOWLEDGE_GRAPH_TAB", "false") == "true",
    "Last Week's Summary": os.getenv("LAST_WEEKS_SUMMARY_TAB", "false")
    == "true",
    "This Week's Tasks": os.getenv("THIS_WEEKS_TASKS_TAB", "false") == "true",
}
