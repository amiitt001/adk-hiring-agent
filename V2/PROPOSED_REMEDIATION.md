# Proposed Remediation Plan

This plan records the intended changes before implementation, following the audit request. The repository has no established test suite, no structured service/API layer, and no separate resume upload flow. The plan preserves Google ADK and the existing command-line, ADK web, launcher, and n8n integration surfaces.

## Confirmed scope

1. Add the six requested audit deliverables with architecture mapping, file responsibilities, dependency flow, findings, evidence, severity, readiness scorecard, and actual validation status.
2. Add a small regression test suite using mocks for GitHub HTTP calls and launcher behavior; standard tests will not call Gemini or GitHub.
3. Correct the confirmed GitHub-review prompt defect: it explicitly fabricates portfolio findings and penalizes account age, repository quantity, and activity. Treat GitHub as optional, observable evidence only; report unavailable data as unknown.
4. Correct the verdict prompt so it cannot make an autonomous hire/no-hire decision, infer protected or irrelevant traits, invent facts, assign penalties to missing evidence, or synthesize unsupported numeric scores. Require human review and traceable evidence.
5. Centralize Gemini model configuration and use the currently documented default only after checking official model documentation; remove stale model choices/defaults from configuration surfaces.
6. Improve GitHub validator correctness: use GitHub's current token scheme, validate parsed usernames, keep HTTP failures distinct from missing users, handle malformed responses and date parsing, and avoid returning raw network exception details that could contain request data.
7. Harden the launcher within its existing design: bound request body size, use a threaded server, prevent public GET responses from echoing saved secrets, escape dynamic HTML, constrain custom environment key names, avoid logging/returning secret-bearing errors, set restrictive `.env` permissions where supported, and cleanly shut down child processes. Preserve the interactive local setup flow.
8. Fix or clearly document deployment behavior where the current Render fallback starts a second port that Render does not route, and keep the direct configured-secret startup on Render's assigned port. Add a health check path to the blueprint.
9. Update setup/deployment documentation and dependency declarations only when installed/runtime compatibility is verified.

## Boundaries and trade-offs

- A secure public, multi-tenant hiring service requires authentication, authorization, candidate-data retention controls, and a proxied/session-aware web architecture. That is a substantial product architecture change and is not included in this pass; the reports will mark public exposure of the current unauthenticated ADK UI/launcher as a deployment blocker.
- The current launcher’s two-port setup flow cannot be made reliably reachable on Render without a proxy or service redesign. This pass will avoid pretending that a second port is exposed and will document/adjust the safe deploy path.
- The n8n workflow is a separately imported product surface, not the Render app. Its webhook currently accepts credentials and candidate data directly and makes LLM calls; it will be audited and documented, while invasive workflow redesign remains separate.
- No resume file parsing/upload implementation exists in the inspected repository. The current interface accepts conversation text; PDF/DOCX claims in the requested audit will be reported as unsupported rather than fabricated.

## Validation to perform

- Inspect every tracked and untracked non-generated repository file (without changing pre-existing untracked files).
- Run syntax/JSON validation, focused unit tests with mocked external calls, and available static/dependency checks; record missing tools and actual results.
- Verify current model naming against official Google documentation and Render binding/health-check expectations against official Render documentation.
