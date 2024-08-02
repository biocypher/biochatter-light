# GLOBALS

DEV_FUNCTIONALITY = (
    "This functionality is not available when using the community API key, as "
    "it can involve many requests to the API."
)

OFFLINE_FUNCTIONALITY = (
    "functionality is not available in the online version of BioChatter Light. "
    "Please check the [GitHub Repository](https://github.com/biocypher/biochatter-light) "
    "for instructions on running the app locally."
)

PRIMARY_MODEL_PROMPTS = [
    "You are an assistant to a biomedical researcher.",
    "Your role is to contextualise the user's findings with biomedical "
    "background knowledge. If provided with a list, please give granular "
    "feedback about the individual entities, your knowledge about them, and "
    "what they may mean in the context of the research.",
    "You can ask the user to provide explanations and more background at any "
    "time, for instance on the treatment a patient has received, or the "
    "experimental background. But for now, wait for the user to ask a "
    "question.",
]

CORRECTING_AGENT_PROMPTS = [
    "You are a biomedical researcher.",
    "Your task is to check for factual correctness and consistency of the "
    "statements of another agent.",
    "Please correct the following message. Ignore references to previous "
    "statements, only correct the current input. If there is nothing to "
    "correct, please respond with just 'OK', and nothing else!",
]

TOOL_PROMPTS = {
    "progeny": (
        "The user has provided information in the form of a table. The rows "
        "refer to biological entities (patients, samples, cell types, or the "
        "like), and the columns refer to pathways. The values are pathway "
        "activities derived using the bioinformatics method progeny. Here are "
        "the data: {df}"
    ),
    "dorothea": (
        "The user has provided information in the form of a table. The rows "
        "refer to biological entities (patients, samples, cell types, or the "
        "like), and the columns refer to transcription factors. The values are "
        "transcription factor activities derived using the bioinformatics "
        "method dorothea. Here are the data: {df}"
    ),
    "gsea": (
        "The user has provided information in the form of a table. The first "
        "column refers to biological entities (samples, cell types, or the "
        "like), and the individual columns refer to the enrichment of "
        "individual gene sets, such as hallmarks, derived using the "
        "bioinformatics method gsea. Here are the data: {df}"
    ),
}
RAG_PROMPTS = [
    "The user has provided additional background information from scientific "
    "articles.",
    "Take the following statements into account and specifically comment on "
    "consistencies and inconsistencies with all other information available to "
    "you: {statements}",
]
SCHEMA_PROMPTS = [
    "The user has provided database access. The database contents are "
    "detailed in the following YAML config.",
    "The top-level entries in the YAML config refer to the types of "
    "entities included in the database. Entities can additionally have a "
    "`properties` attribute that informs of their attached information. Here "
    "is the config: {config}",
]

WHAT_MESSAGES = [
    "A platform for the application of Large Language Models (LLMs) in biomedical research.",
    "A way to make LLMs more __useful__ and __trustworthy__.",
    "A means to make biomedical research more reproducible.",
    "A platform for contextualisation of biomedical results.",
    "An interface for the intuitive interaction with current cutting-edge AI.",
    "An __open-source__ project.",
    "A way to make biomedical research more efficient.",
    "A time-saver.",
]

HOW_MESSAGES = [
    "Building wrappers around LLMs to tune their responses and ameliorate their shortcomings.",
    "Connecting to complementary technology, such as (vector) databases and model chaining.",
    "Being playful and experimental, and having fun!",
    "Coming together as a community and being communicative.",
    "Collaborating on the future of biomedical research.",
    "Engineering prompts to make LLMs more useful.",
    "Following open science principles.",
    "Being transparent about the limitations of the technology.",
    "Being modular and extensible.",
    "Injecting prior knowledge into LLM queries.",
]

SUMMARY_QUERY = """MATCH (person:Person)-[:Leads]->(project:Project)-[:PartOf]->(iteration:Iteration)
WHERE project.status = 'Done' OR project.status = 'In Progress'
WITH person, project, iteration
OPTIONAL MATCH (project)-[hc:HasComment]->(comment:Comment)
WITH person, project, iteration, comment.text AS commentText, hc.recency AS recency
ORDER BY recency ASC
WITH person, project, iteration, COLLECT(commentText)[..5] AS comments
RETURN person.name, 
       project.status, 
       project.size, 
       project.title, 
       project.description, 
       iteration.title, 
       REDUCE(output = '', comment in comments | output + '; ' + comment) AS concatenated_comments"""

SUMMARY_QUERY_INDIVIDUAL = """MATCH (person:Person {{name: '{person}'}})-[:Leads]->(project:Project)-[:PartOf]->(iteration:Iteration)
WHERE project.status = 'Done' OR project.status = 'In Progress'
WITH person, project, iteration
OPTIONAL MATCH (project)-[hc:HasComment]->(comment:Comment)
WITH person, project, iteration, comment.text AS commentText, hc.recency AS recency
ORDER BY recency ASC
WITH person, project, iteration, COLLECT(commentText)[..5] AS comments
RETURN person.name, 
       project.status, 
       project.size, 
       project.title, 
       project.description, 
       iteration.title, 
       REDUCE(output = '', comment in comments | output + '; ' + comment) AS concatenated_comments"""

TASKS_QUERY = """MATCH (person:Person)-[:Leads]->(project:Project)-[:PartOf]->(iteration:Iteration)
WHERE project.status = 'Todo' OR project.status = 'In Progress'                                  
WITH person, project, iteration
OPTIONAL MATCH (project)-[hc:HasComment]->(comment:Comment)
WITH person, project, iteration, comment.text AS commentText, hc.recency AS recency
ORDER BY recency ASC
WITH person, project, iteration, COLLECT(commentText)[..5] AS comments
RETURN person.name, 
       project.status, 
       project.size, 
       project.title, 
       project.description, 
       iteration.title, 
       REDUCE(output = '', comment in comments | output + '; ' + comment) AS concatenated_comments"""

TASKS_QUERY_INDIVIDUAL = """MATCH (person:Person {{name: '{person}'}})-[:Leads]->(project:Project)-[:PartOf]->(iteration:Iteration)
WHERE project.status = 'Todo' OR project.status = 'In Progress'                                  
WITH person, project, iteration
OPTIONAL MATCH (project)-[hc:HasComment]->(comment:Comment)
WITH person, project, iteration, comment.text AS commentText, hc.recency AS recency
ORDER BY recency ASC
WITH person, project, iteration, COLLECT(commentText)[..5] AS comments
RETURN person.name, 
       project.status, 
       project.size, 
       project.title, 
       project.description, 
       iteration.title, 
       REDUCE(output = '', comment in comments | output + '; ' + comment) AS concatenated_comments"""

SUMMARY_INSTRUCTION = "You will receive a collection of projects, and your task is to summarise them for the group. Explain what was done in the last project iteration at a high level, including the size of the task (XS to XL) and the participating team members. Distinguish between completed and ongoing tasks."

SUMMARY_INSTRUCTION_INDIVIDUAL = "You will receive a collection of projects led by one team member, and your task is to summarise them for the member. Explain what they did in the last project iteration at a high level, including the size of the task (XS to XL). Distinguish between completed and ongoing tasks."

TASKS_INSTRUCTION = "You will receive a collection of projects, and your task is to plan their execution in the next project phase for the group. Prioritise the tasks according to their size, priority, and assigned members, and suggest potentially useful collaborations. Prioritise projects by their priority value and focus on the current iteration. Reserve projects from the following iterations as backup suggestions. Dedicate a section in the beginning to who should talk to whom."

TASKS_INSTRUCTION_INDIVIDUAL = "You will receive a collection of tasks of an individual member of a group, and your task is to plan the next project phase for this member. Prioritise projects by their priority value and focus on the current iteration, taking size into account. Reserve projects from the following iterations as backup suggestions. Suggest potentially useful collaborations in a dedicated section in the beginning."
