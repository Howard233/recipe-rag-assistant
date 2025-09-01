from . import ingest

from qdrant_client import QdrantClient, models

from dotenv import load_dotenv
from openai import OpenAI
from typing import List, Dict, Any

# preparation
load_dotenv()
openai_client = OpenAI()
ingest.index_documents()
qdrant_client = QdrantClient("http://localhost:6333")


def qdrant_rrf_search(query, collection_name="recipe-rag-hybrid", limit=5) -> List[models.ScoredPoint]:
    """rrf search for our rag

    Args:
        query (_type_): user query
        collection_name (str, optional): Qdrant collection name. Defaults to "recipe-rag-hybrid".
        limit (int, optional): results returned. Defaults to 5.

    Returns:
        List[models.ScoredPoint]: _description_
    """

    query_points = qdrant_client.query_points(
        collection_name=collection_name,
        prefetch=[
            models.Prefetch(
                query=models.Document(
                    text=query,
                    model="jinaai/jina-embeddings-v2-small-en",
                ),
                using="jina-small",
                limit=(5 * limit),
            ),
            models.Prefetch(
                query=models.Document(
                    text=query,
                    model="Qdrant/bm25",
                ),
                using="bm25",
                limit=(5 * limit),
            ),
        ],
        # Fusion query enables fusion on the prefetched results
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        with_payload=True,
    )

    results = []
    for point in query_points.points:
        results.append(point.payload)
    return results

def build_prompt(query:str, search_results:List[models.ScoredPoint]) -> str:
    prompt_template = """
You're a cooking assistant. Answer the QUESTION based on the CONTEXT from the recipe database.
Use only the facts from the CONTEXT when answering the QUESTION.

QUESTION: {question}

CONTEXT: 
{context}
""".strip()

    context = ""

    for doc in search_results:
        context = (
            context + f"{doc['text']}\n\n"
        )  # doc['text'] should contain all the recipe information

    prompt = prompt_template.format(question=query, context=context).strip()
    return prompt

def llm(prompt:str, llm_model:str="gpt-4o-mini") -> str:
    """llm generating the answer from the prompt

    Args:
        prompt (str): prompt built from the serach results
        llm_model (str, optional): llm model used. Defaults to "gpt-4o-mini".

    Returns:
        str: llm generated answer
    """
    response = openai_client.chat.completions.create(
        model=llm_model, messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content