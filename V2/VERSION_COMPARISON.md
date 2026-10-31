# V1 and V2 Architecture Comparison

| Area | V1 — original snapshot | V2 — active implementation |
|---|---|---|
| Source of truth | Exact copy of files tracked at original commit `7232ba3`, tagged `v1.0.0` | Audited copy isolated under `V2/`; future feature work belongs here |
| Entrypoint | Original top-level `agent.py`, launcher, scripts, and ADK commands | ADK app wrapper at `adk_agents/hiring_agent`; `run.sh` selects Web, CLI, or setup launcher |
| Orchestration | Prompt-led conversational sequencing with LLM sub-agents | Still prompt-led and free-form; prompts now require evidence and human review, but no workflow state machine exists |
| Resume evaluation | Original prompt and claims | Revised prompt treats resume text as untrusted evidence and does not treat missing evidence as proof of inability |
| GitHub | Profile validation plus a reviewer prompt that could imply repository evidence it did not retrieve | Public repo count and optional one-year public contribution breakdown by repo; source content/quality remain unassessed |
| Verdict | Original automated recommendation behavior | Evidence summary only; no HIRE/NO HIRE, ranking, or synthetic total score |
| Configuration | Original dependency declarations and launcher behavior | Central model/API-key configuration, bounded dependencies, hardened local launcher |
| Deployment | Original launcher fallback and wildcard CORS configuration | Key required before startup; assigned port used; non-root Docker runtime; authentication is still absent |
| Tests | No test suite in the baseline | 11 Python tests, ADK loader test, and n8n formatter tests; no full LLM or hosted E2E tests |

## Independence and preservation

V1 was extracted from Git commit `7232ba3`; all 19 files tracked by that commit match the snapshot byte-for-byte. V1 files were not edited. The repository's Git history remains at the root, and tag `v1.0.0` points to the original commit. V2 contains its own runtime requirements, `.env.example`, scripts, source, tests, and docs. V2 does not import V1 modules.

## Execution

- V1: from `V1/`, install `requirements.txt`, configure `V1/.env`, then use the original CLI with `adk run .`. Its original web command is retained but has not been validated as a dedicated app directory on current ADK.
- V2: from `V2/`, install `requirements.txt`, configure `V2/.env`, then run `./run.sh web` or `./run.sh cli`.

Both Web modes default to port 8080; select a different port for one version if running them simultaneously. Neither public web surface should be exposed without authentication.
