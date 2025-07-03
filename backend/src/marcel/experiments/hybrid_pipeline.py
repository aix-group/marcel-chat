import logging
from typing import List

from haystack import Document, Pipeline
from haystack.components.builders import ChatPromptBuilder
from haystack.components.joiners.document_joiner import DocumentJoiner
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever
from haystack.dataclasses import ChatMessage
from haystack.document_stores.in_memory import InMemoryDocumentStore
from openai import AsyncOpenAI, OpenAI

from marcel.config import DATA_PATH, FAQ_PATH, LLM_API_KEY, LLM_BASE_URL, MODEL_NAME
from marcel.experiments import data_loader
from marcel.experiments.components import ContentLinkNormalizer
from marcel.experiments.faq_retriever import FAQRetriever
from marcel.routes import ChatMessage as InputChatMessage

FAQ_EMBEDDING_MODEL = "all-MiniLM-L6-v2"

logger = logging.getLogger(__name__)


system_prompt_general = """You are a helpful and engaging chatbot called Marcel. Your name is Marcel and you are employed at the Marburg University. You help students with questions regarding admission and enrolment to the MSc Data Science Program. Only engage in topics related to admission and enrolment. Do not engage in other discussions."""

system_prompt_rag = """
You are a helpful and engaging chatbot called Marcel. If someone asks you, your name is Marcel and you are employed at the Marburg University. You answer questions of students around their studies. Please answer the questions based on the provided documents only. Ignore your own knowledge. Don't say that you are looking at a set of documents. If you cannot find the answer to a given question in the documents you must apologize and say that you don't have any information about the topic (e.g., "Unfortunately, I do not have any knowledge about <rephrase the question>").
""".strip()

user_prompt_template_rag = """

Given these documents, answer the question.

## Documents
{% for doc in documents %}
### {{ doc.meta['og:title'] }}
{{ doc.content | replace("\n", "\\\\n") }}

{% endfor %}


## Question
{{ query }}
""".strip()


def get_pipeline(documents: List[Document], faqs: List[Document]):
    # Index documents
    document_store = InMemoryDocumentStore()
    document_store.write_documents(documents=documents)

    # Setup retrieval pipeline
    pipeline = Pipeline()

    def add(name, component):
        pipeline.add_component(name, component)

    def connect(component_a, component_b):
        pipeline.connect(component_a, component_b)

    add(
        "bm25_retriever",
        InMemoryBM25Retriever(document_store=document_store, top_k=5, scale_score=True),
    )
    add("faq_retriever", FAQRetriever(documents=documents, faqs=faqs, top_k=1))
    add("result_joiner", DocumentJoiner(join_mode="merge", top_k=5, weights=[1, 2]))
    add("content_link_normalizer", ContentLinkNormalizer())
    add(
        "prompt_builder",
        ChatPromptBuilder(
            variables=["documents"], required_variables=["documents", "query"]
        ),
    )

    connect("bm25_retriever", "result_joiner")
    connect("faq_retriever", "result_joiner")
    connect("result_joiner", "content_link_normalizer")
    connect("content_link_normalizer", "prompt_builder")

    return pipeline


class HybridPipeline:
    def __init__(self, documents=None, faqs=None):
        logger.info("init hybrid pipeline")
        if documents is None:
            documents = data_loader.load_documents(data_path=DATA_PATH)
        if faqs is None:
            faqs = data_loader.load_faqs(faq_path=FAQ_PATH)

        self.retriever = get_pipeline(documents, faqs)
        self.generator = OpenAI(
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL,
        )
        self.generator_async = AsyncOpenAI(
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL,
        )
        self.retriever.warm_up()

    def retrieve(self, query: str, history: List[InputChatMessage]):
        history_messages = [
            ChatMessage.from_user(message.content)
            if message.role == "user"
            else ChatMessage.from_assistant(message.content)
            for message in history
        ]

        retriever_results = self.retriever.run(
            {
                "bm25_retriever": {"query": query},
                "faq_retriever": {"text": query},
                "prompt_builder": {
                    "template": [ChatMessage.from_system(system_prompt_rag)]
                    + history_messages
                    + [ChatMessage.from_user(user_prompt_template_rag)],
                    "template_variables": {"query": query},
                },
            },
            include_outputs_from=set(
                [
                    "faq_retriever",
                    "bm25_retriever",
                    "content_link_normalizer",
                    "prompt_builder",
                ]
            ),
        )

        return retriever_results

    async def requires_retrieval(self, query: str, max_retries=1, timeout=2):
        prompt = (
            "Please determine if the following user utterance is a question. "
            "Respond with 'YES' if it is a genuine question. Respond with 'NO' if it is chit-chat or if the user asks the chatbot what kind of information it could provide, unrelated to earlier conversation."
            "Only respond with the label YES or NO.\n\nMessage: {message}"
        )

        client = self.generator_async.with_options(
            max_retries=max_retries, timeout=timeout
        )
        completion = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt.format(message=query)}],
            temperature=0.6,
            max_tokens=5,
            n=1,
        )
        content = completion.choices[0].message.content
        if content and content.strip():
            return "YES" in content.upper()

        raise ValueError("Unexpected response")

    async def run_async(self, query: str, history: List[InputChatMessage], debug=False):
        try:
            answer_strategy = (
                "retrieve"
                if await self.requires_retrieval(query)
                else "generate_with_history"
            )
        except Exception as e:
            logger.info(
                "Could not determine if query needs retrieval. Run retrieval.",
                exc_info=e,
            )
            answer_strategy = "retrieve"

        retriever_results = None
        if answer_strategy == "generate_with_history":
            messages = [
                {"role": "system", "content": system_prompt_general},
                *[
                    {"role": message.role, "content": message.content}
                    for message in history
                ],
                {"role": "user", "content": query},
            ]
        else:
            retriever_results = self.retrieve(query, history)
            messages = [
                message.to_openai_dict_format()
                for message in retriever_results["prompt_builder"]["prompt"]
            ]

        generator_results = await self.generator_async.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            stream=True,
        )  # type: ignore

        async def chunk_generator():
            async for chunk in generator_results:
                if len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield delta.content

        result = {
            "generated_answer": chunk_generator(),
            "documents": retriever_results["content_link_normalizer"]["documents"]
            if retriever_results
            else [],
            "answer_strategy": answer_strategy,
        }

        if debug:
            result["raw"] = retriever_results

        return result
