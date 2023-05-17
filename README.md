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
The document summarisation feature is currently only available on local builds
of ChatGSE (see below). It requires a connection to a vector database
(currently only [Milvus](https://milvus.io/) is supported). Please follow [these
instructions](https://milvus.io/docs/install_standalone-docker.md) to mount a
Docker instance on your machine (using standard ports). Then, you can run the
ChatGSE app as described below, using the document summarisation feature to
upload documents and use similarity search to inject context into your prompts.


## Local deployment

### Docker
Using docker, run the following commands to deploy a local browser app:

```
git clone https://github.com/biocypher/ChatGSE.git
cd ChatGSE
docker build -t chatgse .
docker run -p 8501:8501 chatgse
```

Note that the community key feature is not available locally, so you need to
provide your own API key (either in the app or as an environment variable).

### Poetry
Using poetry, run the following commands to deploy a local browser app:

```
git clone https://github.com/biocypher/ChatGSE.git
cd ChatGSE
poetry install
poetry run streamlit run app.py
```
