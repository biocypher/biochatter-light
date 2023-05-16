import os

print(os.getcwd())
from chatgse._docsum import DocumentSummariser, Document


def test_document_summariser():
    # runs long, requires API key and local milvus server
    # uses ada-002 for embeddings
    docsum = DocumentSummariser()
    text_path = "test/bc_summary.pdf"
    # load document as file

    documents = docsum.split_document(text_path)
    assert isinstance(documents, list)
    assert isinstance(documents[0], Document)

    docsum.store_embeddings(documents)
    assert docsum.vector_db is not None

    query = "What is BioCypher?"
    results = docsum.similarity_search(query)
    assert len(results) == 3
    assert all(["BioCypher" in result.page_content for result in results])


def test_load_txt():
    docsum = DocumentSummariser()
    text_path = "test/bc_summary.txt"
    document = docsum._load_document(text_path)
    assert isinstance(document, list)
    assert isinstance(document[0], Document)


def test_load_pdf():
    docsum = DocumentSummariser()
    pdf_path = "test/bc_summary.pdf"
    document = docsum._load_document(pdf_path)
    assert isinstance(document, list)
    assert isinstance(document[0], Document)
