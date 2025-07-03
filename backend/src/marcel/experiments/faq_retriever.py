import logging
from typing import List, Literal

from haystack import Document, Pipeline, component, super_component
from haystack.components.embedders import (
    SentenceTransformersDocumentEmbedder,
    SentenceTransformersTextEmbedder,
)
from haystack.components.retrievers import (
    InMemoryEmbeddingRetriever,
)
from haystack.components.writers import DocumentWriter
from haystack.document_stores.in_memory import InMemoryDocumentStore

logger = logging.getLogger(__name__)


@component
class DocumentDeduplicator:
    @component.output_types(documents=List[Document])
    def run(self, documents: List[Document]):
        seen = set()
        filtered = []
        for doc in documents:
            if doc.id not in seen:
                filtered.append(doc)
                seen.add(doc.id)
        return {"documents": filtered}


@component
class ParentDocumentRetriever:
    def __init__(self, documents: List[Document]):
        document_store = InMemoryDocumentStore()
        document_store.write_documents(documents=documents)
        self.document_store = document_store

    @component.output_types(documents=List[Document])
    def run(self, documents: List[Document]):
        result = []
        for doc in documents:
            parent_id = doc.meta["parent_id"]
            if isinstance(parent_id, list):
                parent_filter = {
                    "operator": "OR",
                    "conditions": [
                        {"field": "id", "operator": "==", "value": id_}
                        for id_ in parent_id
                    ],
                }
            else:
                parent_filter = {"field": "id", "operator": "==", "value": parent_id}

            parents = self.document_store.filter_documents(parent_filter)
            for parent_doc in parents:
                parent_doc = parent_doc.to_dict()
                parent_doc["score"] = doc.score
                parent_doc = Document.from_dict(parent_doc)
                result.append(parent_doc)
        return {"documents": result}


@super_component
class FAQRetriever:
    def __init__(
        self,
        documents: List[Document],
        faqs: List[Document],
        embedding_model="all-MiniLM-L6-v2",
        embedding_similarity_function: Literal["dot_product", "cosine"] = "cosine",
        top_k=1,
    ):
        # Assign parent IDs to FAQs.
        # NOTE: this assumes 1-1 mapping of url to doc. Needs to be revisited if we chunk documents (1-n relation).
        url_to_doc_id = {doc.meta["url"]: doc.id for doc in documents}
        faqs_with_parent = []
        for faq in faqs:
            try:
                parent_ids = [url_to_doc_id[url] for url in faq.meta["sources"]]
                faq = faq.to_dict()
                faq["parent_id"] = parent_ids
                faq = Document.from_dict(faq)
                faqs_with_parent.append(faq)
            except KeyError:
                logger.warning("No parent for faq: %s", faq)

        # Index FAQs
        faq_store = InMemoryDocumentStore(
            embedding_similarity_function=embedding_similarity_function
        )
        faq_indexing = Pipeline()
        faq_indexing.add_component(
            "embedder",
            SentenceTransformersDocumentEmbedder(
                model=embedding_model,
                progress_bar=False,
                local_files_only=True,
            ),
        )
        faq_indexing.add_component("writer", DocumentWriter(document_store=faq_store))
        faq_indexing.connect("embedder", "writer")
        faq_indexing.run({"documents": faqs_with_parent})

        pipeline = Pipeline()
        pipeline.add_component(
            "query_embedder",
            SentenceTransformersTextEmbedder(
                model=embedding_model,
                progress_bar=False,
                local_files_only=True,
            ),
        )
        pipeline.add_component(
            "faq_retriever",
            InMemoryEmbeddingRetriever(document_store=faq_store, top_k=top_k),
        )
        pipeline.add_component(
            "parent_document_retriever",
            ParentDocumentRetriever(documents=documents),
        )
        pipeline.add_component("document_deduplicator", DocumentDeduplicator())

        pipeline.connect("query_embedder.embedding", "faq_retriever.query_embedding")
        pipeline.connect("faq_retriever", "parent_document_retriever")
        pipeline.connect("parent_document_retriever", "document_deduplicator")
        self.pipeline = pipeline
