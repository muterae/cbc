# CBC Learning Companion

An adaptive Grade 3 Mathematics learning app for Kenya's Competency-Based Curriculum (CBC).

A learner logs in with a student ID, generates a quiz, and answers it. The server predicts the
learner's competency band, retrieves the matching KICD curriculum material, and generates a
quiz at that level.

> **Current milestone:** mobile UI, running against a local fallback quiz. The server's quiz
> generation endpoint is still a stub, so the app will switch from the fallback to the real
> network call once that route is implemented.

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
```

Requires `server/.env` with `GROQ_API_KEY` and `PINECONE_API_KEY`.

## Documentation

- [`docs/decisions/`](docs/decisions/) — why each architectural choice was made
- [`docs/pages/`](docs/pages/) — one document per screen, written as the screen is built

### Decision log

| ID | Decision |
|---|---|
| [0001](docs/decisions/0001-monorepo.md) | Single repository for mobile and server |
| [0002](docs/decisions/0002-package-naming.md) | Android application ID `ke.ac.bics.cbcapp` |
