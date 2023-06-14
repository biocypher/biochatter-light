# 💬🧬 ChatGSE
Gene set interpretation and more, assisted by large language models. Find the
deployed app at https://chat.biocypher.org. We are currently ***heavily***
work in progress, but we are commited to open source and very open to comments,
criticisms, and contributions! Read the [preprint
here](https://arxiv.org/abs/2305.06488)!

## 🤝 Get involved!
To stay up to date with the project, please star the repository and watch the
zulip community chat (free to join) at https://biocypher.zulipchat.com.
ChatGSE-related discussion happens in the `#chatgse` stream.

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
[here](https://github.com/biocypher/ChatGSE/discussions/11)! You can go
[here](https://github.com/biocypher/ChatGSE/discussions/20) to find inspiration
for things the model can do, such as creating formatted markdown output to
create mindmaps or other visualisations.

## 📑 Document summarisation / In-context learning
You can use the document summarisation feature to upload documents and use
similarity search to inject context into your prompts. The document
summarisation feature is currently only available on local builds of ChatGSE
(see below). It requires a connection to a vector database (currently only
[Milvus](https://milvus.io/) is supported). We follow [these
instructions](https://milvus.io/docs/install_standalone-docker.md) to mount a
Docker instance on your machine (using the standard ports). We provide a Docker
compose setup to mount the Milvus containers and the ChatGSE container together:

```
git clone https://github.com/biocypher/ChatGSE.git
cd ChatGSE
docker compose up -d
```

This command creates three containers for Milvus and one for ChatGSE. After a
short startup time, you can access the ChatGSE app at http://localhost:8501.

## Local deployment

### Devcontainer
To deploy/develop the app locally, we recommend using VS Code with the included
devcontainer setup. This requires Docker and the [Remote
Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
extension. After cloning the repository, open the folder in VS Code and click
the `Reopen in Container` button that appears in the bottom right corner (or
use the command palette to find the command). This will build a Docker image
of the app and open it in VS Code. You can then run the app by adding a
configuration similar to this one to your launch.json:

```

{
    "name": "Streamlit",
    "type": "python",
    "request": "launch",
    "program": "/usr/local/bin/streamlit",
    "console": "integratedTerminal",
    "justMyCode": true,
    "cwd": "${workspaceFolder}",
    "args": [
        "run",
        "app.py"
    ]
}

```

Note that if you want to use the document summarisation feature or other
connected services, you will still need to start these separately. For the
vector DB component of the `docker-compose.yml` file, you can do it like so:

```
docker compose up -d standalone
```

Once the other docker containers are running, they should be discoverable from
within the devcontainer. If you add your own containers, make sure that they
use the same network as your devcontainer (e.g. `milvus`).

### Docker
Using docker, run the following commands to deploy a local browser app (without
the additional containers for the vector database):

```
git clone https://github.com/biocypher/ChatGSE.git
cd ChatGSE
docker build -t chatgse .
docker run -p 8501:8501 chatgse
```

Note that the community key feature is not available locally, so you need to
provide your own API key (either in the app or as an environment variable).

#### Provide your API key
Instead of manually entering the key, you can provide it to the Docker run
command as an environment variable. With a text file (e.g. `local.env`) that
contains the keys:

```
OPENAI_API_KEY=sk-...
...
```

you can run the following command: 

```
docker run --env-file local.env -p 8501:8501 chatgse
```

### Poetry
Local installation can be performed using Poetry (or other package managers
that can work with a `pyproject.toml` file):

```
git clone https://github.com/biocypher/ChatGSE.git
cd ChatGSE
poetry install
```

For Apple Silicon machines, this must be followed by the following commands
(inside the activated environment using `poetry shell`):

```
pip uninstall grpcio
mamba install grpcio  # alternatively, conda
```

This step is necessary due to incompatibilities in the standard ARM grpcio
package. Currently, only conda-forge provides a compatible version. To avoid
this issue, you can work in a devcontainer (see above).
