# Architecture Review

## Overview

The Python application is an ADK package whose `root_agent` is loaded by ADK's web or CLI command. The root agent delegates to agent tools for rubric creation, resume review, optional GitHub evidence summary, and evidence synthesis. GitHub REST/GraphQL lookup is a Python `FunctionTool`. The browser-based hiring interface itself is ADK Web; `launcher.py` is a separate configuration page, not the candidate evaluation UI. The n8n JSON is an independent workflow and is not exposed by the Render application.

## File-by-file responsibility map

| File | Responsibility and audit notes |
|---|---|
| [`agent.py`](./agent.py) | Root conversational orchestrator, registers four agent tools and the GitHub validator function. State transitions are expressed in instructions, not code. |
| [`tools_agents.py`](./tools_agents.py) | Defines RubricBuilder, ResumeReviewer, GitHubReviewer, and VerdictSynthesizer. Prompts have been revised for job relevance, prompt-injection resistance, evidence labels, and human review. Outputs remain free-form text. |
| [`github.py`](./github.py) | GitHub REST profile lookup and optional GraphQL public contribution summary; counts public repositories, contribution types grouped by repository, and leading repository metadata. |
| [`settings.py`](./settings.py) | New shared dotenv loading, `GEMINI_API_KEY`/`GOOGLE_API_KEY` aliasing, and centralized model selection. |
| [`adk_agents/hiring_agent/`](./adk_agents/hiring_agent/) | ADK-discoverable wrapper that exposes the root agent under a valid app name; `adk web` expects an agent directory under an agents root. |
| [`launcher.py`](./launcher.py) | Local API-key setup page and process launcher. It now defaults to loopback, does not echo stored secret values, bounds JSON requests, applies CSRF origin checks, and writes `.env` with mode `0600`. It is not intended as a public deployment setup endpoint. |
| [`__init__.py`](./__init__.py) | Exposes `root_agent` for ADK package discovery. |
| [`tests/test_github.py`](./tests/test_github.py) | Unit tests for GitHub username handling and mocked success/failure/timeout conditions. |
| [`tests/test_launcher.py`](./tests/test_launcher.py) | Unit tests for secret-free page rendering and private `.env` output. |
| [`tests/test_n8n_decision.js`](./tests/test_n8n_decision.js) | Executes n8n Code-node JavaScript in Node and checks human-review output, missing input, credential handling, and script syntax. |
| [`requirements.txt`](./requirements.txt) | Runtime dependencies. `google-genai` was removed as a direct dependency because repository code does not import it; ADK supplies its provider dependency. ADK is capped below 2 pending migration tests. |
| [`run.sh`](./run.sh) | Local venv setup and launcher/web/CLI entry points. Adds a Python 3.10 check and respects process environment API keys. |
| [`start.sh`](./start.sh) | Render/container entry point. Requires a configured API key and runs ADK on `$PORT` at `0.0.0.0`; no public setup launcher fallback. |
| [`Dockerfile`](./Dockerfile) | Python 3.11 image; installs Python requirements, copies app, runs as a non-root user, and invokes `start.sh`. |
| [`render.yaml`](./render.yaml) | Render Python web service, environment configuration, pinned Python 3.11.11, and start command. No custom HTTP health path is configured. |
| [`.env.example`](./.env.example) | Placeholder Gemini, model, and optional GitHub settings; contains no real credentials. |
| [`.gitignore`](./.gitignore) | Excludes `.env`, credential files, local data, virtual environments, and generated files. |
| [`.dockerignore`](./.dockerignore) | Excludes secrets, Git metadata, virtual environments, and ADK local state from Docker context. |
| [`pyrightconfig.json`](./pyrightconfig.json) | Pyright workspace configuration; disables `reportGeneralTypeIssues`, reducing the usefulness of type diagnostics. |
| [`adk_hiring_agent_n8n_workflow.json`](./adk_hiring_agent_n8n_workflow.json) | Separate webhook/manual workflow, Gemini HTTP requests, optional GitHub lookup, and output formatter. It has no configured webhook authentication. Decision output is now fixed to `HUMAN_REVIEW_REQUIRED`. |
| [`README.md`](./README.md) | Main installation, configuration, and limitation guide; updated to match actual functionality. |
| [`RENDER_DEPLOYMENT.md`](./RENDER_DEPLOYMENT.md) | Render setup guidance; updated to require a dashboard secret and describe the second-port failure in the former fallback. |
| [`INTEGRATION_GUIDE.md`](./INTEGRATION_GUIDE.md) | Integration instructions; corrected to distinguish Render ADK Web from the separately hosted n8n webhook. |
| [`N8N_WORKFLOW_README.md`](./N8N_WORKFLOW_README.md) | n8n workflow setup and output documentation; now warns about missing endpoint authentication and execution data. |
| [`LEARNING_GUIDE.md`](./LEARNING_GUIDE.md) | Pre-existing untracked learning document. It claims FastAPI, simulated repository scoring, and binary hiring decisions that do not match the implementation. Left unchanged to preserve pre-existing user data. |
| [`LICENSE`](./LICENSE) | MIT license. |
| [`PROPOSED_REMEDIATION.md`](./PROPOSED_REMEDIATION.md) | Plan recorded before source changes, including scope boundaries and validation intent. |
| `.agents/`, `.codex/` | Empty directories at audit time. |

Generated `__pycache__` files were excluded from the source inventory; they are ignored and are not runtime source.

## Agent dependency graph

```mermaid
flowchart TD
    U[Recruiter] --> R[Root LlmAgent]
    R --> RB[RubricBuilder LlmAgent]
    R --> RR[ResumeReviewer LlmAgent]
    R --> GV[GitHubValidator FunctionTool]
    R --> GR[GitHubReviewer LlmAgent]
    R --> VS[VerdictSynthesizer LlmAgent]
    GV --> GH[GitHub REST profile /users/{username}]
    GV --> GQL[GitHub GraphQL public contribution groups]
    RB --> G[Gemini via ADK]
    RR --> G
    GR --> G
    VS --> G
    R --> G
    R --> O[ADK Web or ADK CLI]
```

Rubric output and candidate evidence move through conversation context rather than typed, versioned request objects. The flow is therefore dependent on the orchestrator accurately tracking conversational state. There is no explicit rubric ID or enforced reuse across candidates.

## Request-to-response flow

1. `adk web adk_agents` discovers `adk_agents/hiring_agent/agent.py`, which imports the root agent. `adk run adk_agents/hiring_agent` uses the valid ADK app name `hiring_agent`. Both paths were validated using the installed ADK 1.39.1 loader; the prior root-directory invocation was not a valid app-discovery path.
2. The root agent requests a job description and invokes RubricBuilder.
3. The rubric text is shown and the agent requests resume text.
4. ResumeReviewer reads the rubric and resume from the conversation and produces a free-form assessment.
5. If a profile is supplied, the root calls `github_validator`; the function normalizes the input and makes a bounded GET to the REST profile endpoint. It reports the API's public repository count. With `GITHUB_TOKEN`, it also makes one bounded GraphQL request for public commit, pull request, issue, and review contribution counts grouped by repository over the prior 365 days. It reports the leading repository by combined event count and by commit count. Without a token or when the query fails, the profile remains verified and contribution details are explicitly unavailable.
6. When asked, VerdictSynthesizer summarizes evidence and human-review questions. It must not make a hiring decision.
7. ADK returns its response through its Web UI or CLI. In the tested ADK 1.39.1 version, default storage is local `.adk` storage unless session/artifact services are configured; no explicit production storage policy is configured here.

Separately, the n8n workflow receives a webhook request (currently without authentication) or manual test event, creates a rubric, evaluates resume text, optionally checks a GitHub profile, and returns a JSON summary. The n8n output formatter does not calculate scores or hiring decisions.

## External API dependencies

| Consumer | Service | Calls/data | Failure handling |
|---|---|---|---|
| ADK agents | Gemini API through Google ADK | Job description and resume/profile evidence are model context. | No application-defined retry, fallback, or structured response validation. |
| `github.py` | GitHub REST + GraphQL APIs | REST profile/public repository count; optional GraphQL public contribution types grouped by repository for the last 365 days. Uses optional `GITHUB_TOKEN` and bounded timeouts. | A GraphQL failure leaves profile verification intact and marks contribution evidence unavailable. Private repositories are excluded from the returned breakdown. |
| `launcher.py` | Gemini model-list endpoint | Tests a user-provided API key via `x-goog-api-key` request header. | Timeout and generic network error handling; no retry. |
| n8n workflow | Gemini REST endpoint | Four model calls, key read from n8n environment expression in an HTTP header. | HTTP nodes use `neverError`; non-success result interpretation remains weak. |
| n8n workflow | GitHub REST API | Public user-profile endpoint, no repository data. | Error payload currently has no robust status-code normalization. |

## Existing gaps

- No resume parser, MIME validation, file size control for resume files, or upload functionality.
- No API service contract, data model, score schema, or deterministic score aggregation.
- No authenticated application users, tenant/role controls, or candidate record lifecycle.
- No repository-list/content/commit retrieval; repository quality and activity cannot be assessed.
- No explicit session/rubric/candidate isolation or cross-candidate reset tests.
- No tool-call state machine, retry policy, model fallback, rate limiter, or cost budget.
- No generated report storage or audit record describing model, rubric version, prompt version, and source evidence.
- ADK package loading was tested with ADK 1.39.1, but no live Gemini request, ADK web server, browser flow, or complete evaluation end-to-end test was run.
