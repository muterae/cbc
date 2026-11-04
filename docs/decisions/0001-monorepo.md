# 0001 — Single repository for mobile and server

## Context

The project has two codebases:

- `cbcapp` — an Android app (Kotlin/Compose) at `AndroidStudioProjects\cbcapp`
- `cbc-server` — a FastAPI backend at `BICS\...\Semester Project\cbc-server`

They were in unrelated folders. Only the server was under version control (3 commits); the
Android project had no Git repository at all. The two halves are tightly coupled: the mobile
data layer is written against the request/response contract documented in
`server/AGENTS.md`, and most changes touch both.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| Separate repositories | Independent history, smaller clones | Two places to look, API changes require two commits, easy to drift |
| Git submodules | Keeps each history in its own repo | Extra concept, frequent "detached HEAD" and pointer-update friction |
| **Monorepo** | One clone, one history, API contract and client change together | Both toolchains in one repo; needs a combined `.gitignore` |

## Decision

One Git repository at `Semester Project/cbc/` with `mobile/` and `server/` subdirectories.

The server's existing history was preserved with `git subtree add --prefix=server`, so its
three commits appear in the monorepo log under `server/`.

## Consequences

- Android Studio opens `cbc/mobile`; the Python tooling runs from `cbc/server`.
- The root `.gitignore` covers both toolchains, so build output, `.venv`, and `__pycache__`
  never enter the repository.
- Large source material (`server/generator/documents`, `server/generator/images_temp`, both
  over 50 MB) and the virtual environment are ignored, keeping the repo small enough to
  snapshot for submission.
- A change to the quiz contract can be made in the same commit as the mobile model that
  consumes it.
