# RAG-based Cooking Assistant

This is my capstone project for [DataTalksClub's LLM Zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp/tree/main) (2025).

# Description

A Retrieval-Augmented Generation (RAG) cooking assistant that delivers step-by-step cooking instructions and culinary guidance. Simply ask for any dish, and get comprehensive recipes with detailed preparation steps, ingredient lists, cooking techniques, and helpful tips.

# Datasets

The recipes are scraped from [Food.com](Food.com) - **88 All-Time Best Dinner Recipes**.

# Technologies
- `Python 3.10`
- `OpenAI` as an LLM
- `uv` for Python package and project manager
- `Docker` and `Docker Compose` for containerization

# Preparation

The project uses `uv` for project and dependencies management. You can install `uv` by following the [instruction](https://docs.astral.sh/uv/getting-started/installation/#installation-methods) from its official website. 

if you are not able to install `uv`, you can still use `pip` to install the requirements.

Please remember to create a python virtual environment before installing any packages and running any scripts.

**MacOS/Linux example:**
```
# if using uv
uv venv my-env # creates a virtual env named 'my-env'

source my-env/bin/activate # activate the virtual env

uv pip install -r requirements.txt
```

Non-uv command:
```
python -m venv my-env

source myenv/bin/activate

pip install -r requirements.txt
```
