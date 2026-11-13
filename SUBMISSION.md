# Ajaia — AI-Native Full Stack Developer Assignment — Submission

**Candidate:** Ajay Krishna Devulapally  
**Project:** Scribe — lightweight shared document workspace

## Reviewer links

- **Live product URL:** `PASTE_YOUR_WORKING_RENDER_URL_HERE`
- **Source code (public GitHub):** https://github.com/Ajay26krishna/scribe-document-editor
- **Google Drive submission folder:** https://drive.google.com/drive/folders/15yG8FJSZvjVO4L07SZjb0q-IKroBUhyO (enable Viewer link access before submitting)
- **3–5 minute video walkthrough:** `PASTE_UNLISTED_VIDEO_URL_HERE`

## How to review in 60 seconds

1. Open the **live product URL** above; no signup or payment is needed.
2. Select **Maya Chen** (`maya@demo.scribe`) in the account switcher. Create and format a document; wait for autosave and refresh to confirm persistence.
3. Click **Share**, grant **Noah Patel** (`noah@demo.scribe`) **Can edit**, then switch to Noah and find the document under **Shared with me**.
4. Change Noah's role to **Can view** to demonstrate read-only access.
5. Click **Import file** to upload a UTF-8 `.txt` or `.md` file (maximum 512 KB).
6. On any document use **⋯ → Export to PDF** and select **Save as PDF** in the browser print dialog.
7. Open **⋯ → Version history** to preview previous saves; as the document owner, choose an older revision and restore it as a new revision.

**Access model:** The two accounts are simulated and selectable with no password. This is deliberate for evaluating the sharing workflow, not production authentication. Do not enter confidential content in this demo.

## Exactly what the Google Drive folder contains

1. `Scribe_Ajaia_Final_Source.zip` — source code, tests, static assets, deployment configuration, documentation, sample import file, and screenshot; excludes virtual environments, local databases, secrets, and caches.
2. `README.md` — reviewer quick start, Windows/local setup, architecture overview, feature status, limitations, and deployment instructions.
3. `ARCHITECTURE.md` — architectural decisions, data model, permissions, autosave, and scope trade-offs.
4. `AI_WORKFLOW.md` — AI tools used, what was changed, and verification actually performed.
5. `SUBMISSION.md` — this manifest and reviewer-access instructions.
6. `WALKTHROUGH_SCRIPT.md` — narrated video script with on-screen cues.
7. `walkthrough_url.txt` — unlisted walkthrough URL (**replace placeholder after recording**).
8. `live_url.txt` — live Render URL (**replace placeholder before submission**).
9. `dashboard.png` — dashboard preview.
10. `sample-import.md` — example import file.

## Implemented and verified

| Requirement | Status |
| --- | --- |
| Create / rename / edit / save / reopen | Working locally and in the deployed browser |
| Rich text: bold, italic, underline, headings, lists | Working; italic rendering issue corrected |
| Autosave and preserved formatting | Working in local and live manual testing |
| Import UTF-8 `.txt` / `.md` | Working; intentionally limited Markdown subset |
| Owner / editor / viewer permissions | Working, with backend checks; demo identity switcher |
| Local persistence | SQLite |
| Hosted persistence | Turso; `/healthz` confirms Turso and SQL readback confirms writes |
| Deployment | Render web service, functioning in browser |
| Automated tests | Twelve passing tests, including history migration, restoration, retention and permissions |
| Browser PDF export (stretch) | Implemented; verify using Chrome/Edge Print → Save as PDF on the deployed URL |
| Bounded version history (stretch) | Implemented, local API tests pass; production Turso redeploy and manual verification pending |
| Walkthrough video | Link pending recording |

## Deliberate exclusions and next 2–4 hours

No real OAuth/login, emailed invitations, simultaneous editing, comments, `.docx` import, or complete Markdown rendering. PDF uses the browser print dialog rather than a server-generated PDF file; history retains the last 30 **saved** revisions, and initial upgrade history starts from the document state at migration. With additional time I would add real authentication/invitations, unsaved-draft conflict recovery and version diffing, and Playwright end-to-end browser tests.

## Local setup (Windows PowerShell)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

Open http://127.0.0.1:8000. Full instructions are in `README.md`.
