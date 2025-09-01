# RAG-based Cooking Assistant

This is my capstone project for [DataTalksClub's LLM Zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp/tree/main) (2025).

## Description

A Retrieval-Augmented Generation (RAG) cooking assistant that delivers step-by-step cooking instructions and culinary guidance. Simply ask for any dish, and get comprehensive recipes with detailed preparation steps, ingredient lists, cooking techniques, and helpful tips.

## Datasets

The recipes are scraped from [Food.com](Food.com) - **88 All-Time Best Dinner Recipes**.

## Technologies
- `Python 3.10`
- `OpenAI` as an LLM
- `uv` for Python package and project manager
- `Docker` and `Docker Compose` for containerization
- `FastAPI` as the API interface (see [Background](#background) for more information on `FastAPI`) 

## Code

The code for the application is in the [recipe_assistant](recipe_assistant/) folder:

### Interface
* [app](recipe_assistant/app) - this is the folder that stores the `FastAPI` project.
    * [main.py](recipe_assistant/app/main.py) - this is the main entrypoint of our application. We start application from this file.
    * [api](recipe_assistant/app/api) - we stores our implementation of the API endpoints in this folder.
    * [core](recipe_assistant/app/core) - the project configs are stored in this folder.  
    * [models](recipe_assistant/app/models) - this folder stores our definition of the Pydantic model that represents the API request body.
* [api_example.http](recipe_assistant/api_example.http) - This http file utilizes the `REST Client` extension from VSCode. It provides a easy way to interact and test the API we build. 

### Ingestion
- [rag.py](recipe_assistant/rag.py) - the main RAG logic for building the prompt, retrieving the relevant documents, and generating the answers.
- [ingest.py](recipe_assistant/ingest.py) - processing and indexing the documents into `Qdrant` vector database.
- [scrape_recipes.py](recipe_assistant/scrape_recipes.py) - the scripts that scrapes the recipe data from [Food.com](Food.com).

## Using the application

### Prepare the environment

The project uses `uv` for project and dependencies management. You can install `uv` by following the [instruction](https://docs.astral.sh/uv/getting-started/installation/#installation-methods) from its official website. 

if you are not able to install `uv`, you can still use `pip` to install the requirements with the [requirements.txt](requirements.txt).

Please remember to create a `python virtual environment` before installing any packages and running any scripts.

**MacOS/Linux example:**
```
# if using uv
uv venv my-env # creates a virtual env named 'my-env'

source my-env/bin/activate # activate the virtual env

uv pip install -r requirements.txt
```

Non-uv command (standard way of using `pip` to create virtual env and install dependencies):
```
python -m venv my-env

source myenv/bin/activate

pip install -r requirements.txt
```

### Start Qdrant vector database

We use `docker compose` to spin up the Qdrant service.
```
cd Qdrant
docker compose up -d
```

### Scraping the source data (Optional)

I have saved the source data in [recipes.csv](data/recipes.csv). However, you can run the following script if you are interested in scraping the data yourself.

```
# If you have uv installed
cd recipe_assistant
uv run scrape_recipes.py
```

### Running the application

Inside the project root directory [recipe-rag-assistant](./), run the following command:
```
uv run uvicorn recipe_assistant.app.main:app --reload --host 0.0.0.0 --port 8000
```

This starts our FastAPI application on http://localhost:8000/. Use a browser to access this link and it will give you the following message:

```json
{"message":"Welcome to the recipe assistant application!"}
```

FastAPI generates an API swagger after we start our application: http://localhost:8000/docs. 


## Experiment

For experiments, we use Jupyter notebooks. They are saved in [`notebooks`](notebooks/) folder.

Use your preferred IDE (Anaconda, VSCode and etc.) to run the notebooks.

We have the following notebooks:
- [`rag-test.ipynb`](notebooks/rag-test.ipynb): This notebook contains the code for the RAG flow and the evaluation of the system
- [`evaluation-data-generation.ipynb`](notebooks/evaluation-data-generation.ipynb): This notebook generates the ground truth dataset with the LLM for retrieval evaluation. 

### Retrieval evaluation

The basic approach uses `sparse vector search` from `Qdrant` using model `bm25`.

- Hit rate: 99.545%
- MRR: 95.951%

The `dense vector search` from `Qdrant` gives the following results (model used: `jinaai/jina-embeddings-v2-small-en`):

- Hit rate: 98.864%
- MRR: 97.564%

The `Hybrid search` from `Qdrant` gives the following results:

- Hit rate: 99.318%
- MRR: 97.425%

The `Hybrid search` approach has similar results to `sparse vector search`, but it has slighly higher MRR.

### RAG flow evaluation

We used the LLM-as-a-Judge metric to evaluate the quality
of our RAG flow.

For `gpt-4o-mini`, we had:

- 427 (97%) `RELEVANT`
- 13 (3%) `PARTLY_RELEVANT`

For `gpt-4o`, we had:

- 420 (95%) `RELEVANT`
- 20 (5%) `PARTLY_RELEVANT`

Interestingly, `gpt-4o-mini` has a better performance than `gpt-4o`.

## Background

Here we provide a brief introduction to `FastAPI` which is not used in `LLMZoomcamp`.

### FastAPI
We use `FastAPI` for creating the API interface for our application. 

[`FastAPI`](https://fastapi.tiangolo.com/) is a modern, fast (high-performance), web framework for building APIs with Python based on standard Python type hints.

In our case, we send questions to `http://localhost:8000/api/v1/question`.