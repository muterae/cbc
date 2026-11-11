# CBC Learning Companion

An adaptive Grade 3 Mathematics learning app for Kenya's Competency-Based Curriculum (CBC).

A learner logs in with a student ID, generates a quiz, and answers it. The server predicts the
learner's competency band, retrieves the matching KICD curriculum material, and generates a
quiz at that level.

> **Current milestone:** the server onboarding path is live: fixed placement quiz,
> in-memory learner profiles, placement scoring, and profile-driven adaptive quizzes
> (`GET /api/v1/intro-quiz`, `/api/v1/profiles`, `POST /api/v1/adaptive-quiz`). It is
> grounded in 149 embedded KICD lessons and the CBC band playbook. The mobile app still
> uses its local fallback quiz; wiring it to the server is the next step.

## Repository layout

```
cbc/
├── mobile/     Android app (Kotlin + Jetpack Compose)
├── server/     FastAPI backend (Python, XGBoost, RAG, Groq)
├── docs/       Per-screen and per-decision documentation
└── README.md
```

Both projects live in one repository because they are developed and demonstrated together:
the API contract in `server/AGENTS.md` drives the mobile data layer directly.

## Mobile

- Kotlin 2.2.10, Jetpack Compose (Material 3), single-activity architecture
- Package: `ke.ac.bics.cbcapp`
- Min SDK 26, target/compile SDK 37

```bash
cd mobile
./gradlew assembleDebug        # build APK
./gradlew testDebugUnitTest    # unit tests
```

Open `mobile/` as the project root in Android Studio.

## Server

- FastAPI, Python 3.14, managed with `uv`

```bash
cd server
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
uv run pytest
```

Requires `server/.env` with `GROQ_API_KEY` and `PINECONE_API_KEY`. Set
`GROQ_MODEL` to override the default `qwen/qwen3.8-27b`.

## Documentation

- [`docs/design-system.md`](docs/design-system.md) — colours, type scale, spacing, shape
- [`docs/pages/`](docs/pages/) — one short document per screen
- [`docs/decisions/`](docs/decisions/) - why each architectural choice was made

### Decision log

| ID | Decision |
|---|---|
| [0001](docs/decisions/0001-monorepo.md) | Single repository for mobile and server |
| [0002](docs/decisions/0002-package-naming.md) | Android application ID `ke.ac.bics.cbcapp` |
| [0003](docs/decisions/0003-design-tokens.md) | Semantic colour/type tokens, ABeeZee, 30dp radius |
