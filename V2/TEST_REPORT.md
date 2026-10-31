# Test and Validation Report

**Audit date:** 2026-10-31
**Environment:** Python 3.12.3, temporary virtual environment, `google-adk` 1.39.1. Tests use mocked GitHub responses; no Gemini credentials or live API calls are needed.

## Results

| Check | Result | Notes |
|---|---|---|
| `python -m unittest discover -s tests -v` | **PASS — 16 tests** | ADK app discovery (1), GitHub REST/GraphQL validation/error cases (12), launcher secret/config cases (3). |
| `node tests/test_n8n_decision.js` | **PASS** | Embedded Code-node syntax and response behavior, missing inputs, and credential handling. |
| `python3 -m compileall -q .` | **PASS** | Python files compile. |
| `bash -n run.sh start.sh` | **PASS** | Shell syntax. |
| JSON parse of n8n workflow | **PASS** | Workflow file is valid JSON. |
| `python -m pip check` | **PASS** | No broken installed requirements in the temporary environment. |
| `git diff --check` | **PASS** | No whitespace errors in tracked changes. |
| `pip-audit -r requirements.txt` | **NOT COMPLETED** | PyPI and OSV advisory service requests timed out, including an escalated retry. Vulnerability status remains unknown. |
| Ruff / Pyright | **NOT RUN** | Tools are not installed; no network-dependent setup was attempted. |
| Live Gemini tests | **NOT RUN** | No credentials were used; the normal suite is offline/mocked. |
| Live ADK server, browser E2E, Docker build, Render deploy | **NOT RUN** | Runtime app discovery was validated, but socket binding, image build, and hosted deployment were outside this validation. |

## Coverage and limits

Unit coverage focuses on GitHub input and mocked REST/GraphQL success/failure handling, launcher handling of secrets, ADK agent discovery, and n8n output formatting. There are no dedicated tests for model output schemas, rubric scoring consistency, orchestration/session isolation, full candidate evaluation, accessibility, authenticated access, or real service retry behavior. The workflow JavaScript test does not prove n8n deployment compatibility or webhook security.

The Python suite is run using `google-adk` 1.39.1 and the project's declared dependencies. Test doubles cover GitHub requests; no external API is contacted. Passing these checks does not establish hiring validity, security against adversarial resumes, or production readiness.
