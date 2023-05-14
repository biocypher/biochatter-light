import os

print(os.getcwd())
from chatgse._docsum import DocumentSummariser, Document


def test_document_summariser():
    # runs long, requires API key and local milvus server
    docsum = DocumentSummariser()
    text_path = "test/bc_summary.txt"
    documents = docsum.split_document(text_path)
    assert isinstance(documents, list)
    assert isinstance(documents[0], Document)

    docsum.store_embeddings(documents)
    assert docsum.vector_db is not None

    query = "What is BioCypher?"
    results = docsum.similarity_search(query)
    assert len(results) == 3
    assert all(["BioCypher" in result.page_content for result in results])
