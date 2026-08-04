# Scriptorium Workspace: Implementation Blueprint & Architectural Rules

> **Target Audience**: AI Coding Agents & Engineers implementing Scriptorium Workspace.
> **Reference Architecture**: Proven patterns from `D:/elix/praxis_csc` (`desktop.py`, `backend/`, `frontend/`, `.agents/AGENTS.md`).

---

## 1. System Architecture Overview

Scriptorium Workspace is a self-contained, local-first Desktop GUI Application for non-tech users in Vietnam.

```
Scriptorium Workspace
├── React Frontend (Vite + TS + Tailwind + ShadcnUI)
│   └── Layout: Folders (left) | Editor / Reviewer / Chat (right)
├── Python FastAPI Backend (127.0.0.1:47000)
│   ├── Desktop Orchestrator (pywebview + Win32 Named Mutex)
│   ├── Local File Sandbox (safe_join_sandbox)
│   └── Agent Orchestrator & WebSocket NDJSON Event Stream
└── Elixverse AI Routing Gateway (api.elixverse.com / PAYG Zero-BYOK)
```

---

## 2. Tech Stack Specification

* **Frontend**: React 18, Vite, TypeScript (Strict Typing), TailwindCSS, ShadcnUI, Lucide Icons, `@monaco-editor/react`, KaTeX (LaTeX math rendering).
* **Backend**: Python 3.11+, FastAPI, Uvicorn, SQLite3, `httpx`, `pydantic`, `json_repair`.
* **Desktop Shell**: `pywebview` launching Uvicorn on loopback port (`127.0.0.1:47000`), polling `/health`, opening native window.
* **Single-Instance Control**: Win32 Named Mutex (`Global\ScriptoriumWorkspace_Mutex_47000`).
* **Packaging**: PyInstaller single `.exe` build (declaring resource paths via `sys._MEIPASS`).

---

## 3. Architectural Rules & Guardrails for AI Coding Agents (R1 - R15)

Every AI Coding Agent developing this codebase MUST strictly follow these 15 architectural rules:

### 3.1. Lifecycle & Threading Rules (R1 - R3)
- **R1: Server Lifecycle Managed via Typed State Machine**: `Booting -> EnvironmentChecking -> ServerReady -> ShuttingDown`. The frontend must poll `/health` and block interactions until `ServerReady`.
- **R2: Dynamic Port Fallback**: Attempt to bind to port `47000`. On collision, scan sequentially from `47001` to `48000`.
- **R3: CORS Middleware Registered First**: CORS middleware must be added outermost in FastAPI.

### 3.2. Security & Sandbox Rules (R4 - R6)
- **R4: Safe Path Containment Chokepoint**: ALL file operations on `D:/my_workspace/` MUST validate paths through `safe_join_sandbox(base_dir, relative_path)` to prevent path traversal (`../`).
- **R5: No Mocks in Production Code**: Mocks forbidden in production paths; isolated under `tests/`.
- **R6: Log Sandbox Failures to SQLite**: Record every execution failure in SQLite before returning HTTP error.

### 3.3. Asynchronous & AI Execution Rules (R7 - R9)
- **R7: Circuit Breakers for Agent Loops**: Set `MAX_STALLED_TURNS = 3` for consecutive compiler/validator failures, and `MAX_TARGET_CHURN = 5` for single-target modifications.
- **R8: Reasoning Token Control for Structured JSON**: Set `thinkingBudget: 0` (hard disable) on every LLM call for structured output (JSON schema/repair) to prevent token truncation and latency overhead.
- **R9: Three-Layer JSON Resilience Pattern**: Apply 1. Prevention (Token limits), 2. Recovery (`json_repair`), 3. Fallback (Chunked generation).

### 3.4. Packaging & Build Rules (R10 - R11)
- **R10: PyInstaller Hidden Imports**: Explicitly declare dynamic dependencies (`sqlite3`, `httpx`, `passlib`, `pydantic`, `json_repair`, `jinja2`) in `pyinstaller.spec`.
- **R11: Runtime Path Resolution (`_MEIPASS`)**: Build helper `get_resource_path()` for resolving PyInstaller temporary bundle paths.

### 3.5. API & UI State Synchronization Rules (R12 - R13)
- **R12: Edge Normalization**: Enforce camelCase conversion at API boundary via Pydantic `ConfigDict(alias_generator=to_camel)`. React client consumes camelCase exclusively.
- **R13: Prevent React Stale Closures**: Use functional state updaters `setState(prev => ...)` or `useRef`.

### 3.6. Data Integrity & Error Visibility Rules (R14 - R15)
- **R14: No Silent Mutation Failures**: Every React Query `useMutation` MUST handle failure visibly via `onError` toast/alert or inline error render.
- **R15: On-Disk Artifact Source Sync**: When an endpoint renames a resource referenced in on-disk files, it MUST patch or regenerate the on-disk file in the same request.

---

## 4. Local Workspace Sandbox Taxonomy (`D:/my_workspace`)

```
D:/my_workspace/
├── personals/              # User/Org profile metadata
│   ├── user_profile.json
│   └── org_profile.json
├── data/                   # Brand assets, PPTX/Word templates, glossaries
├── documents/              # Long-term reference documents
├── skills/                 # Portable Skill Packs exported from Scriptorium
├── registry/               # Local skill registry catalog
└── projects/               # Session work matters
    ├── _template/          # Default project skeleton
    └── yyyyMMdd-hhmmss-{name}/
        ├── .context/
        │   ├── PROJECT_PLAN.md
        │   └── STATE.json
        ├── inputs/         # User uploaded source files
        └── outputs/        # Agent generated deliverables
```

---

## 5. Elixverse AI Provider Router Integration Contract

- Base URL: `https://api.elixverse.com/api/v1` (Local dev: `http://localhost:8000/api/v1`)
- Contract Reference: `D:\elix\platform\docs\API_REFERENCE.md`
- Endpoint: `POST /chat/completions` (OpenAI-shaped, streaming & sync)
- Authentication: `Authorization: Bearer elix_sk_...` or OAuth token with `ai.use` scope.
- Features: Automatic provider failover, dynamic PAYG pricing, zero-BYOK setup for end users.
