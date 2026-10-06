# Bite Buddy NYC 🍜

A chat agent for young, indecisive NYC diners. It asks what you're craving,
which borough you're in, your budget and where you're starting from, then
finds a place and tells you how to get there.

## Project layout

| File | What it does |
|---|---|
| `main.py` | FastAPI server. `POST /chat` returns `{response, session_id, tool_calls}`; `GET /` serves the UI |
| `agent.py` | Gemini chat loop: system prompt, per-session memory, runs tools and records each call |
| `tools.py` | The 5 tools (**stubs with fake data for now**). Add new tools to the `TOOLS` registry at the bottom |
| `static/index.html` | Placeholder UI that shows tool calls. Redesign it |
| `Dockerfile` | Container image for Cloud Run |

## 1. Run locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then paste your key from https://aistudio.google.com/apikey
uvicorn main:app --reload --port 8080
```

Open http://localhost:8080 and try "I want cheap ramen in Manhattan".

Test the API directly:

```bash
curl -X POST localhost:8080/chat -H 'content-type: application/json' \
  -d '{"message": "surprise me in Brooklyn"}'
# send the returned session_id with the next message to keep the conversation
```

## 2. Replace the stubs, one tool at a time

Ideas for real data sources:

- `search_restaurants` / `surprise_pick`: Google Places API (Text Search), Yelp
  Fusion, or NYC Open Data's restaurant inspection dataset (free, no key).
- `get_subway_trip`: Google Maps Directions API with `mode=transit`.
- `estimate_total_cost`, `suggest_cuisines`: pure Python, no API needed.

Rules from lecture to keep:

- The docstring and argument descriptions are what the model reads, so make them clear.
- Don't raise. Return `{"error": "<what went wrong + what to do>"}`.
- Always use `timeout=` on HTTP requests and catch `requests.RequestException`.

## 3. Deploy to Cloud Run

One-time setup:

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

Deploy from source. Cloud Build uses the Dockerfile:

```bash
gcloud run deploy nyc-food-agent \
  --source . \
  --region us-east1 \
  --allow-unauthenticated \
  --max-instances 1 \
  --set-env-vars GEMINI_API_KEY=YOUR_KEY,GEMINI_MODEL=gemini-2.5-flash
```

The command prints a public URL. Redeploy with the same command after changes.

> **Why `--max-instances 1`?** Conversation memory lives in a Python dict in
> one container. If Cloud Run started a second instance, a user could land on
> it and lose their history. One instance is fine for a class project.
> Memory also resets on redeploy or when an idle instance shuts down.

For a cleaner setup, store the key in Secret Manager and pass
`--set-secrets GEMINI_API_KEY=gemini-key:latest` instead of `--set-env-vars`.
