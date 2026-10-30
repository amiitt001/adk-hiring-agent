# ⚡ ADK Hiring Agent - n8n Workflow Integration

This directory contains the complete **n8n workflow JSON (`adk_hiring_agent_n8n_workflow.json`)** that translates the Google ADK Hiring Agent python multi-agent pipeline (`agent.py`, `tools_agents.py`) into an automated n8n workflow.

---

## 🚀 Workflow Architecture

The n8n workflow orchestrates 5 specialized AI evaluation steps:

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

You can supply the API keys in one of 3 ways:

### Option 1: Via Webhook Payload (Easiest)
Pass `"gemini_api_key"` directly in your POST request body.

### Option 2: Via n8n Environment Variables
Set the following environment variable in your n8n instance:
- `GEMINI_API_KEY`: Your Google Gemini API Key
- `GITHUB_TOKEN`: (Optional) Your GitHub Personal Access Token

### Option 3: Hardcode / Default Node Parameters
In the **Prepare Input & API Keys** node, replace `process.env.GEMINI_API_KEY` with your key string.

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
    "gemini_api_key": "YOUR_GEMINI_API_KEY",
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
  "decision": "HIRE",
  "composite_score": "8.5/10",
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
