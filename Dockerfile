FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y curl && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false && \
    poetry install --no-dev -E neo4j

COPY . .

EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501"]