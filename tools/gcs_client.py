import json
import uuid
from datetime import datetime
from google.cloud import storage
from config import GCS_BUCKET_NAME


def _client() -> storage.Client:
    return storage.Client()


def upload_raw_docs(docs: list[dict], query: str) -> str:
    """Upload raw retrieved docs to GCS. Returns the GCS blob path."""
    client = _client()
    bucket = client.bucket(GCS_BUCKET_NAME)

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    blob_name = f"raw/{timestamp}_{uuid.uuid4().hex[:8]}.json"

    payload = {"query": query, "fetched_at": timestamp, "docs": docs}
    blob = bucket.blob(blob_name)
    blob.upload_from_string(json.dumps(payload), content_type="application/json")

    return f"gs://{GCS_BUCKET_NAME}/{blob_name}"


def download_raw_docs(blob_path: str) -> list[dict]:
    """Download raw docs from a GCS path (gs://bucket/blob)."""
    client = _client()
    path = blob_path.replace(f"gs://{GCS_BUCKET_NAME}/", "")
    bucket = client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(path)
    data = json.loads(blob.download_as_text())
    return data.get("docs", [])
