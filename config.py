import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def get_openai_client() -> OpenAI:
    return OpenAI(api_key=os.environ["OPENAI_API_KEY"])


# OpenAI
OPENAI_MODEL: str = "gpt-4o"
EMBED_MODEL: str = "text-embedding-3-small"
EMBED_DIM: int = 1536

# Pinecone
PINECONE_API_KEY: str = os.environ.get("PINECONE_API_KEY", "")
PINECONE_INDEX_NAME: str = os.environ.get("PINECONE_INDEX_NAME", "supply-chain-risk")
PINECONE_ENVIRONMENT: str = os.environ.get("PINECONE_ENVIRONMENT", "us-east-1")

# NewsAPI
NEWS_API_KEY: str = os.environ.get("NEWS_API_KEY", "")

# GCP Cloud SQL (PostgreSQL)
POSTGRES_HOST: str = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT: str = os.environ.get("POSTGRES_PORT", "5432")
POSTGRES_DB: str = os.environ.get("POSTGRES_DB", "supply_chain")
POSTGRES_USER: str = os.environ.get("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD: str = os.environ.get("POSTGRES_PASSWORD", "")
CLOUD_SQL_CONNECTION_NAME: str = os.environ.get("CLOUD_SQL_CONNECTION_NAME", "")

# GCP Cloud Storage
GCS_BUCKET_NAME: str = os.environ.get("GCS_BUCKET_NAME", "supply-chain-risk-raw")
GCP_PROJECT_ID: str = os.environ.get("GCP_PROJECT_ID", "")
