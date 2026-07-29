"""
Knowledge base and FAISS vector store setup.

Loads the health knowledge base from data/medical_kb.json and builds a
FAISS index over it using local sentence transformer embeddings, so the
retrieve step in the graph can run a similarity search over it.
"""

import json
import os

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

from config import EMBEDDING_MODEL_NAME

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "medical_kb.json")


def load_raw_documents():
    # just reads the json file into a plain python list of dicts
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_vector_store():
    # read the knowledge base file
    raw_documents = load_raw_documents()

    # turn each entry into a LangChain Document, topic and source go in
    # metadata so the retrieve node can show them as citations later
    documents = []
    for entry in raw_documents:
        doc = Document(
            page_content=entry["content"],
            metadata={
                "id": entry["id"],
                "topic": entry["topic"],
                "source": entry["source"],
            },
        )
        documents.append(doc)

    # loads the embedding model, downloads it once on first run, then it
    # is cached locally by sentence transformers
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

    # builds the FAISS index in memory from the documents and embeddings
    vector_store = FAISS.from_documents(documents, embeddings)
    return vector_store