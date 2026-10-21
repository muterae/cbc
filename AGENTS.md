# AGENTS.md — System Specification & Agent Architecture

This document defines the architecture, agentic components, data flows, and development protocols for the **CBC Grade 2 AI-Driven Learning Companion**.

---

## 1. System Vision & Architecture

The system delivers automated, curriculum-grounded, adaptive learning for Grade 2 Mathematics under Kenya's Competency-Based Curriculum (CBC / KICD standard). It operates under a **hybrid intelligence paradigm**:

1. **Deterministic / Predictive Layer (ML):** Evaluates learner telemetry and historical data to classify student performance into CBC competency bands in $<5\text{ ms}$.
2. **Context Retrieval Layer (RAG):** Extracts grounded curriculum requirements, learning outcomes, and assessment rubrics from vector storage.
3. **Generative / Evaluator Layer (LLM):** Synthesizes structured, pedagogically bounded quizzes and diagnostic summaries tailored to the student's evaluated band.

### Component Topology

```
[Kotlin Mobile Client]
       │
       │ (HTTP POST: Telemetry, Session State, Learner Profile)
       ▼
[FastAPI Server Engine]
   ├── [Predictive Classifier Agent] (In-memory XGBoost Bundle via Joblib)
   │     └── Output: Competency Band [BE, AE, ME, EE]
   │
   ├── [Curriculum Retrieval Agent] (Pinecone Vector DB + MiniLM Embeddings)
   │     └── Output: KICD Design Excerpts, Learning Outcomes, Sub-strand Rubrics
   │
   └── [Adaptive Synthesis Agent] (Groq API: Llama 3.1 / Gemma 2)
         └── Output: Validated Strict JSON (Questions, Options, Hints, Diagnostics)
       │
       ▼
[Kotlin Mobile Client] (Renders Adaptive Quiz UI)
```

---

## 2. Agent Roles & Specifications

### Agent 1: The Predictive Classifier (Telemetry Evaluator)
* **Type:** Supervised Tabular Ensemble (`XGBClassifier` wrapped in `scikit-learn.pipeline.Pipeline`).
* **Runtime:** In-memory on CPU within the FastAPI process lifecycle (`lifespan` handler).
* **Latency Profile:** $<5\text{ ms}$.
* **Artifact:** `cbc_predictor_bundle.pkl`.

#### Input Schema
* **Numerical Features:**
  * `StudyHoursPerWeek` (float): Accumulated interaction/practice duration.
  * `Attendance (%)` (float): School attendance rate.
  * `PreviousGrade` (float): Historical running average of quiz assessments.
  * `Online Classes Taken` (int/float): Engagement count with digital exercises.
* **Categorical Features:**
  * `ParentalSupport` (`"Low"`, `"Medium"`, `"High"`)
  * `ExtracurricularActivities` (`"Yes"`, `"No"`)
  * `Gender` (`"Male"`, `"Female"`)

#### Internal Pipeline
1. `SimpleImputer(strategy="median")` + `StandardScaler()` for continuous metrics.
2. `SimpleImputer(strategy="most_frequent")` + `OneHotEncoder(handle_unknown="ignore")` for categorical fields.
3. `XGBClassifier(n_estimators=120, max_depth=5, learning_rate=0.08, eval_metric="mlogloss")`.
4. Output decoded through `LabelEncoder.inverse_transform` to produce the categorical CBC band.

#### Target Output Bands
* `Below Expectation (BE)`
* `Approaching Expectation (AE)`
* `Meeting Expectation (ME)`
* `Exceeding Expectation (EE)`

---

### Agent 2: The Curriculum Retrieval Agent (RAG Grounding)
* **Type:** Dense Semantic Retriever over Vector Index.
* **Storage:** Pinecone Serverless Index (`cbc-curriculum-rag`, AWS `us-east-1`).
* **Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2` (Local CPU execution, 384 dimensions, Cosine metric).
* **Ingested Corpus:** KICD Grade 2 Mathematics Activities Curriculum Design (`grade2_math.txt`).

#### Ingestion Rules
* Splitter: `RecursiveCharacterTextSplitter`.
* Chunk Parameters: `chunk_size=700`, `chunk_overlap=100`.
* Separator Precedence: `["\n\n", "\n", ". ", " "]`.
* Metadata Tagging: Every vector carries `{"source": "grade2_math.txt", "chunk_index": int, "text": string}`.

#### Retrieval Protocol
```python
query = f"Grade 2 Mathematics strand: {strand}, assessment level: {predicted_band}"
# Fetches Top-K (default: 3) highest similarity matches
```

---

### Agent 3: The Adaptive Synthesis Agent (Generative Assessment)
* **Type:** Hosted High-Throughput LLM via Groq Cloud (`llama-3.1-8b-instant`).
* **Execution Mode:** Zero-shot / Few-shot prompt conditioning with forced JSON mode (`response_format={"type": "json_object"}`).
* **Temperature:** `0.3` – `0.4` (prioritizing curriculum fidelity over stylistic variation).

#### Pedagogical Difficulty Mapping
* **`Below Expectation (BE)`:** Concrete counting, visual cues, max 12 words per question, step-by-step physical hints (e.g., counters, sticks).
* **`Approaching Expectation (AE)`:** Standard single-step arithmetic, familiar Kenyan realia (shillings, mangoes, sukuma wiki), rule-reminder hints.
* **`Meeting Expectation (ME)`:** Standard KICD end-of-substrand tasks, 1- and 2-step word problems, self-checking hints.
* **`Exceeding Expectation (EE)`:** Inverse/reverse reasoning ($\square + 6 = 15$), missing-operator problems, logical comparison, critical-thinking prompts.

#### Contract Payload (JSON Output)
```json
{
  "strand": "Numbers - Addition",
  "competency_band": "Approaching Expectation",
  "questions": [
    {
      "question_number": 1,
      "question_text": "Amina has 12 oranges. Juma gives her 5 more oranges. How many oranges does Amina have altogether?",
      "options": ["A) 15", "B) 16", "C) 17", "D) 18"],
      "correct_answer": "C) 17",
      "hint": "Count 5 steps forward starting from 12.",
      "pedagogical_objective": "Reinforce 2-digit plus 1-digit addition without regrouping."
    }
  ],
  "teacher_insight_summary": "Learner is practicing basic single-step word problems grounded in practical realia."
}
```

---

## 3. Communication Protocols & APIs

### Primary Endpoint: `POST /api/v1/adaptive-quiz`

#### Request Payload
```json
{
  "student_id": "std_ke_09823",
  "strand": "Addition",
  "hours_studied": 3.5,
  "attendance": 92.0,
  "previous_scores": 58.0,
  "online_classes_taken": 4,
  "parental_support": "Medium",
  "extracurricular_activities": "Yes",
  "gender": "Female"
}
```

#### Processing Sequence
1. FastAPI validates input via `pydantic.BaseModel`.
2. Telemetry is formatted into a 1-row Pandas DataFrame matching `expected_columns`.
3. `pipeline.predict(df)` outputs discrete integer $\rightarrow$ decoded to string band (e.g., `"Approaching Expectation"`).
4. `HuggingFaceEmbeddings` encodes the search query $\rightarrow$ queries Pinecone for Top-3 relevant curriculum chunks.
5. Ingests curriculum chunks + competency instructions + strand into Groq API prompt.
6. Returns validated JSON payload directly to the Kotlin client.

---

## 4. Development & Operation Workflows

### Environment Setup
```bash
# Virtual Environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Dependencies
pip install fastapi uvicorn pydantic joblib pandas scikit-learn xgboost \
            pinecone sentence-transformers langchain-community \
            langchain-text-splitters groq python-dotenv
```

### Environment Variables (`.env`)
```bash
PINECONE_API_KEY="pcsk_..."
GROQ_API_KEY="gsk_..."
```

### Training the Predictor
```bash
python train_model.py
# Outputs: cbc_predictor_bundle.pkl
```

### Ingesting Curriculum to Vector DB
```bash
python embed_and_upsert.py
# Chunks grade2_math.txt, creates Pinecone serverless index, and upserts vectors
```

### Starting the Orchestration Server
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 5. Guardrails & Failure Modes

1. **Vector DB Connectivity Fallback:** If Pinecone times out or exceeds rate limits, the system falls back to a static in-memory dictionary of Grade 2 KICD core competency benchmarks.
2. **Missing Band Mitigation:** The predictor training script must always use dynamic `LabelEncoder` transformations to prevent sparse label failures (`ValueError: Invalid classes inferred`).
3. **JSON Schema Enforcement:** Generative API calls must use Groq's native JSON mode. If validation fails on the backend, a deterministic fallback quiz template matching the strand is returned rather than propagating a 500 error to the mobile client.
4. **Data Isolation:** All personal identifiable information (`StudentID`, `Name`) is strictly excluded from the predictive training matrix to prevent bias and data leakage.
