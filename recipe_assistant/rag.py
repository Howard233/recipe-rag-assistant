from . import ingest

from qdrant_client import QdrantClient, models

from dotenv import load_dotenv
from openai import OpenAI
from typing import List, Dict, Any, Tuple
import os
from time import time
import json

# preparation
load_dotenv()
openai_client = OpenAI()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
qdrant_client = QdrantClient(QDRANT_URL)

def init_qdrant():
    """Initialize and index documents in Qdrant"""
    ingest.create_qdrant_collection()
    ingest.index_documents()

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

def llm(prompt:str, llm_model:str) -> Tuple[str, Dict[str, int]]:
    """generating the answer using the llm after the retreival 

    Args:
        prompt (str): prompt
        llm_model (str): llm model

    Returns:
        Tuple[str, Dict[str, int]]:: generated answer, and the stats of the token for the llm usage
    """
    response = openai_client.chat.completions.create(
        model=llm_model, messages=[{"role": "user", "content": prompt}]
    )

    answer = response.choices[0].message.content

    token_stats = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
    }
    return answer, token_stats

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


def evalualte_relevance(question, answer):

    evaluation_prompt_template = """
    You are an expert evaluator for a RAG system.
    Your task is to analyze the relevance of the generated answer to the given question.
    Based on the relevance of the generated answer, you will classify it
    as "NON_RELEVANT", "PARTLY_RELEVANT", or "RELEVANT".

    Here is the data for evaluation:

    Question: {question}
    Generated Answer: {answer}

    Please analyze the content and context of the generated answer in relation to the question
    and provide your evaluation in parsable JSON without using code blocks:

    {{
    "Relevance": "NON_RELEVANT" | "PARTLY_RELEVANT" | "RELEVANT",
    "Explanation": "[Provide a brief explanation for your evaluation]"
    }}
    """.strip()

    prompt = evaluation_prompt_template.format(question=question, answer=answer)
    evaluation, tokens = llm(prompt, llm_model='gpt-4o-mini')

    try:
        json_eval = json.loads(evaluation)
        return json_eval, tokens
    except json.JSONDecodeError:
        result = {"Relevance": "UNKNOWN", "Explanation": "Failed to parse evaluation"}
        return result, tokens

OPENAI_PRICING = {
    "gpt-5": {
        "input": 1.25,
        "output": 10.00
    },
    "gpt-5-mini": {
        "input": 0.25,
        "output": 2.00
    },
    "gpt-5-nano": {
        "input": 0.05,
        "output": 0.40
    },
    "gpt-4o-mini": {
        "input": 0.15,     # dollars per 1M tokens
        "output": 0.60
    },
    "gpt-4o": {
        "input": 2.50,
        "output": 10.00
    },
    }

def calculate_openai_cost(model, tokens):

    openai_cost = None

    if model not in OPENAI_PRICING:
        print("Model not recognized. OpenAI cost calculation failed.")
    else:
        cost_info = OPENAI_PRICING[model]
        openai_cost = tokens["prompt_tokens"] * cost_info["input"] / 1000000 + tokens["completion_tokens"] * cost_info["output"] / 1000000
        
    return openai_cost


def rag(query:str, llm_model:str="gpt-4o-mini", limit:int=5) -> str:
    """llm generating the answer from the prompt

    Args:
        query (str): user query
        llm_model (str, optional): llm model used. Defaults to "gpt-4o-mini".

    Returns:
        str: llm generated answer
    """
    start_time = time()

    search_results = qdrant_rrf_search(query, limit=limit)
    prompt = build_prompt(query, search_results)
    answer_text, token_stats = llm(prompt, llm_model)

    relevance, rel_token_stats = evalualte_relevance(query, answer_text)

    end_time = time()
    response_time = end_time - start_time

    openai_cost_rag = calculate_openai_cost(llm_model, token_stats)
    openai_cost_eval = calculate_openai_cost(llm_model, rel_token_stats)

    openai_cost = openai_cost_rag + openai_cost_eval

    answer_data = {
        "answer": answer_text,
        "model_used": llm_model,
        "response_time": response_time,
        "relevance": relevance.get("Relevance", "UNKNOWN"),
        "relevance_explanation": relevance.get("Explanation", "Failed to parse evaluation"),
        "prompt_tokens": token_stats["prompt_tokens"],
        "completion_tokens": token_stats["completion_tokens"],
        "total_tokens": token_stats["total_tokens"],
        "eval_prompt_tokens": rel_token_stats["prompt_tokens"],
        "eval_completion_tokens": rel_token_stats["completion_tokens"],
        "eval_total_tokens": rel_token_stats["total_tokens"],
        "openai_cost": openai_cost
    }

    return answer_data