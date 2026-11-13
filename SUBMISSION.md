# Ajaia AI-Native Full Stack Developer Assignment — Submission

**Candidate:** Ajay Krishna Devulapally  
**Project:** Scribe — lightweight shared document workspace

## Links — fill in before submitting

- **Google Drive folder:** TODO — paste the shareable folder URL
- **Live product URL:** TODO — paste your deployed Render URL after completing its smoke test
- **3–5 minute walkthrough:** TODO — paste the same video URL saved in `walkthrough_url.txt`

## Exactly what this folder contains

- `main.py` — API, server permissions and validation
- `storage.py` — local SQLite and remote Turso persistence
- `importer.py` — limited `.txt` / `.md` to Quill Delta importer
- `static/index.html`, `static/app.js`, `static/styles.css` — frontend
- `tests/test_app.py`, `tests/test_remote_adapter.py`, `pytest.ini` — automated API tests
- `requirements.txt`, `requirements-dev.txt` — dependencies
- `.env.example`, `.gitignore`, `render.yaml` — environment/deployment configuration
- `README.md` — setup, reviewer instructions, limitations, and deployment steps
- `ARCHITECTURE.md` — architecture and prioritized trade-offs
- `AI_WORKFLOW.md` — AI usage and verification note (candidate review required)
- `WALKTHROUGH_SCRIPT.md` — video recording outline
- `walkthrough_url.txt` — walkthrough URL (pending replacement)
- `sample-import.md` — sample file for the import demonstration
- `screenshots/dashboard.png` — screenshot of the dashboard with seeded local data

`data/*.sqlite3` databases, credentials, Python cache, and virtual environment files are intentionally excluded.

## Reviewer access

No password is necessary: use the **Viewing as** dropdown to switch between `maya@demo.scribe` and `noah@demo.scribe`. These are seeded demonstration accounts, not production authentication. The live website should not contain sensitive information.

## Feature status (update after deployment)

| Capability | Status |
| --- | --- |
| Create, rename, edit, delete, and reopen | Implemented; local API tests pass |
| Rich-text formatting + autosave | Implemented; browser end-to-end manual check pending |
| `.txt`/`.md` import | Implemented; API tests pass (limited Markdown syntax) |
| Share with viewer/editor role + revoke | Implemented; API tests pass |
| Backend permission checks | Implemented; API tests pass |
| SQLite local persistence | Implemented; API tests pass |
| Hosted Turso persistence | Implementation prepared; live smoke test pending |
| Public deployment | **Not yet completed** |
| Walkthrough recording | **Not yet completed** |

## Not implemented (intentional cuts)

Real sign-in/OAuth, `.docx` import, complete Markdown parsing, live simultaneous editing, comments, version history, PDF export, public links, and production-grade account security.

## Next 2–4 hours

1. Real authentication and invitation identity instead of demo switching.
2. Improved conflict/recovery UX and document revision history.
3. Automated browser tests and self-hosted Quill assets.

## Local run

```bash
pip install -r requirements.txt
uvicorn main:app --reload
# Open http://127.0.0.1:8000/
```

Tests: `pip install -r requirements-dev.txt && pytest -q`. See `README.md` for full deployment instructions.
