# Comprehensive Technical Audit

**Project:** AI-Powered Conversational Hiring Agent
**Audit date:** 2026-10-31
**Scope:** All repository source, launcher, scripts, deployment configuration, documentation, and the imported n8n workflow. The pre-existing untracked `LEARNING_GUIDE.md` was inspected but not changed.

## Executive assessment

This repository is a small ADK prototype, not a production hiring system. It defines a conversational root agent, four LLM sub-agents, one GitHub profile function, an interactive local setup launcher, ADK's built-in web and CLI entry points, and a separately imported n8n workflow. It does not contain a custom hiring API, custom candidate web UI, uploaded-resume parser, repository analyzer, authentication system, or candidate-data retention policy.

The most serious production risks remain unauthenticated public access to the ADK Web UI and the unauthenticated n8n webhook. The LLM-generated resume score is not schema-validated or deterministically computed. Candidate data may be sent to Gemini without an application-level privacy notice or retention controls. Human review is now stated in the Python and n8n verdict paths, but scores and evidence still need independent verification.

### Prioritized issues

| Priority | Finding | Status |
|---|---|---|
| P0 | Public Render ADK Web UI has no application authentication or authorization; anyone who can reach it can use the agent and submit candidate data. | Open blocker |
| P0 | n8n webhook has no authentication configured and triggers paid model calls with arbitrary request data. | Open blocker |
| P1 | Resume scoring is still LLM-generated prose with no output schema, point-range validation, or deterministic scoring implementation. | Partially mitigated by prompt changes; open |
| P1 | ADK conversation orchestration relies on prompt-level sequencing and conversation context; no workflow state machine, role/rubric binding, candidate reset, or recovery tests exist. | Open |
| P1 | No repository data is fetched. The former GitHub reviewer fabricated repository observations; this is now corrected to report "Not assessed." | Fixed in Python and n8n prompts |
| P1 | The original n8n response parser classified `NO HIRE` as `HIRE` because it tested for `HIRE` first. It also returned an LLM-derived score and decision. | Fixed: output now requires human review and no score is calculated |
| P1 | n8n Gemini prompts previously instructed simulated GitHub assessments and automated hiring decisions. | Fixed in workflow prompts |
| P1 | Original shell and launcher commands passed the repository root directly to ADK discovery/run, which does not expose this project as a valid named ADK app. | Fixed with `adk_agents/hiring_agent`; verified by ADK 1.39.1 `AgentLoader` |
| P2 | No PDF/DOCX/TXT parsing or upload path exists despite the requested audit criteria; the supported input is pasted text. | Documented limitation |
| P2 | Dependency declarations were unbounded; ADK 2.x introduces a new major API generation. `google-adk` is now capped at `<2` pending an intentional migration. | Installed and runtime-discovery tested at ADK 1.39.1; dependencies are still not locked |
| P2 | Existing `LEARNING_GUIDE.md` describes a FastAPI app, simulated portfolio scoring, and final binary decisions that are not the current implementation. It is an existing untracked file and was left untouched. | Open documentation inconsistency |

## Category scorecard

Scores reflect the current repository after the changes in this audit, not a claim of production readiness.

| Category | Score / 10 | Basis |
|---|---:|---|
| Architecture | 4 | Small and understandable, but conversation-driven tool routing and external workflows are not explicit deterministic pipelines. |
| Agent orchestration | 3 | Tool wrappers are present; sequencing, state isolation, retries, and error recovery are mostly prompt-level and untested. |
| AI/LLM reliability | 3 | Model centralized and currently documented; no JSON schema validation, cost controls, fallback, or agent integration tests. |
| Evaluation accuracy | 2 | Resume score remains model-generated; GitHub repository assessment is unavailable; no validated calibration or human-review workflow exists. |
| Security | 2 | Local launcher is hardened, but the public app and n8n webhook remain unauthenticated and process candidate data. |
| Code quality | 5 | Changes improve separation, validation, and error handling; original code still has large prompts, limited types, and no service boundary. |
| Testing | 4 | 11 Python unit tests and embedded-workflow checks pass; ADK loader was verified, but live API, E2E, and broad security test coverage is absent. |
| User experience | 4 | Launcher is simple and readable; no candidate progress model, accessible error/status review, or custom results UI. |
| Deployment | 5 | Render binds `$PORT` on `0.0.0.0`; Python runtime is pinned and missing keys fail closed, but public access remains unsafe. |
| Documentation | 5 | Core setup/deployment docs corrected; an existing untracked learning guide remains stale, and test/privacy procedures are incomplete. |
| **Total** | **37 / 100** | **Not production ready** |

### Critical blockers and next milestones

1. Add authentication and authorization before exposing either ADK Web or the n8n webhook; restrict access to authorized hiring staff.
2. Replace prompt-only execution with a typed evaluation request, explicit role/rubric/candidate state, and a human review checkpoint.
3. Add schema-validated model outputs and a deterministic score calculation with documented treatment of unknown evidence.
4. Add data minimization, notice/consent, retention/deletion controls, and secure observability before processing real resumes.
5. Build integration and E2E tests against the pinned ADK version, with mocked model and GitHub services.

See [ARCHITECTURE_REVIEW.md](./ARCHITECTURE_REVIEW.md), [SECURITY_AUDIT.md](./SECURITY_AUDIT.md), [REMEDIATION_REPORT.md](./REMEDIATION_REPORT.md), [TEST_REPORT.md](./TEST_REPORT.md), and [DEPLOYMENT_READINESS.md](./DEPLOYMENT_READINESS.md) for evidence and detail.
