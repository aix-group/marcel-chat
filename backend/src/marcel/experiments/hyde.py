import os
from typing import List

import numpy as np
from haystack import Pipeline, component
from haystack.components.builders import ChatPromptBuilder
from haystack.components.embedders import SentenceTransformersDocumentEmbedder
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.dataclasses import ChatMessage, Document
from haystack.utils import Secret

system_prompt = """You are an employee at the University of Marburg. Your task is to generate documents that provide useful information to help students with their study-related questions. Your response should be formatted as a Markdown page, suitable for publication on the university website. Make sure that the page includes all relevant information, but keep the length below 300 words."""

user_prompt = "This is a student question: {{question}}\n\nGenerated page:"
question = "What are the admission requirements for MSc data science?"


@component
class AverageDocumentEmbedding:
    @component.output_types(embedding=List[float])
    def run(self, documents: List[Document]):
        stacked_embeddings = np.array([doc.embedding for doc in documents])
        avg_embedding = np.mean(stacked_embeddings, axis=0)
        return {"embedding": avg_embedding.tolist()}


@component
class ChatMessagesToDocuments:
    @component.output_types(documents=List[Document])
    def run(self, answers: List[ChatMessage]):
        return {"documents": [Document(content=answer.text) for answer in answers]}


@component
class HyDE:
    def __init__(
        self,
        embedding_model="sentence-transformers/multi-qa-mpnet-base-dot-v1",
        n=1,
        temperature=0.75,
        max_tokens=512,
        embedding_prefix="",
    ):
        self.embedding_model = embedding_model
        self.n = n
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.embedding_prefix = embedding_prefix

        pipeline = Pipeline()
        pipeline.add_component("prompt_builder", ChatPromptBuilder())
        pipeline.add_component(
            "generator",
            OpenAIChatGenerator(
                model="neuralmagic/Meta-Llama-3.1-70B-Instruct-quantized.w8a8",
                api_base_url=os.environ["LLM_BASE_URL"],
                api_key=Secret.from_token(os.environ["LLM_API_KEY"]),
                generation_kwargs={
                    "n": n,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=240,
                max_retries=0,
            ),
        )
        pipeline.add_component("document_converter", ChatMessagesToDocuments())
        pipeline.add_component(
            "document_embedder",
            SentenceTransformersDocumentEmbedder(
                model=embedding_model, progress_bar=False, prefix=embedding_prefix
            ),
        )
        pipeline.add_component("embedding_aggregator", AverageDocumentEmbedding())

        pipeline.connect("prompt_builder", "generator")
        pipeline.connect("generator", "document_converter")
        pipeline.connect("document_converter", "document_embedder")
        pipeline.connect("document_embedder", "embedding_aggregator")
        self.pipeline = pipeline

    @component.output_types(
        hypothetical_documents=List[Document], embedding=List[float]
    )
    def run(self, text: str):
        result = self.pipeline.run(
            {
                "prompt_builder": {
                    "template": [
                        ChatMessage.from_system(system_prompt),
                        ChatMessage.from_user(user_prompt),
                    ],
                    "template_variables": {"question": text},
                }
            },
            include_outputs_from=set(["document_embedder", "embedding_aggregator"]),
        )
        return {
            "hypothetical_documents": result["document_embedder"]["documents"],
            "embedding": result["embedding_aggregator"]["embedding"],
        }

    def warm_up(self):
        self.pipeline.warm_up()
