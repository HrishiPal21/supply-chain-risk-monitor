#!/usr/bin/env bash
# Supply Chain Risk Monitor — GCP deployment script
# Run: bash deploy.sh
# Prerequisites: gcloud CLI installed and authenticated (gcloud auth login)

set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION — edit these before running
# ─────────────────────────────────────────────────────────────────────────────
PROJECT_ID="project-c78fe78e-cf75-4da8-a24"
REGION="us-central1"
SERVICE_NAME="supply-chain-risk"
SQL_INSTANCE="supply-chain-db"
SQL_DB="supplychain"
SQL_USER="appuser"

# ─────────────────────────────────────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────────────────────────────────────
if [[ -z "$PROJECT_ID" ]]; then
  echo "ERROR: Set PROJECT_ID at the top of this script before running."
  exit 1
fi

REPO="us-central1-docker.pkg.dev/${PROJECT_ID}/supply-chain"
IMAGE="${REPO}/app"
CONNECTION_NAME="${PROJECT_ID}:${REGION}:${SQL_INSTANCE}"

echo ""
echo "═══════════════════════════════════════════════════"
echo "  Supply Chain Risk Monitor — GCP Deploy"
echo "  Project : $PROJECT_ID"
echo "  Region  : $REGION"
echo "  Service : $SERVICE_NAME"
echo "═══════════════════════════════════════════════════"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Set active project
# ─────────────────────────────────────────────────────────────────────────────
echo "▶ [1/8] Setting active project..."
gcloud config set project "$PROJECT_ID"

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Enable required APIs
# ─────────────────────────────────────────────────────────────────────────────
echo "▶ [2/8] Enabling APIs (this takes ~1 min the first time)..."
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Cloud SQL instance + database + user
# ─────────────────────────────────────────────────────────────────────────────
echo "▶ [3/8] Creating Cloud SQL instance (takes 3-5 min)..."
if gcloud sql instances describe "$SQL_INSTANCE" --project="$PROJECT_ID" &>/dev/null; then
  echo "   ✓ Instance '$SQL_INSTANCE' already exists — skipping create."
else
  gcloud sql instances create "$SQL_INSTANCE" \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region="$REGION" \
    --storage-size=10GB \
    --storage-auto-increase
  echo "   ✓ Instance created."
fi

echo "   Creating database..."
gcloud sql databases create "$SQL_DB" --instance="$SQL_INSTANCE" 2>/dev/null || \
  echo "   ✓ Database '$SQL_DB' already exists."

echo "   Creating DB user..."
echo -n "   Enter a password for DB user '$SQL_USER': "
read -rs SQL_PASSWORD
echo ""
gcloud sql users create "$SQL_USER" \
  --instance="$SQL_INSTANCE" \
  --password="$SQL_PASSWORD" 2>/dev/null || \
  echo "   ✓ User '$SQL_USER' already exists (password unchanged)."

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — Secrets
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "▶ [4/8] Storing secrets in Secret Manager..."
echo "   You'll be prompted for each API key."
echo ""

_upsert_secret() {
  local name="$1"
  local value="$2"
  if gcloud secrets describe "$name" --project="$PROJECT_ID" &>/dev/null; then
    echo "$value" | gcloud secrets versions add "$name" --data-file=-
    echo "   ✓ $name updated."
  else
    echo "$value" | gcloud secrets create "$name" \
      --replication-policy=automatic --data-file=-
    echo "   ✓ $name created."
  fi
}

echo -n "   OPENAI_API_KEY: "; read -rs V; echo ""; _upsert_secret "OPENAI_API_KEY" "$V"
echo -n "   PINECONE_API_KEY: "; read -rs V; echo ""; _upsert_secret "PINECONE_API_KEY" "$V"
echo -n "   NEWS_API_KEY: "; read -rs V; echo ""; _upsert_secret "NEWS_API_KEY" "$V"
echo -n "   EDGAR_EMAIL: "; read -r V; _upsert_secret "EDGAR_EMAIL" "$V"
_upsert_secret "POSTGRES_PASSWORD" "$SQL_PASSWORD"

# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — Pinecone config (not secrets, just env vars — still store safely)
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo -n "   PINECONE_INDEX_NAME (default: supply-chain-risk): "; read -r PINECONE_INDEX
PINECONE_INDEX="${PINECONE_INDEX:-supply-chain-risk}"
echo -n "   PINECONE_ENVIRONMENT (default: us-east-1): "; read -r PINECONE_ENV
PINECONE_ENV="${PINECONE_ENV:-us-east-1}"

# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — Artifact Registry repo
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "▶ [5/8] Creating Artifact Registry repository..."
if gcloud artifacts repositories describe supply-chain \
    --location="$REGION" --project="$PROJECT_ID" &>/dev/null; then
  echo "   ✓ Repository already exists."
else
  gcloud artifacts repositories create supply-chain \
    --repository-format=docker \
    --location="$REGION" \
    --description="Supply Chain Risk Monitor images"
  echo "   ✓ Repository created."
fi

gcloud auth configure-docker "us-central1-docker.pkg.dev" --quiet

# ─────────────────────────────────────────────────────────────────────────────
# STEP 7 — Build and push Docker image
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "▶ [6/8] Building and pushing Docker image (Cloud Build)..."
gcloud builds submit \
  --tag "$IMAGE" \
  --project="$PROJECT_ID" \
  .
echo "   ✓ Image pushed: $IMAGE"

# ─────────────────────────────────────────────────────────────────────────────
# STEP 8 — Grant Cloud Run SA access to secrets + Cloud SQL
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "▶ [7/8] Granting permissions..."

# Cloud Run uses the compute default service account by default
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

for SECRET in OPENAI_API_KEY PINECONE_API_KEY NEWS_API_KEY EDGAR_EMAIL POSTGRES_PASSWORD; do
  gcloud secrets add-iam-policy-binding "$SECRET" \
    --member="serviceAccount:${SA}" \
    --role="roles/secretmanager.secretAccessor" \
    --project="$PROJECT_ID" --quiet
done

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA}" \
  --role="roles/cloudsql.client" --quiet

echo "   ✓ Permissions set."

# ─────────────────────────────────────────────────────────────────────────────
# STEP 9 — Deploy to Cloud Run
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "▶ [8/8] Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE" \
  --region "$REGION" \
  --platform managed \
  --add-cloudsql-instances "$CONNECTION_NAME" \
  --set-env-vars "CLOUD_SQL_CONNECTION_NAME=${CONNECTION_NAME}" \
  --set-env-vars "POSTGRES_DB=${SQL_DB}" \
  --set-env-vars "POSTGRES_USER=${SQL_USER}" \
  --set-env-vars "PINECONE_INDEX_NAME=${PINECONE_INDEX}" \
  --set-env-vars "PINECONE_ENVIRONMENT=${PINECONE_ENV}" \
  --set-secrets "OPENAI_API_KEY=OPENAI_API_KEY:latest" \
  --set-secrets "PINECONE_API_KEY=PINECONE_API_KEY:latest" \
  --set-secrets "NEWS_API_KEY=NEWS_API_KEY:latest" \
  --set-secrets "EDGAR_EMAIL=EDGAR_EMAIL:latest" \
  --set-secrets "POSTGRES_PASSWORD=POSTGRES_PASSWORD:latest" \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --concurrency 10 \
  --min-instances 0 \
  --max-instances 3

echo ""
echo "═══════════════════════════════════════════════════"
echo "  Deployment complete!"
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --region "$REGION" --format="value(status.url)")
echo "  URL: $SERVICE_URL"
echo "═══════════════════════════════════════════════════"
