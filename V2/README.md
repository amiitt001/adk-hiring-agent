# V2 — Audited ADK Hiring Agent

V2 is the actively maintained implementation. It is isolated from the preserved V1 source snapshot. This is decision-support software; it must not make or trigger final employment decisions.

## Setup

Requires Python 3.10+, a Gemini API key, and optionally a GitHub token.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) in `.env`. Set `MODEL_NAME` to a supported Gemini model if you want to override the default. Never commit `.env` or real credentials.

## Run

```bash
./run.sh web       # ADK Web at http://localhost:8080
./run.sh cli       # ADK command-line interface
./run.sh launcher  # local-only API-key setup UI at http://localhost:8888
```

For the production-style container/Render entry point, `start.sh` requires the API key in the process environment and binds ADK Web to `0.0.0.0:$PORT`. Do not expose it publicly until authentication and authorization are added. The launcher is for local setup only.

## Tests

With dependencies installed, run:

```bash
python -m unittest discover -s tests -v
node tests/test_n8n_decision.js
```

These tests use mocked GitHub responses and do not require Gemini credentials. See [TEST_REPORT.md](./TEST_REPORT.md) for tested scope and gaps.

## V2 architecture and limitations

- Root agent and agent tools are defined in `agent.py` and `tools_agents.py`.
- `adk_agents/hiring_agent/` provides the ADK Web app discovery wrapper.
- GitHub validation is limited to public profile metadata; repositories are not reviewed.
- Resume and job description are text inputs; file upload/parsing is not implemented.
- Scoring is still free-form LLM output and is not schema-validated or deterministically aggregated.
- Authentication, authorization, candidate-data lifecycle controls, model rate limits, and full evaluation E2E tests remain outstanding.

See the [audit report](./AUDIT_REPORT.md), [security audit](./SECURITY_AUDIT.md), [architecture review](./ARCHITECTURE_REVIEW.md), [remediation report](./REMEDIATION_REPORT.md), and [deployment readiness review](./DEPLOYMENT_READINESS.md).
