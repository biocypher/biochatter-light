# 💬🧬 BioChatter Light

This app demonstrates workflows in biomedical research and application, assisted
by large language models. Find the deployed app at https://light.biochatter.org.
This app is a development platform and framework demonstration, not a commercial
service. We are commited to open source and very open to comments, criticisms,
and contributions! Read the preprint [here](https://arxiv.org/abs/2305.06488)!

This repository contains only the frontend code of our streamlit app. The code
base used for communication with the LLMs, vector databases, and other
components of our project is developed at 
https://github.com/biocypher/biochatter. Check there if you have your own UI and
are looking for a way to connect it to the world of LLMs! If you are looking for
a full-featured client-server web application, check out [BioChatter
Next](https://next.biochatter.org), developed at
https://github.com/biocypher/biochatter-server and
https://github.com/biocypher/biochatter-next.

## 🚀 Quick start

If you want to build your own version of the app, you can modify all components
of the workflow by cloning this repository and running the app locally. You can
also deploy the app on your own server or cloud service. The app is built using
[Streamlit](https://streamlit.io/), a Python library for creating web
applications from Python scripts.

### Tab selection

You can use environment variables to select the tabs to display; these can also
be defined in the `docker-compose.yml` file. The following environment variables
are available:

- Basic tabs
    - `CHAT_TAB`: Show the chat tab.
    - `PROMPT_ENGINEERING_TAB`: Show the prompt engineering tab.
    - `CORRECTING_AGENT_TAB`: Show the correcting agent tab.
- Retrieval-augmented generation
    - `RAG_TAB`: Show the retrieval-augmented generation tab.
    - `KNOWLEDGE_GRAPH_TAB`: Show the knowledge graph tab.
- Special use cases
    - `CELL_TYPE_ANNOTATION_TAB`: Show the cell type annotation tab.
    - `EXPERIMENTAL_DESIGN_TAB`: Show the experimental design tab.
    - `GENETICS_ANNOTATION_TAB`: Show the genetics annotation tab.
    - `LAST_WEEKS_SUMMARY_TAB`: Show the last week's summary tab (project management).
    - `THIS_WEEKS_TASKS_TAB`: Show this week's tasks tab (project management).
    - `TASK_SETTINGS_PANEL_TAB`: Show the task settings panel tab (project management).  

Simply set these to `true` to show the corresponding tab. We also have the
`DOCKER_COMPOSE` environment variable, which we use to signal to the app that it
is running inside a Docker container; you won't need to set this manually.

## Neo4j connectivity and authentication

If you want to connect a Neo4j knowledge graph to the BioChatter app, you can
set some environment variables to configure the connection. The following
variables are available:

- `NEO4J_URI`: The URI of the Neo4j database, e.g., `bolt://localhost:7687`.
- `NEO4J_USER`: The username for the Neo4j database, e.g., `neo4j`.
- `NEO4J_PASSWORD`: The password for the Neo4j database, e.g., `password`.
- `NEO4J_DBNAME`: The name of the Neo4j database to connect to, e.g., `neo4j`.

The knowledge graph tab allows the specification of URI (hostname and port), the
username and password in the UI. The database name is set to `neo4j` by default,
if you have a different one, please set the environment variable.

## 🤝 Get involved!

To stay up to date with the project, please star the repository and watch the
zulip community chat (free to join) at https://biocypher.zulipchat.com.
Related discussion happens in the `#biochatter` stream.

We are very happy about contributions from the community, large and small!
If you would like to contribute to the platform's development, please refer to
our [contribution guidelines](CONTRIBUTING.md). :)

Importantly, you don't need to be an expert on any of the technical aspects of
the project! As long as you are interested and would like to help make this
platform a great open-source tool, you're good. 🙂

> **Imposter syndrome disclaimer:** We want your help. No, really. There may be a little voice inside your head that is telling you that you're not ready, that you aren't skilled enough to contribute. We assure you that the little voice in your head is wrong. Most importantly, there are many valuable ways to contribute besides writing code.
>
> This disclaimer was adapted from the [Pooch](https://github.com/fatiando/pooch) project.

## 🛠 Prompt engineering discussions

You can discuss your favourite prompt setups and share the corresponding JSON
files in the discussion
[here](https://github.com/biocypher/biochatter-light/discussions/11)! You can go
[here](https://github.com/biocypher/biochatter-light/discussions/20) to find
inspiration for things the model can do, such as creating formatted markdown
output to create mindmaps or other visualisations.

## 📑 Retrieval-Augmented Generation / In-context learning

You can use the Retrieval-Augmented Generation (RAG) feature to upload documents
and use similarity search to inject context into your prompts. The RAG feature
is currently only available on local builds of BioChatter Light (see below). It requires
a connection to a vector database (currently only [Milvus](https://milvus.io/)
is supported). We follow [these
instructions](https://milvus.io/docs/install_standalone-docker.md) to mount a
Docker instance on your machine (using the standard ports). We provide a Docker
compose setup to mount the Milvus containers and the BioChatter Light container together:

```
git clone https://github.com/biocypher/biochatter-light.git
cd biochatter-light
docker compose up -d
```

This command creates three containers for Milvus and one for BioChatter Light. After a
short startup time, you can access the BioChatter Light app at http://localhost:8501.

## Local deployment

### Docker

The simplest way to deply BioChatter Light on your machine is using the Docker image we
provide on Docker Hub. You can run it using the following command:

```
docker run -p 8501:8501 biocypher/biochatter-light
```

You can also build the image yourself from this repository (without the
additional containers for the vector database):

```
git clone https://github.com/biocypher/biochatter-light.git
cd biochatter-light
docker build -t biochatter-light .
docker run -p 8501:8501 biochatter-light
```

Note that the community key feature is not available locally, so you need to
provide your own API key (either in the app or as an environment variable).

#### Local LLMs using Xorbits Inference

Note that connection to locally deployed models via the Xinference API is not
supported in the Docker image (because the optional "xinference" dependencies of
BioChatter are not installed due to their large size). If you want to use this
feature, you can build the image yourself including these dependencies, by
setting

```
biochatter = {version = "0.4.7", extras = ["xinference"]}
```

in the `pyproject.toml` file. You can then build the image as described above,
or install and run the app locally using Poetry (see below).

#### Provide your API key

Instead of manually entering the key, you can provide it to the Docker run
command as an environment variable. You can designate the variable in your
environment directly (`export OPENAI_API_KEY=sk-...`), or start the container
with a text file (e.g. `local.env`) that contains the keys:

```
OPENAI_API_KEY=sk-...
...
```

you can run the following command: 

```
docker run --env-file local.env -p 8501:8501 biochatter-light
```

### Poetry

Local installation can be performed using Poetry (or other package managers
that can work with a `pyproject.toml` file):

```
git clone https://github.com/biocypher/biochatter-light.git
cd biochatter-light
poetry install
```

#### Mac OS and Apple Silicon

For Apple Silicon machines, this must be followed by the following commands
(inside the activated environment using `poetry shell`):

```
pip uninstall grpcio
mamba install grpcio  # alternatively, conda
```

This step is necessary due to incompatibilities in the standard ARM grpcio
package. Currently, only conda-forge provides a compatible version. To avoid
this issue, you can work in a devcontainer (see above).
