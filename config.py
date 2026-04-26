import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def get_openai_client() -> OpenAI:
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        raise EnvironmentError(
            "OPENAI_API_KEY is not set. "
            "Add it to your .env file or environment variables and restart the app."
        )
    return OpenAI(api_key=key)


# OpenAI
OPENAI_MODEL: str = "gpt-4o"          # judge, guardrail, exposure (high-stakes reasoning)
ANALYST_MODEL: str = "gpt-4o-mini"    # bear, bull, geo analysts (3 calls — biggest cost lever)
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

# SEC EDGAR
EDGAR_EMAIL: str = os.environ.get("EDGAR_EMAIL", "user@example.com")
EDGAR_UA: str = f"SupplyChainRiskMonitor {EDGAR_EMAIL}"

# GCP Cloud Storage
GCS_BUCKET_NAME: str = os.environ.get("GCS_BUCKET_NAME", "supply-chain-risk-raw")
GCP_PROJECT_ID: str = os.environ.get("GCP_PROJECT_ID", "")
