# Remediation Report

## Implemented

### Model configuration and dependencies

- Added [`settings.py`](./settings.py) as the single Python source for dotenv loading, API-key aliasing, and `MODEL_NAME`.
- Kept the default `gemini-3.5-flash` after checking Google's model catalogue: it is listed as a supported stable legacy model, so it is not currently an invalid identifier. Model IDs remain deployment-configurable. See [Gemini model documentation](https://ai.google.dev/gemini-api/docs/models).
- Removed `google-genai` as a direct dependency because source code does not import it. Bounded the requests and dotenv major versions and capped `google-adk` below 2 because ADK 2.x is a major API generation; migrate only with runtime tests. Installed requirements in a temporary environment and verified Google ADK 1.39.1 on Python 3.12.3. The current Google ADK package requires Python 3.10+; the shell entry point now checks this.

### Candidate evaluation quality

- Rewrote rubric and resume prompts to use explicit role requirements, a candidate-independent rubric, no protected or irrelevant traits, evidence citations, unknown/unscored evidence handling, and no autonomous employment recommendation.
- Rewrote the GitHub reviewer prompt to distinguish returned public metadata from source-code, testing, documentation, authorship, and quality assessment. It no longer fabricates evidence or scores.
- Rewrote the verdict prompt to summarize evidence and human-review questions without HIRE/NO HIRE, candidate ranking, composite score, or compensation guidance.
- Updated root-agent wording and product documentation to describe decision support and the actual supported text-only interface.

### GitHub integration

- Added [`github.py`](./github.py) and delegated the function tool to it.
- Validates usernames and GitHub profile URLs, sends the optional token using the `Bearer` scheme, applies connect/read timeouts, distinguishes 404 from rate limits and network failures, rejects malformed success responses, and avoids including raw exception text in output.
- Reports the public repository count from the REST profile response. When `GITHUB_TOKEN` is configured, one GraphQL request returns last-365-day public commit, pull request, issue, and review counts grouped by up to 100 repositories, plus the leading repository by combined contribution-event count and by commit count. GraphQL failure leaves profile validation intact and contribution evidence unavailable.
- Removed age, completeness, repository count, and follower count as quality judgments. A profile with no repositories remains a verified profile, not a warning about candidate ability.

### Launcher, shell, and deployment

- [`launcher.py`](./launcher.py) now binds to loopback by default, no longer includes stored secrets in HTML, marks secret fields as leave-blank-to-keep, uses bounded JSON requests, applies local-origin checks to POSTs, constrains custom environment key names, avoids raw exception responses, and writes `.env` atomically with mode `0600`.
- Removed wildcard `--allow_origins "*"` and shell-based port killing. The child process no longer uses unread stdout/stderr pipes and is terminated with a timeout/kill fallback.
- [`start.sh`](./start.sh) now fails closed without a deployment API key rather than exposing the interactive setup launcher on Render. It uses Render's assigned `$PORT` and `0.0.0.0`.
- [`render.yaml`](./render.yaml) pins Python 3.11.11, following Render's version configuration guidance; [`Dockerfile`](./Dockerfile) runs as non-root and no longer installs unused `curl`, `git`, and `procps` system packages.
- [`run.sh`](./run.sh) checks Python 3.10+ and recognizes process environment API keys as well as `.env`.
- Added `adk_agents/hiring_agent/` because ADK Web discovers apps under an agents root; the former `adk web .` / `adk run .` invocations did not identify this repository as a valid ADK app. Verified the wrapper with ADK 1.39.1's real `AgentLoader` and confirmed all five root tools load.

### n8n workflow

- Removed the false `HIRE` parser and score extraction. Output is always `HUMAN_REVIEW_REQUIRED` with no calculated composite score.
- Fixed malformed candidate-name regular-expression code discovered by compiling the embedded JavaScript.
- Updated prompts to prohibit simulated GitHub assessment and autonomous hiring decisions.
- Moved Gemini credentials out of webhook input and URL query parameters; the HTTP request nodes use an n8n environment expression in an API-key header. The key is no longer carried in the workflow item data.
- Webhook requests without a job description or resume now fail instead of silently using sample candidate data. Manual trigger samples remain available.
- Updated integration and workflow docs to warn that the sample webhook has no authentication configured.

## Pending work, ordered by risk

1. **Add user authentication and authorization** to ADK Web and secure the n8n endpoint. Until then, do not expose these interfaces to public users or real candidate data.
2. **Add typed schemas and deterministic scoring**: validate rubric weights and criterion scores; compute totals in code; reject malformed or out-of-range output; preserve unknown evidence explicitly.
3. **Add explicit workflow state and session isolation**: role/rubric identifiers, candidate resets, controlled tool transitions, per-run context limits, and recovery behavior.
4. **Implement source-level repository review** only if justified: fetch bounded selected public content, verify candidate-selected project relevance, cite source locations, treat private/unavailable evidence as unknown, and remove activity/volume penalties. Current counts do not establish authorship or skill.
5. **Set candidate-data policy**: notice, consent, data minimization, retention/deletion, access logging, and provider approval.
6. **Add ADK integration/E2E tests** for tool calls, session persistence/isolation, invalid model/key handling, retries, prompt injection, and no-GitHub paths.
7. **Lock dependency resolution and scan it in CI**. Installation and runtime compatibility were verified for ADK 1.39.1, but dependencies remain ranges and the vulnerability scanner could not reach its advisory service.
8. **Repair stale, pre-existing [`LEARNING_GUIDE.md`](./LEARNING_GUIDE.md)** once its untracked status is resolved; it currently documents nonexistent FastAPI and binary-decision behavior.

## Trade-offs

- The app remains on Google ADK and the existing CLI/Web surfaces. A custom authenticated web service would be a substantial architecture change; it is called out as a blocker rather than introduced without an approved design.
- GitHub contribution counts are descriptive evidence, not repository quality or candidate scores. Source-level repository review remains unimplemented.
- `google-adk<2` is a compatibility guard. A temporary environment verified requirements installation, package consistency, root-agent import, and ADK app discovery with ADK 1.39.1. Gemini calls and a live ADK server were not exercised.
