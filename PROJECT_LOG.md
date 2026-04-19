# Supply Chain Risk Monitor — Project Log

---

## Day 1 — 2026-04-19

### What we built

Full project scaffold from zero. Every file is wired and importable — nothing is pseudocode.

**Stack finalized**
- LLM: OpenAI GPT-4o
- Agents: LangGraph + LangChain
- RAG: Pinecone + OpenAI `text-embedding-3-small`
- Data: RSS Feeds + SEC EDGAR + NewsAPI
- Database: GCP Cloud SQL (PostgreSQL)
- Storage: GCP Cloud Storage
- Frontend: Streamlit (3 pages)
- Containerization: Docker + Docker Compose
- Deployment: GCP Cloud Run
- CI/CD: GitHub Actions → GCR → Cloud Run

**Files created**

| File | Status |
|---|---|
| `agents/state.py` | Pre-existing, kept as-is |
| `agents/graph.py` | Built + fixed fan-out bug |
| `agents/nodes/data_retriever.py` | Built + updated for full stack |
| `agents/nodes/bear_analyst.py` | Built |
| `agents/nodes/bull_analyst.py` | Built |
| `agents/nodes/geopolitical_analyst.py` | Built |
| `agents/nodes/judge.py` | Built — returns structured JSON with risk score 0–100 |
| `agents/nodes/guardrail.py` | Built — trust scores + hallucination flags |
| `tools/edgar.py` | Built |
| `tools/news.py` | Built |
| `tools/rss_feed.py` | Built — 5 curated feeds |
| `tools/pinecone_client.py` | Built + index connection cached |
| `tools/gcs_client.py` | Built |
| `tools/postgres_db.py` | Built — Cloud SQL + local Docker compatible |
| `db/schema.sql` | Built — PostgreSQL DDL |
| `app.py` | Built — Streamlit entry point |
| `pages/1_Search.py` | Built |
| `pages/2_Results.py` | Built |
| `pages/3_GuardRail.py` | Built |
| `config.py` | Built — single source for all env vars |
| `Dockerfile` | Built — Cloud Run compatible |
| `docker-compose.yml` | Built — app + Postgres sidecar |
| `.github/workflows/deploy.yml` | Built — full CI/CD pipeline |
| `requirements.txt` | Built |
| `.env.example` | Built |
| `.gitignore` | Built |

**Bugs caught and fixed (pre-review)**
1. `judge.py` — unused `import re` removed
2. `postgres_db.py` — JSONB columns needed `psycopg2.extras.Json()` wrapper, not raw `json.dumps()`
3. `postgres_db.py` — schema path changed from relative string to `os.path` anchored to `__file__`
4. `pinecone_client.py` — `_get_index()` was creating a new client + calling `list_indexes()` on every call; fixed with module-level cache
5. `data_retriever.py` — deduplication was comparing dict objects (never matched); fixed to compare by `text` content
6. `2_Results.py` — `score:.0f` would crash on `None`; added null guard + `st.cache_data(ttl=30)` to stop DB hits on every rerender
7. `requirements.txt` — `pinecone-client` is deprecated; corrected to `pinecone`

---

## Day 2 — Pick up here

**Priority 1 — Make it runnable locally**
- [ ] `cp .env.example .env` and fill in: `OPENAI_API_KEY`, `PINECONE_API_KEY`, `NEWS_API_KEY`
- [ ] `docker compose up` — verify Postgres starts and schema applies cleanly
- [ ] `pip install -r requirements.txt` in a venv and confirm no import errors
- [ ] Run a single end-to-end query from `1_Search.py` with `streamlit run app.py`

**Priority 2 — Validate the LangGraph pipeline**
- [ ] Smoke test `run_pipeline("semiconductor supply from Taiwan")` directly in a Python shell
- [ ] Confirm all 3 analyst outputs are non-None before judge runs
- [ ] Confirm `judge` returns valid JSON with `risk_score` as an integer
- [ ] Confirm `guardrail_report` is a dict (not a string) when saved to Postgres

**Priority 3 — GCP infra setup (needed for Day 3 deploy)**
- [ ] Create GCP project, enable APIs: Cloud Run, Cloud SQL, Cloud Storage, Secret Manager
- [ ] Create Cloud SQL PostgreSQL 16 instance — note the connection name
- [ ] Create GCS bucket (`supply-chain-risk-raw`)
- [ ] Create a service account with roles: Cloud SQL Client, Storage Object Admin
- [ ] Download service account JSON → `secrets/gcp_service_account.json` (gitignored)
- [ ] Add all GitHub Actions secrets: `GCP_SA_KEY`, `GCP_PROJECT_ID`, `CLOUD_SQL_CONNECTION_NAME`, plus all API keys

**Known gaps to address this week**
- No token length guard before sending docs to GPT-4o — long EDGAR filings could exceed context window
- RSS feed URLs need live validation (FT feed may require subscription)
- No retry logic on OpenAI API calls (rate limits will surface during testing)
- `pages/2_Results.py` sidebar doesn't clear cache after a new run is saved — user must wait 30s or refresh
