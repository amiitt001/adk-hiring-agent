# ADK Hiring Agent

This repository keeps the original V1 snapshot and the actively maintained V2 implementation side by side. V1 is preserved from the original commit; new changes belong in [`V2/`](./V2/).

## Choose a version

| | V1 | V2 |
|---|---|---|
| Purpose | Original reference implementation | Audited, actively maintained implementation |
| Source | Exact snapshot of original tracked commit `7232ba3` | Current audited code, tests, deployment files, and reports |
| Agent behavior | Original prompts and orchestration, including its original limitations | Human-review decision support, more cautious evidence handling, and no fabricated GitHub repository assessments |
| GitHub | Original profile integration | Bounded profile validation; repository-level quality remains unassessed |
| Security | Original behavior | Hardened local launcher and deployment startup; public app authentication remains a blocker |
| Tests | None in the original baseline | Mocked GitHub and launcher tests, ADK discovery check, and n8n formatter checks |

See the [version architecture comparison](./V2/VERSION_COMPARISON.md), [V2 architecture review](./V2/ARCHITECTURE_REVIEW.md), and [audit scorecard](./V2/AUDIT_REPORT.md) for details. V2 is not production-ready: public ADK Web and the sample n8n webhook have no authentication.

## Prerequisites

- Python 3.10 or newer for the current Google ADK dependency range.
- A Gemini API key. Do not commit `.env`, API keys, or GitHub tokens.
- Optional GitHub token for a higher API rate limit.

## Run V1

V1's original files and README are preserved without source edits in [`V1/`](./V1/). Use a separate virtual environment and environment file:

```bash
cd V1
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env to set GEMINI_API_KEY (and optional GITHUB_TOKEN).
adk run .
```

V1's original README also documents its launcher and Web mode. Those original instructions are retained as part of the baseline; see the [V1 README](./V1/README.md). On current ADK, CLI app discovery is verified for the V1 directory. The original Web command has not been verified as independently discoverable and should be treated as a legacy limitation.

## Run V2

```bash
cd V2
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env to set GEMINI_API_KEY (and optional GITHUB_TOKEN).
./run.sh web
```

For the CLI, run `./run.sh cli`. The local launcher is available with `./run.sh launcher`; it binds to loopback by default. More details are in the [V2 README](./V2/README.md).

V1 and V2 use independent requirements, scripts, and `.env` files. Their default web ports differ in the provided scripts: V1 uses its original 8080 web port and V2 uses 8080 as well, so change one port if running both simultaneously.

## Repository and release history

- Root Git history is preserved. Tag `v1.0.0` points to original commit `7232ba3`.
- Branch `v2-development` is the active V2 development line.
- V1 and V2 share this repository's Git history; V1 is a source snapshot, not a nested Git repository.
- V2 milestones should be tested, reviewed, committed, pushed, and checked against the remote before they are described as synchronized.
- No V2 beta or stable release tag has been created.

## Known limitations

- V2 does not parse uploaded PDF, DOCX, or TXT files; resume content is supplied as text.
- V2 does not fetch repository contents, commit history, or project quality evidence.
- Evaluation still relies on free-form model output; there is no calibrated scoring model or deterministic score aggregation.
- There is no application authentication, authorization, candidate data retention/deletion workflow, or production session store.
- V1 contains the original behavior and documentation as-is, including known inaccuracies and legacy setup limitations.

## License

See [`LICENSE`](./LICENSE).
