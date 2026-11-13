# Scribe — a lightweight shared document workspace

> **Ajaia AI-Native Full Stack Developer Assignment**  
> Candidate: Ajay Krishna Devulapally

Scribe is a deliberately scoped document editor: create or import documents, format and autosave text, share access with a teammate, and reopen content with its formatting intact.

## 60-second reviewer quick start

1. Open the **live URL** added to `SUBMISSION.md` after deployment.
2. The default account is **Maya Chen**. Open **Welcome to Scribe**, format text, wait for **All changes saved**, then refresh to confirm persistence.
3. Create a document, click **Share**, select **Noah Patel** and **Can edit**, and click **Grant access**.
4. Switch the top-right demo account to **Noah Patel**. The document appears under **Shared with me** and is editable. Switch back to Maya to revoke access.
5. Import a UTF-8 `.txt` or `.md` file using **Import file** in the left sidebar.

### Seeded demo accounts (no passwords)

| Display name | Email | How to access |
| --- | --- | --- |
| Maya Chen | `maya@demo.scribe` | Select “Maya Chen” in the account dropdown |
| Noah Patel | `noah@demo.scribe` | Select “Noah Patel” in the account dropdown |

**Authentication is intentionally mocked** via a cookie-backed account switcher, as permitted by the assignment. Do not treat the demo as a production identity system. Both accounts are available to every reviewer.

## Tech stack

- **Backend:** Python 3.10+, FastAPI, Pydantic; REST endpoints.
- **Frontend:** browser-native JavaScript, HTML, CSS; Quill 2.0.3 rich-text editor (loaded from jsDelivr CDN, internet required).
- **Persistence:** built-in SQLite locally; Turso/libSQL over HTTPS in hosted mode, same SQL schema and server-side permission checks.
- **Testing:** pytest + FastAPI TestClient, real temporary SQLite database.
- **Deployment:** single Render Python web service + persistent Turso database, both with free plans.

A build process, Node.js, and Docker are **not** needed to run this project.

## Local setup

From the project root:

```bash
python -m venv .venv
```

Activate the environment:

```bash
# macOS/Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install and start:

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Open **http://127.0.0.1:8000/**. The app creates `data/scribe.sqlite3`, creates tables, and seeds two demo users and example documents on first run. Data survives page refreshes and app restarts. Keep browser internet access enabled for Quill (jsDelivr) and optional Google Fonts.

**To reset the local demo:** stop the server, delete `data/scribe.sqlite3`, and restart.

### Run tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

The automated tests cover document CRUD and formatted content persistence, optimistic concurrency conflicts, per-user access enforcement, share/editor/viewer roles and revocation, Markdown/text imports, and server-side Delta validation.

**API documentation:** `http://127.0.0.1:8000/docs` (FastAPI Swagger UI). **Health check:** `http://127.0.0.1:8000/healthz`.

## Recommended live deployment: Render + Turso

**Why two services?** Free Render web instances have an *ephemeral filesystem* that is wiped when they spin down or restart. A local SQLite database is fine for development but would not provide reliable deployed persistence. The hosted configuration uses the same SQLite-compatible schema stored in a separate Turso database.

1. Create a free database in **[Turso](https://turso.tech/)**. Copy the database URL (usually `libsql://…turso.io`) and create an authentication token with database access.
2. Push the project source to a GitHub repository. Keep `.env` and database files private; `.gitignore` already excludes them.
3. Sign in to **[Render](https://render.com/)** and select **New → Web Service**, then connect the repository. Render can read `render.yaml`, or configure the following manually:
   - Runtime: `Python 3`
   - Plan: `Free`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Health check path: `/healthz`
4. Set **secret** environment variables in Render (never commit tokens):

   ```env
   TURSO_DATABASE_URL=libsql://YOUR_DATABASE_HOST.turso.io
   TURSO_AUTH_TOKEN=YOUR_DATABASE_AUTH_TOKEN
   ```

5. Deploy. Wait for Render's deployment to finish, then open the provided `https://…onrender.com` URL. The first request may have a cold start.
6. **Smoke-test on the deployed URL:** make a document, change formatting, wait for autosave, refresh; switch to Noah and verify that only shared documents are accessible; refresh again to verify remote persistence.
7. Copy the deployed URL into `SUBMISSION.md` and your Google Drive handoff.

**Important:** The source here includes a Turso HTTP protocol adapter and test-covered local SQLite path. Without your own Turso token and Render account, the hosted adapter and live deployment are **not yet verified end to end**. Do this smoke test before submitting. No reviewer needs a paid account.

Documentation: [Render FastAPI deployment](https://render.com/docs/deploy-fastapi), [Render free-tier filesystem limitations](https://render.com/docs/free), [Turso pricing](https://turso.tech/pricing), [Quill installation](https://quilljs.com/docs/installation).

## Working features

| Area | Implemented behavior |
| --- | --- |
| Documents | Create, rename, edit, delete, search by title or owner, reopen |
| Rich text | Bold, italic, underline, strike, headings 1–3, lists, blockquotes, clear formatting |
| Persistence | Quill Delta JSON saved through FastAPI into SQLite-compatible storage |
| Autosave | 700 ms debounce, visible save state; queued saves; revision check prevents silent overwrites |
| File import | UTF-8 `.txt` and a **deliberate subset** of `.md` (headings, lists, bold, italic, inline code) |
| Sharing | Owner can grant editor or viewer access to the other seeded account, update or revoke it |
| Backend permissions | Unauthorized documents are omitted; viewer edits rejected; owner-only share/delete operations |
| Validation | 1–120 character titles, import types/size, Delta text/attributes, content-size limits |
| Seed data | One owned document and one read-only shared document visible at startup |
| Experience | Responsive dashboard, document editor, sharing modal, error toasts |

### Constraints / intentional exclusions

- Markdown support is **not a complete Markdown implementation**; tables, images, links, nested lists, fenced code blocks, and other extensions are not converted to rich formats. They are preserved as plain editable text when possible.
- Only UTF-8 `.txt`/`.md` imports, maximum **512 KB**. No `.docx` or attachment storage. The editor accepts a maximum of 100,000 text characters / 250 KB serialized Delta.
- Quill is loaded from an external CDN to minimize build setup. Browser access to jsDelivr is required.
- No real login/passwords/OAuth, email invitations, public links, live multi-cursor collaboration, comments, version history, PDF export, backups, or rate limiting.
- Conflict behavior is **detect and reject**, not merge: simultaneous stale updates get HTTP `409`; the editor notifies the user to reopen. This avoids silent overwrites but is not real-time collaboration.
- Demo switching is accessible to all; never store sensitive information in this assignment deployment.
- A shared document link still requires the account to be granted access. Copying a link alone does not grant permission.

### What I would build with another 2–4 hours

1. Real authentication/session handling (e.g. Auth.js or OAuth), server-verified identity and invitation email flow.
2. Better conflict UX with draft recovery and optional version snapshots instead of an error-only response.
3. Playwright browser regression tests for editor formatting, import, reload, and share flows; self-hosted Quill assets for offline reliability.

## Folder map

```text
scribe-assignment/
├── main.py                 # FastAPI routes, validation, authorization
├── storage.py              # Local SQLite and remote Turso HTTP adapter
├── importer.py             # Safe text / limited Markdown -> Quill Delta
├── static/
│   ├── index.html          # Application structure
│   ├── app.js              # UI state, editor integration and autosave
│   └── styles.css          # Responsive design
├── tests/
│   ├── test_app.py         # Local API tests
│   └── test_remote_adapter.py  # Hosted adapter protocol test
├── screenshots/
│   └── dashboard.png       # Dashboard preview
├── sample-import.md       # Demo file to import
├── pytest.ini
├── render.yaml             # Render deployment template
├── .env.example            # Environment variable example
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
├── ARCHITECTURE.md
├── AI_WORKFLOW.md
├── WALKTHROUGH_SCRIPT.md
├── walkthrough_url.txt
└── SUBMISSION.md
```

## AI use and responsible attribution

AI was used to plan and generate an initial implementation and documentation. The candidate is responsible for **running the code independently, reviewing it, fixing any issues found, deploying the public version, recording the demo, and personalizing the AI workflow note to reflect what they actually did**. See `AI_WORKFLOW.md` for a starting draft that separates verified tests from pending manual checks.
