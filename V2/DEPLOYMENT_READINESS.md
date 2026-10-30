# Deployment Readiness — Render

**Status: Not ready for public production use.** The service now starts on Render's assigned port and fails closed without a Gemini API key, but ADK Web has no application authentication or authorization. Do not expose it to the public internet or process real candidate data until access control and privacy controls are implemented.

## Configuration review

- `render.yaml` declares Python 3.11.11 and the `./start.sh` start command.
- `start.sh` requires `GEMINI_API_KEY` or `GOOGLE_API_KEY`, then executes ADK Web bound to `0.0.0.0` and `${PORT:-8080}`.
- The discovered ADK app resides under `adk_agents/hiring_agent`; its wrapper imports the root agent. ADK 1.39.1's `AgentLoader` successfully discovered it.
- The launcher is no longer used as a public Render fallback. It defaults to loopback for local setup.
- Docker uses a non-root runtime user and invokes the same startup script.
- No custom health check path is defined. Render uses its port-based service check.
- Secrets are expected from Render environment variables; no real credentials were found in tracked source during this inspection.

Render documents `PYTHON_VERSION` for selecting the Python runtime and supports environment variables/secret files for deployment secrets: [Python version](https://render.com/docs/python-version), [environment variables](https://render.com/docs/configure-environment-variables), [Blueprint specification](https://render.com/docs/blueprint-spec).

## Blocking risks and open checks

1. **Authentication:** ADK Web is public and unauthenticated. Add an authenticated gateway or application-level authentication and authorization before deploying publicly.
2. **n8n:** The separate sample workflow has an unauthenticated webhook and is not deployed by the Render service. Configure endpoint authentication and rate limits before activation.
3. **Candidate data:** Define notice/consent, data minimization, retention, deletion, and access logging before processing resumes.
4. **Build reproducibility:** Requirements are bounded but not locked. Add a tested lock/constraints file and automated vulnerability checks. `pip-audit` could not obtain advisory data due network timeouts, so the dependency status is unknown.
5. **Operational verification:** No live Render deployment, HTTP health probe, Docker image build, graceful hosted shutdown test, or production log review was performed.
6. **Model operation:** No live Gemini credential, quota, rate-limit, or provider failure path was exercised. There is no app-level fallback or cost limiter.

## Readiness verdict

The corrected startup and ADK discovery path are configuration-ready based on static inspection and local loader validation. This is not a deployment certification. Public exposure remains blocked by missing authentication, and production use remains blocked by data governance, dependency scanning, and hosted runtime verification.
