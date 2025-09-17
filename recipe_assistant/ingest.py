import pandas as pd
from qdrant_client import QdrantClient, models
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

from pathlib import Path

load_dotenv()

# Find the project root (where data folder is located)
current_file = Path(__file__)  # ingest.py location
project_root = current_file.parent.parent  # Go up to recipe-rag-assistant
DATA_PATH = project_root / "data" / "recipes.csv"
COLLECTION_NAME = "recipe-rag-hybrid"

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
qdrant_client = QdrantClient(QDRANT_URL)


def create_qdrant_collection(collection_name: str = COLLECTION_NAME) -> None:
    """create a collection within Qdrant Vector DB for hybrid search

    Args:
        collection_name (str): the name of the collection to be created. Defaults to COLLECTION_NAME.
    """

    # hybrid search with Qdrant
    if not qdrant_client.collection_exists(collection_name):
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config={
                # Named dense vector for jinaai/jina-embeddings-v2-small-en
                "jina-small": models.VectorParams(
                    size=512,
                    distance=models.Distance.COSINE,
                ),
            },
            sparse_vectors_config={
                "bm25": models.SparseVectorParams(
                    modifier=models.Modifier.IDF,
                )
            },
        )


def prepare_recipe_documents(data_path: str = DATA_PATH) -> List[Dict[str, Any]]:
    """prepare the recipe documents for indexing

    Args:
        data_path (str, optional): path to the recipe data source. Defaults to DATA_PATH.

    Returns:
        List[Dict[str, Any]]: prepared recipe documents
    """

    df_recipes = pd.read_csv(data_path)
    recipes_documents = df_recipes.to_dict(orient="records")

    for recipe in recipes_documents:
        description_stripped = recipe["recipe_description"].strip()
        directions_joined = " ".join(eval(recipe["directions"]))
        ingredients_joined = "; ".join(eval(recipe["ingredients"]))

        text = f"Recipe: {recipe['recipe_name'].strip()} | Description: {description_stripped} | Ratings: {recipe['ratings'].strip()} | Ready in: {recipe['ready-in'].strip()} | Directions: {directions_joined.strip()} | Ingredients: {ingredients_joined.strip()}"

        recipe["text"] = text

    return recipes_documents


def index_documents() -> None:
    """index the Qdrant vector DB with recipes documents"""
    recipes_documents = prepare_recipe_documents()

    # construct points
    points = []

    for recipe in recipes_documents:
        point = models.PointStruct(
            id=recipe["recipe_id"],
            vector={
                "jina-small": models.Document(
                    text=recipe["text"],
                    model="jinaai/jina-embeddings-v2-small-en",
                ),
                "bm25": models.Document(
                    text=recipe["text"],
                    model="Qdrant/bm25",
                ),
            },
            payload={
                "recipe_id": recipe["recipe_id"],
                "text": recipe["text"],
                "recipe_name": recipe["recipe_name"],
                "recipe_link": recipe["recipe_link"],
                "recipe_description": recipe["recipe_description"],
                "ratings": recipe["ratings"],
                "ready-in": recipe["ready-in"],
                "directions": recipe["directions"],
                "ingredients": recipe["ingredients"],
            },
        )
        points.append(point)

    # upsert into DB
    qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points)
