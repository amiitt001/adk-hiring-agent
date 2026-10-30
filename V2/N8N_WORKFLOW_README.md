# ⚡ ADK Hiring Agent - n8n Workflow Integration

This directory contains the complete **n8n workflow JSON (`adk_hiring_agent_n8n_workflow.json`)** that translates the Google ADK Hiring Agent python multi-agent pipeline (`agent.py`, `tools_agents.py`) into an automated n8n workflow.

---

## 🚀 Workflow Architecture

The n8n workflow runs a rubric, resume evidence summary, optional GitHub profile check,
and evidence summary for human review. It does not make hiring decisions.

```
                  ┌───────────────────────────────┐
                  │ Webhook / Manual Test Trigger │
                  └───────────────┬───────────────┘
                                  │
                  ┌───────────────▼───────────────┐
                  │  Prepare Input & API Keys     │
                  └───────────────┬───────────────┘
                                  │
                  ┌───────────────▼───────────────┐
                  │  Step 1: RubricBuilder (LLM)  │
                  └───────────────┬───────────────┘
                                  │
                  ┌───────────────▼───────────────┐
                  │ Step 2: ResumeReviewer (LLM)  │
                  └───────────────┬───────────────┘
                                  │
                  ┌───────────────▼───────────────┐
                  │    Has GitHub Username?       │
                  └───────┬───────────────┬───────┘
                     YES  │               │ NO
        ┌─────────────────┴─┐           ┌─┴─────────────────┐
        │ GitHub REST API   │           │ Skip GitHub Eval  │
        └────────┬──────────┘           └─┬─────────────────┘
                 │                        │
        ┌────────▼──────────┐             │
        │ Step 4: GitHub    │             │
        │ Reviewer (LLM)    │             │
        └────────┬──────────┘             │
                 └────────────────┬───────┘
                                  │
                  ┌───────────────▼───────────────┐
                  │ Step 5: VerdictSynthesizer    │
                  └───────────────┬───────────────┘
                                  │
                  ┌───────────────▼───────────────┐
                  │ Format Final JSON Response    │
                  └───────────────────────────────┘
```

---

## 📦 How to Import into n8n

1. Open your **n8n Instance** (Cloud or Self-Hosted).
2. Click **Workflows** -> **Add Workflow** (or `+` button).
3. Click the **`...`** (options menu in the top right of the canvas).
4. Select **Import from File...** and choose [`adk_hiring_agent_n8n_workflow.json`](file:///home/orion/Downloads/adk-hiring-agent-main/adk-hiring-agent-main/adk_hiring_agent_n8n_workflow.json).
5. Click **Save** (Ctrl+S / Cmd+S).

---

## 🔑 Configuration & API Keys

The workflow requires a **Google Gemini API Key** (and optionally a **GitHub Personal Access Token** for higher rate limits).

Set the API key in the n8n runtime environment. The workflow reads `GEMINI_API_KEY` from
the server environment through an n8n expression and sends it in an HTTP header. Ensure your
n8n instance permits `$env.GEMINI_API_KEY` in expressions (or configure an equivalent managed
HTTP credential). Do not include credentials in webhook payloads; n8n execution history can
retain input and node data.

Set the following environment variable in your n8n instance:
- `GEMINI_API_KEY`: Your Google Gemini API Key

The webhook currently has no authentication configured. Do not expose it to the public Internet
or send real candidate information until you configure n8n webhook authentication or place the
endpoint behind an authenticated gateway. Restrict n8n execution-data retention and access.

---

## 🧪 Testing the Workflow

### Method A: Direct UI Test (Manual Trigger)
1. Open the imported workflow in n8n.
2. Click on **Manual Test Trigger** or click **Test Step** / **Test Workflow** at the bottom.
3. The workflow will run with default sample inputs (Senior Python Engineer JD + Sample Resume for Alex Mercer).

### Method B: Via Webhook (cURL / Postman / Python)

**Endpoint:** `POST http://<your-n8n-domain>:5678/webhook/adk-hiring-agent`

**Sample cURL Request:**
```bash
curl -X POST http://localhost:5678/webhook/adk-hiring-agent \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "We are looking for a Lead Python Developer with 5+ years experience in FastAPI, Postgres, and Docker.",
    "resume": "John Doe\nSoftware Engineer\nGitHub: github.com/johndoe\n5 years experience in Python, FastAPI, Docker, and AWS.",
    "github_username": "johndoe"
  }'
```

---

## 📄 Response Output Structure

The workflow returns a clean JSON summary object:

```json
{
  "success": true,
  "candidate_name": "John Doe",
  "decision": "HUMAN_REVIEW_REQUIRED",
  "composite_score": "Not calculated",
  "summary": {
    "rubric": "...Markdown rubric...",
    "resume_evaluation": "...Level 1 Resume evaluation breakdown...",
    "github_validation": {
      "status": "PASSED",
      "public_repos": 35,
      "followers": 12
    },
    "github_evaluation": "...Level 2 GitHub portfolio evaluation...",
    "final_verdict": "...Complete Verdict Synthesizer report..."
  }
}
```
