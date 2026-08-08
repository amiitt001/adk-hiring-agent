# 🔌 How to Integrate the ADK Hiring Agent into Any Project

This guide explains how external applications (Web Apps, HR Portals, ATS Systems, Python backends, or Low-Code workflows) can easily use the **AI Hiring Agent feature**.

---

## 🎯 Integration Options Overview

| Integration Method | Best For | Prerequisites | Output Format |
|---|---|---|---|
| **1. REST API / Webhook (n8n or Render)** | Web apps (Node.js, React, Python, PHP, Go), Mobile Apps, ATS | Webhook URL | JSON Summary |
| **2. Python Package / Code Import** | Python backends (FastAPI, Django, Flask, LangChain) | Python 3.8+ & `google-adk` | Python objects / string reports |
| **3. Low-Code Automations (n8n)** | Slack, Google Forms, Greenhouse, Airtable, Notion, Email | n8n instance | Triggered workflows |

---

## 🌐 Option 1: Integrate via Webhook / REST API (Any Language)

If you deployed the workflow to Render or imported `adk_hiring_agent_n8n_workflow.json` into n8n, any app can evaluate candidates by making an HTTP POST request.

### Node.js / JavaScript (Fetch / Axios)
```javascript
async function evaluateCandidate(jobDescription, resumeText, githubUsername) {
  const response = await fetch('https://your-n8n-or-render-app.com/webhook/adk-hiring-agent', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      gemini_api_key: process.env.GEMINI_API_KEY,
      job_description: jobDescription,
      resume: resumeText,
      github_username: githubUsername
    })
  });

  const result = await response.json();
  console.log("Hiring Decision:", result.decision); // "HIRE" or "NO HIRE"
  console.log("Score:", result.composite_score);     // e.g. "8.5/10"
  console.log("Full Report:", result.summary.final_verdict);
  return result;
}
```

### Python (requests / httpx)
```python
import requests

def evaluate_candidate(job_description: str, resume: str, github_username: str = ""):
    url = "https://your-n8n-or-render-app.com/webhook/adk-hiring-agent"
    payload = {
        "job_description": job_description,
        "resume": resume,
        "github_username": github_username
    }
    response = requests.post(url, json=payload)
    return response.json()
```

---

## 🐍 Option 2: Direct Import in Python Projects

If your project is built in Python, you can import `agent.py` and `tools_agents.py` directly into your codebase.

1. **Install requirements:**
   ```bash
   pip install google-adk google-genai python-dotenv requests
   ```

2. **Call sub-agents in Python code:**
   ```python
   from tools_agents import (
       rubric_builder,
       resume_reviewer,
       github_validator,
       github_reviewer,
       verdict_synthesizer
   )

   # Step 1: Validate GitHub Account
   github_data = github_validator(username="octocat")
   print("GitHub Valid:", github_data["status"])

   # Step 2: Use Root Orchestrator Agent
   from agent import root_agent
   ```

---

## ⚡ Option 3: Connect to HR Tools & Forms (Greenhouse, Slack, Google Forms)

Using the **n8n Workflow (`adk_hiring_agent_n8n_workflow.json`)**, you can automatically trigger candidate evaluations:

1. **Google Forms / Typeform**: Automatically trigger evaluation whenever a job applicant submits a resume link.
2. **Slack Bot**: Post candidate evaluation reports (`🟢 HIRE` / `🔴 NO HIRE`) directly to a `#hiring-channel`.
3. **ATS Systems (Greenhouse / Lever / Workable)**: Auto-evaluate incoming resumes and attach scores directly to the candidate card.
