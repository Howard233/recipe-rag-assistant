from qdrant_client import QdrantClient, models
import pandas as pd

qdrant_client = QdrantClient("http://localhost:6333")

EMBEDDING_DIMENSIONALITY = 512


def create_qdrant_collection(collection_name):
    if not qdrant_client.collection_exists(collection_name=collection_name):
        print(f'New Qdrant collections: {collection_name}. Creating it.')
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=EMBEDDING_DIMENSIONALITY, distance=models.Distance.COSINE
            ),
        )
        print('Collection created')


def load_points(
    collection_name,
    data_path="../data/recipes.csv",
    model_handle="jinaai/jina-embeddings-v2-small-en",
):
    create_qdrant_collection(collection_name)
    df_recipes = pd.read_csv(data_path)
    points = []

    recipes_raw = df_recipes.to_dict(orient="records")
    for recipe in recipes_raw:
        description_stripped = recipe["recipe_description"].strip()
        directions_joined = " ".join(eval(recipe["directions"]))
        ingredients_joined = "; ".join(eval(recipe["ingredients"]))

        text = f"Recipe: {recipe['recipe_name'].strip()} | Description: {description_stripped} | Ratings: {recipe['ratings'].strip()} | Ready in: {recipe['ready-in'].strip()} | Directions: {directions_joined.strip()} | Ingredients: {ingredients_joined.strip()}"
        recipe["text"] = text

        point = models.PointStruct(
            id=recipe["recipe_id"],
            vector=models.Document(
                text=recipe["text"], model=model_handle
            ),  # embedding the text
            payload={
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

    qdrant_client.upsert(collection_name=collection_name, points=points)
