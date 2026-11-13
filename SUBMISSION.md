# Ajaia — AI-Native Full Stack Developer Assignment — Submission

**Candidate:** Ajay Krishna Devulapally  
**Project:** Scribe — lightweight shared document workspace

## Reviewer links

- **Live product (no signup):** https://scribe-document-editor.onrender.com/
- **Public GitHub source:** https://github.com/Ajay26krishna/scribe-document-editor
- **Google Drive folder:** https://drive.google.com/drive/folders/1D_1d2RU141d1XaFQa10AVHJoj_DpfEcy?usp=sharing
- **3–5 minute walkthrough:** **PENDING — link to be inserted after recording** (also in `walkthrough_url.txt`)

The Google Drive folder has **Anyone with the link → Viewer** permission enabled. The repository is public. No payments or external account creation are necessary for testing Scribe.

## Reviewer quick start

1. Visit the live product and use the top-right account switcher. Default: **Maya Chen** (`maya@demo.scribe`); second user: **Noah Patel** (`noah@demo.scribe`). No passwords are needed.
2. As Maya, create and rename a document, apply bold/italic/underline, headings and lists, wait for **All changes saved**, refresh, and reopen it.
3. Click **Share**, grant Noah **Can edit**, switch to Noah, and open **Shared with me**. Make an edit. Switch back to Maya and change Noah's role to **Can view**; return to Noah to verify read-only behavior.
4. Import `sample-import.md` or a UTF-8 `.txt` file (512 KB maximum).
5. From a document's **⋯** menu, choose **Export to PDF**, then **Save as PDF** in Chrome or Edge's print dialog.
6. From the same menu open **Version history**. Preview previous saved revisions; as the document owner, restore an older revision. This creates a new revision while keeping retained older revisions.

**Security/scope note:** The account switcher simulates identity for demonstration; it is not production authentication. Do not enter sensitive data. Simultaneous coauthoring is not implemented.

## Exactly what is included in this Drive folder

- **`Scribe_Ajaia_Final_Source.zip`** — clean, complete source snapshot with the PDF/history features, code, tests, assets, deployment configuration, and these documents. No environment tokens, local SQLite database, or caches.
- **Individual project files:** `main.py`, `storage.py`, `importer.py`, `requirements.txt`, `requirements-dev.txt`, `pytest.ini`, `render.yaml`, and the `static/`, `tests/`, and `screenshots/` folders. The ZIP is the preferred source download.
- **`README.md`** — quick start, full local setup, feature list, limitations, and deployment information.
- **`ARCHITECTURE.md`** — architecture, persistence, authorization, revision management, and trade-offs.
- **`AI_WORKFLOW.md`** — ChatGPT usage, bugs fixed, rejected scope, and validation.
- **`SUBMISSION.md`** — this document with reviewer links and complete manifest.
- **`WALKTHROUGH_SCRIPT.md`** — narrated 4–5 minute script with on-screen instructions in brackets.
- **`live_url.txt`** — verified deployment address provided by the candidate.
- **`walkthrough_url.txt`** — reserved for the unlisted video URL (recording pending).
- **`sample-import.md`** — Markdown upload sample.

## Functional status

| Requirement | State |
| --- | --- |
| Create, rename, rich-text edit, autosave, and reopen | Implemented; manually tested locally and live |
| Import `.txt` and basic `.md` | Implemented; 512 KB UTF-8 size/type validation |
| Document ownership and sharing | Backend owner/editor/viewer enforcement; two selectable demo users |
| Persistence | SQLite for local use; Turso/libSQL on Render; remote document readback confirmed |
| Browser PDF export (stretch) | Implemented using print CSS and Print → Save as PDF; candidate tested locally and reports live version working |
| Version history (stretch) | Last 30 saved revisions, formatted preview, owner-only restore, revision conflict protection; candidate tested locally and reports live version working |
| Automated testing | 12 pytest tests passed after the update |
| Live deployment | https://scribe-document-editor.onrender.com/ |
| Walkthrough video | **Not yet recorded / link pending** |

## Constraints, known limitations, and next 2–4 hours

Intentional exclusions: OAuth/login, private identity verification, email invitations, real-time simultaneous editing, comments, full Markdown conversion, and `.docx` import. The PDF feature uses a browser print dialog rather than a server-side PDF converter. Version history tracks saved revisions (up to 30), not each keystroke; migration of an existing document starts from its state when history was enabled. The next priorities would be real authentication, improved conflict recovery and side-by-side diffing, and Playwright browser tests.

## Local setup (Windows PowerShell)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

Open `http://127.0.0.1:8000`. Full instructions are in `README.md`.
