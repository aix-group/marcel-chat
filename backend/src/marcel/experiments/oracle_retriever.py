import random
from typing import Any, Dict, List, Optional

import numpy as np
from haystack import (
    Document,
    component,
)
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever
from haystack.document_stores.in_memory import InMemoryDocumentStore


class BM25RetrieverWithOracle(InMemoryBM25Retriever):
    def __init__(
        self,
        document_store: InMemoryDocumentStore,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        scale_score: bool = False,
        mode: Optional[str] = "default",
    ):
        """BM25 retriever to estimate upper/lower bounds based on oracle and random retriever. The overall interface is equivalent to the Haystack InMemoryBM25Retriever.

        Parameters
        ----------
        mode : Optional[str], optional
            Retriever mode accepting the following choices:

            - default: equivalent to standard BM25 retrieval
            - random: select k random documents from the document store
            - oracle_random: selects documents matching condition and adds up to k-len(oracle) random documents
            - oracle_related: selects documents matching condition and adds up to k-len(oracle) related documents scored with BM25
            - oracle: selects documents matching condition
        """
        super().__init__(
            document_store=document_store,
            filters=filters,
            top_k=top_k,
            scale_score=scale_score,
        )
        if mode not in [
            "oracle",
            "oracle_related",
            "oracle_random",
            "random",
            "default",
        ]:
            raise ValueError(f"Invalid mode {mode}.")
        self.mode = mode

    def _oracle_retrieve(self, filters):
        if not filters:
            return []
        docs = self.document_store.filter_documents(filters=filters)
        result = []
        for doc in docs:
            doc_fields = doc.to_dict()
            doc_fields["score"] = 999999
            result.append(Document.from_dict(doc_fields))
        return result

    def _random_retrieve(self, top_k):
        k = min(top_k, self.document_store.count_documents())
        docs = random.sample(list(self.document_store.storage.values()), k)
        scores = list(sorted(np.random.uniform(0, 1, len(docs)), reverse=True))
        result = []
        for doc, score in zip(docs, scores):
            doc_fields = doc.to_dict()
            doc_fields["score"] = score
            result.append(Document.from_dict(doc_fields))
        return result

    @component.output_types(documents=List[Document])
    def run(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: Optional[int] = None,
        scale_score: Optional[bool] = None,
    ):
        if filters is None:
            filters = self.filters
        if top_k is None:
            top_k = self.top_k
        if scale_score is None:
            scale_score = self.scale_score

        docs = []
        if self.mode == "oracle":
            docs = self._oracle_retrieve(filters=filters)
        elif self.mode == "oracle_related":
            docs_related = self.document_store.bm25_retrieval(
                query=query, top_k=top_k, scale_score=scale_score
            )
            docs_oracle = self._oracle_retrieve(filters=filters)
            ids_oracle = set(doc.id for doc in docs_oracle)
            docs_related = [doc for doc in docs_related if doc.id not in ids_oracle]
            docs = docs_oracle + docs_related[: top_k - len(docs_oracle)]
        elif self.mode == "oracle_random":
            docs_random = self._random_retrieve(top_k)
            docs_oracle = self._oracle_retrieve(filters=filters)
            ids_oracle = set(doc.id for doc in docs_oracle)
            docs_random = [doc for doc in docs_random if doc.id not in ids_oracle]
            docs = docs_oracle + docs_random[: top_k - len(docs_oracle)]
        elif self.mode == "random":
            docs = self._random_retrieve(top_k)
        elif self.mode == "default":
            docs = self.document_store.bm25_retrieval(
                query=query, filters=filters, top_k=top_k, scale_score=scale_score
            )
        else:
            docs = []
        return {"documents": docs}
