# Security Audit

**Audit date:** 2026-10-31
**Method:** Static inspection of Python, shell, Docker/Render configuration, launcher HTML/handlers, and n8n workflow. Regression tests cover selected launcher and GitHub behavior. No live service penetration test, SAST tool, or dependency vulnerability scan was available.

## Findings

| ID | Severity | Finding | Affected areas | Current status |
|---|---|---|---|---|
| SEC-01 | **High** | Public ADK Web has no application authentication or authorization. The Render service is a public web service and starts ADK on `0.0.0.0:$PORT`; a remote visitor can access agent operations, consume the configured Gemini quota, and submit candidate data. | [`start.sh`](./start.sh), [`render.yaml`](./render.yaml), ADK Web | Open; deployment blocker |
| SEC-02 | **High** | n8n webhook has no authentication setting. Any caller reaching the active webhook can trigger the workflow and use the instance's Gemini key. Candidate data supplied to the workflow may also be exposed to the n8n instance and its operators. | [`adk_hiring_agent_n8n_workflow.json`](./adk_hiring_agent_n8n_workflow.json), n8n deployment | Open; do not expose publicly |
| SEC-03 | **Medium** | Resume and job-description text is sent to Gemini through ADK/n8n with no in-app disclosure, consent gate, retention policy, deletion mechanism, or data-minimization setting. | [`agent.py`](./agent.py), [`tools_agents.py`](./tools_agents.py), n8n workflow | Open; define privacy controls before real candidate use |
| SEC-04 | **Medium** | Candidate text is untrusted prompt content. Prompt instructions now explicitly treat it as data and resist embedded instructions, but there is no schema-validated boundary or callback that filters tool requests/results. A crafted document can still influence model scoring or conversation behavior. | [`agent.py`](./agent.py), [`tools_agents.py`](./tools_agents.py), n8n prompts | Partially mitigated; adversarial evaluation remains |
| SEC-05 | **Medium** | `launcher.py` accepts user-selected API keys and writes them to `.env`. New writes are mode `0600`, values are not returned in the page, request bodies are bounded, and POST requests require a local-browser origin. However, explicitly overriding `HOST` to a public interface still exposes a configuration service with no user authentication. | [`launcher.py`](./launcher.py) | Local default hardened; keep loopback-only |
| SEC-06 | **Low** | Dependency vulnerability status is unknown. Requirements now constrain ADK to 1.x and bound requests/dotenv majors, but versions are not locked and no vulnerability scan could run. | [`requirements.txt`](./requirements.txt), [`Dockerfile`](./Dockerfile) | Open; add lock/scan in CI |

## Confirmed negative checks

- No real API key was found in tracked source or `.env.example`; `.gitignore` excludes `.env` and common credential files.
- GitHub username input is normalized and checked before constructing fixed GitHub REST and GraphQL endpoint URLs. The Python validator does not accept arbitrary URLs for fetching, so no SSRF path was confirmed in that function. The optional token is sent only to `api.github.com` over HTTPS and is not returned in tool output.
- No resume upload or filesystem path handling exists, so no path traversal or malicious-document parser vulnerability was confirmed. File parsing is unsupported rather than merely untested.
- No shell command is built from user-controlled input after removal of the old `fuser` shell call. `start.sh` uses an argument list via `exec`.
- The launcher escapes stored custom variable names, builds new form rows with DOM APIs, uses `textContent` for status output, does not echo stored secrets, and applies basic security headers.
- No committed `.env` or embedded credential was observed in the inspected tracked files. This does not establish secret cleanliness in repository history or external n8n instances.

## Exploitation scenarios and remediation

### SEC-01 — Public ADK UI without access control (High)

An unauthenticated visitor can open the deployed ADK interface, submit arbitrary prompts/resumes, invoke the configured agent, and consume the deployment's Gemini allowance. The code does not define application user identities, permissions, or per-user quotas. Put the service behind authentication and role-based authorization or keep it private; implement request limits and audit trails before public deployment.

### SEC-02 — Unauthenticated n8n webhook (High)

An external caller can POST to the workflow endpoint and initiate several model calls. Configure n8n webhook authentication or place it behind an authenticated gateway before activating it. Also restrict source networks where possible, set rate limits, and run the n8n security audit for unprotected webhooks. See [n8n security audit documentation](https://docs.n8n.io/hosting/securing/security-audit/).

### SEC-03 — Candidate data handling (Medium)

Resume and job-description text is transmitted to the model provider. The application provides no notice or controls for applicant consent, retention, deletion, access, or provider policy. Minimize personally identifying details before model calls, establish an approved data-handling policy, and do not store evaluations until access and deletion controls exist.

### SEC-04 — Prompt injection and tool control (Medium)

The prompts now say that resume and job-description contents are untrusted. This is helpful but not a security boundary. Add typed input fields, schema-validated outputs, constrained tool allowlists, after-tool validation, and adversarial tests. Do not allow any model output to trigger a hiring action.

### SEC-05 — Launcher exposure (Medium)

The launcher binds to `127.0.0.1` by default and the Render entry point no longer starts it. If an operator explicitly sets `HOST=0.0.0.0` and runs the launcher, a network user can reach the setup page. Keep it local; if remote setup is required, add authenticated TLS access rather than changing the bind address alone.

## Security posture

No Critical finding was confirmed in the source audit. The two High findings prevent public production use. The previous unauthenticated setup-launcher fallback on Render was removed, the local launcher was hardened, n8n model keys were moved out of webhook inputs and URL query strings, and the container now runs as a non-root user. These changes do not make the public ADK Web UI or n8n webhook safe to expose.
