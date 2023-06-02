# 💬🧬 ChatGSE
Gene set interpretation and more, assisted by large language models. Find the
deployed app at https://chatgse.streamlit.app. We are currently ***heavily***
work in progress, but we are commited to open source and very open to comments,
criticisms, and contributions! Read the [preprint
here](https://arxiv.org/abs/2305.06488)!

## 🤝 Get involved!
We are very happy about contributions from the community, large and small!
If you would like to contribute to the platform's development, please refer to
our [contribution guidelines](CONTRIBUTING.md). :)

Importantly, you don't need to be an expert on any of the technical aspects of
the project! As long as you are interested and would like to help make this
platform a great open-source tool, you're good. 🙂

If you want to ask informal questions, talk about dev things, or just chat,
please join our community at https://biocypher.zulipchat.com!

> **Imposter syndrome disclaimer:** We want your help. No, really. There may be a little voice inside your head that is telling you that you're not ready, that you aren't skilled enough to contribute. We assure you that the little voice in your head is wrong. Most importantly, there are many valuable ways to contribute besides writing code.
>
> This disclaimer was adapted from the [Pooch](https://github.com/fatiando/pooch) project.

## 🛠 Prompt engineering discussions
You can discuss your favourite prompt setups and share the corresponding JSON
files in the discussion
[here](https://github.com/biocypher/ChatGSE/discussions/11)!

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

### Mamba
Local installation can be performed using Mamba (recommended) or Conda:

```
git clone https://github.com/biocypher/ChatGSE.git
cd ChatGSE
mamba env create -f environment.yml
conda activate chatgse
pip install -r requirements.txt
```

For Apple Silicon machines, this must be followed by the following commands:

```
pip uninstall grpcio
mamba install grpcio
```

