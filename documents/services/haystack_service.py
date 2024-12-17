import logging
from documents.models import Document
from haystack.document_stores import InMemoryDocumentStore
from haystack.nodes import EmbeddingRetriever, FARMReader
from haystack.pipelines import ExtractiveQAPipeline
from haystack.nodes import BM25Retriever

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize the Document Store with BM25 enabled
document_store = InMemoryDocumentStore(use_bm25=True, embedding_dim=384)
logging.debug(f"BM25 Enabled: {document_store.use_bm25}")

# Initialize the retriever and reader
retriever = BM25Retriever(document_store=document_store)


reader = FARMReader(model_name_or_path="deepset/roberta-base-squad2")

# Step 1: Index documents from the database
def index_documents_from_db():
    # Retrieve all documents from the database
    documents = Document.objects.all()
    logging.info(f"Retrieved {len(documents)} documents from the database.")

    # Convert documents to the format Haystack expects
    indexed_documents = [
        {
            'content': doc.content,
            'meta': {'document_name': doc.title, 'status': doc.status},
        }
        for doc in documents
    ]
    logging.info(f"Indexed {len(indexed_documents)} documents.")

    # Clear existing index and reindex
    document_store.delete_documents()
    document_store.write_documents(indexed_documents)

    # Log the indexed documents in the store
    all_docs = document_store.get_all_documents()
    logging.info(f"Number of documents in the document store: {len(all_docs)}")

    for doc in all_docs:
        logging.debug(f"Document ID: {doc.id}, Title: {doc.meta['document_name']}, Content: {doc.content[:50]}, Status: {doc.meta['status']}")

    # Update embeddings for the documents
    document_store.update_embeddings(retriever)


# Step 2: Create the QA pipeline
pipe = ExtractiveQAPipeline(reader, retriever)

# Handle query processing
def handle_query(query):
    # Use BM25 to search for documents
    existing_docs = document_store.query(query=query)

    if not existing_docs:
        logging.error(f"Document not found in the store for query: {query}")
        return {"response": "Document not found.", "relevant_documents": []}

    # Use pipeline to generate answers (if needed)
    result = pipe.run(query=query, params={"Retriever": {"top_k": 10}, "Reader": {"top_k": 3}})

    if not result["answers"]:
        logging.warning(f"No answers found for query: {query}.")
        return {"response": "No answers found.", "relevant_documents": []}

    return {
        "response": result["answers"][0].answer,
        "relevant_documents": result["documents"],
    }




