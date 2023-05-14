# ChatGSE document summarisation functionality
# split text
# connect to vector db
# do similarity search
# return x closes matches for in-context learning

from typing import List, Optional
import streamlit as st

ss = st.session_state

from langchain.schema import Document
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader
from langchain.vectorstores import Milvus


class DocumentSummariser:
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 0,
        separators: Optional[list] = None,
        model: Optional[str] = None,
        vector_db_vendor: Optional[str] = None,
        connection_args: Optional[dict] = None,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or [" ", ",", "\n"]

        # TODO: variable embeddings depending on model
        # for now, just use ada-002
        self.embeddings = OpenAIEmbeddings()

        # TODO: vector db selection
        self.vector_db_vendor = vector_db_vendor or "milvus"
        self.vector_db = None

        # connection arguments
        self.connection_args = connection_args or {
            "host": "127.0.0.1",
            "port": "19530",
        }

    def set_chunk_siue(self, chunk_size: int) -> None:
        self.chunk_size = chunk_size

    def set_chunk_overlap(self, chunk_overlap: int) -> None:
        self.chunk_overlap = chunk_overlap

    def set_separators(self, separators: list) -> None:
        self.separators = separators

    def _load_document(self, path: str) -> List[Document]:
        loader = TextLoader(path)
        return loader.load()

    def split_document(self, path: str) -> List[Document]:
        document = self._load_document(path)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
        )
        return text_splitter.split_documents(document)

    def store_embeddings(self, documents: List[Document]) -> None:
        if self.vector_db_vendor == "milvus":
            self.vector_db = Milvus.from_documents(
                documents=documents,
                embedding=self.embeddings,
                connection_args=self.connection_args,
            )
        else:
            raise NotImplementedError(self.vector_db_vendor)

    def similarity_search(self, query: str, k: int = 3):
        """
        Returns top n closest matches to query from vector store.

        Args:
            query (str): query string

            k (int, optional): number of closest matches to return. Defaults to
            3.

        """
        if self.vector_db_vendor == "milvus":
            return self.vector_db.similarity_search(query=query, k=k)
        else:
            raise NotImplementedError(self.vector_db_vendor)
