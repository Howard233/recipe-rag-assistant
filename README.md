# RAG-based Cooking Assistant

This is my capstone project for [DataTalksClub's LLM Zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp/tree/main) (2025).

## Description

A Retrieval-Augmented Generation (RAG) cooking assistant that delivers step-by-step cooking instructions and culinary guidance. Simply ask for any dish, and get comprehensive recipes with detailed preparation steps, ingredient lists, cooking techniques, and helpful tips.

## Datasets

The recipes are scraped from [Food.com](Food.com) - **88 All-Time Best Dinner Recipes**.

## Technologies
- `Python 3.12`
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
* [api_example.http](recipe_assistant/api_example.http) - This http file utilizes the `REST Client` extension from VSCode. It provides an easy way to interact and test the API we build. 
    * If you are unable to use this extension, you can still make requests with Python `requests` modules, or other `HTTP` request tools. 

### Ingestion
- [rag.py](recipe_assistant/rag.py) - the main RAG logic for building the prompt, retrieving the relevant documents, and generating the answers.
- [ingest.py](recipe_assistant/ingest.py) - processing and indexing the documents into `Qdrant` vector database.
- [scrape_recipes.py](recipe_assistant/scrape_recipes.py) - the scripts that scrapes the recipe data from [Food.com](Food.com).

## Using the application

### Preparing the Python environment

The project uses `uv` for project and dependencies management. You can install `uv` by following the [instruction](https://docs.astral.sh/uv/getting-started/installation/#installation-methods) from its official website. 

If you are not able to install `uv`, you can still use `pip` to install the requirements with the [requirements.txt](requirements.txt).

Please create a `Python virtual environment` before installing any packages and running any scripts/notebooks locally.

**MacOS/Linux example:**
```bash
# if using uv
uv venv my-env # creates a virtual env named 'my-env'

source my-env/bin/activate # activate the virtual env

uv pip install -r requirements.txt
```

### Preparing the environment variables
You should create an `.env` file that stores your OpenAI API key in the project folder. In addition, we put some other parameters that will be used by the app.

```bash
# example
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
QDRANT_URL=http://localhost:6333

# PostgreSQL Configuration
POSTGRES_HOST= postgres # localhost
POSTGRES_DB=recipe_assistant
POSTGRES_USER=recipe_user
POSTGRES_PASSWORD=recipe_user_pwd
POSTGRES_PORT=5432
```

### Scraping the source data (Optional)

I have saved the source data in [recipes.csv](data/recipes.csv). However, you can run the following script if you are interested in scraping the data yourself.

```bash
# If you have uv installed
cd recipe_assistant
uv run scrape_recipes.py
```

### Running the application

You need to start the services first. We use `docker-compose` to start the services.

#### Running the application with docker-compose
Inside the root directory: [recipe-rag-assistant](./), run
```bash
docker compose up
```
Wait until all services are ready. You can check it from the docker logging messages in the terminal.

Our FastAPI application can then be accessed on http://localhost:8000/. Use a browser to access this link and it will give you the following message:

```json
{"message":"Welcome to the recipe assistant application!"}
```

FastAPI generates an API swagger after the application is started: http://localhost:8000/docs. 

#### Database configuration
The database will be initialized once the application starts. To check the content of the database, use `psql`:

```bash
psql -U recipe_user -h localhost -p 5432 -d recipe_assistant
```

You will be asked to enter the password. It is defined in the `.env` file: `POSTGRES_PASSWORD`.

You can view the tables using `\dt` command:

```sql
\dt
```

You can select from the tables:
```sql
select * from conversations;
```

## Experiment

For experiments, we use Jupyter notebooks. They are saved in [`notebooks`](notebooks/) folder.

Use your preferred IDE (Anaconda, VSCode and etc.) to run the notebooks.

We have the following notebooks:
- [`rag-test.ipynb`](notebooks/rag-test.ipynb): This notebook contains the code for the RAG flow and the evaluation of the system
- [`evaluation-data-generation.ipynb`](notebooks/evaluation-data-generation.ipynb): This notebook generates the ground truth dataset with the LLM for retrieval evaluation. 

### Retrieval evaluation

The basic approach uses `sparse vector search` from `Qdrant` using model `bm25`.

- Hit rate: 100.000%
- MRR: 97.206%

The `dense vector search` from `Qdrant` gives the following results (model used: `jinaai/jina-embeddings-v2-small-en`):

- Hit rate: 100.000%
- MRR: 98.985%

The `Hybrid search` from `Qdrant` gives the following results:

- Hit rate: 100.000%
- MRR: 99.091%

The `Hybrid search` approach has the beset results, compared with other two search.

### RAG flow evaluation

We used the LLM-as-a-Judge metric to evaluate the quality
of our RAG flow.

For `gpt-4o-mini`, we had:

- 424 (96%) `RELEVANT`
- 12 (2%) `PARTLY_RELEVANT`
- 4 (1%) `NON_RELEVANT`

For `gpt-4o`, we had:

- 418 (95%) `RELEVANT`
- 18 (4%) `PARTLY_RELEVANT`
- 4 (1%) `NON_RELEVANT`

Interestingly, `gpt-4o-mini` has a better performance than `gpt-4o`.

## Background

Here we provide a brief introduction to `FastAPI` which is not used in `LLMZoomcamp`.

### FastAPI
We use `FastAPI` for creating the API interface for our application. 

[`FastAPI`](https://fastapi.tiangolo.com/) is a modern, fast (high-performance), web framework for building APIs with Python based on standard Python type hints.

In our case, we send questions to `http://localhost:8000/api/v1/question`.