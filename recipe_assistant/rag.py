import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from openai import OpenAI

openai_client = OpenAI()

from qdrant_client import QdrantClient, models

qdrant_client = QdrantClient("http://localhost:6333")

EMBEDDING_DIMENSIONALITY = 512
