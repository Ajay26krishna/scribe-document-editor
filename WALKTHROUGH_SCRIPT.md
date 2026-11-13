# Scribe — 4–5 minute walkthrough script

**Before recording:** Open the deployed Scribe URL in Chrome and enlarge it to comfortable zoom. Keep a code editor ready on `main.py`, `storage.py`, and `tests/test_app.py`; keep Turso open on the `documents` table or SQL editor. Hide tabs that expose credentials, tokens, or private accounts. Start with **Maya Chen** selected. Use the `sample-import.md` file from the project. The words in **bold brackets** tell you what to show on screen, not what to read aloud.

## 0:00–0:25 — Product and scope

**[SCREEN: Show deployed Scribe dashboard, move cursor over New document, Import file, My documents, and Shared with me.]**

"Hi, I'm Ajay Krishna. This is Scribe, a lightweight collaborative document workspace I built for Ajaia's full stack assignment. I focused on a complete create, edit, save, import, and share workflow rather than trying to recreate all of Google Docs. The app is publicly deployed and uses persistent cloud storage."

## 0:25–1:20 — Create, format, and autosave

**[SCREEN: Click New document. Rename it `Ajaia Walkthrough`. Type a short heading and two sentences. Highlight words and click Bold, Italic, and Underline. Add a heading and a bulleted list.]**

"Users can create and rename documents directly in the editor. Quill gives the editor familiar rich-text controls such as bold, italic, underline, headings, and lists. Formatting is stored as structured Delta JSON, not raw HTML."

**[SCREEN: Pause for `All changes saved`, return to dashboard, reopen the same document, refresh browser.]**

"Changes autosave, and reopening or refreshing preserves both text and formatting."

## 1:15–1:40 — Import a file

**[SCREEN: Return to dashboard; click Import file; select `sample-import.md`; open the newly imported document.]**

"I included document import for UTF-8 text and basic Markdown. The imported content becomes editable immediately. Full Markdown and DOCX conversion were deliberately left out to keep the assignment scoped."

## 1:40–2:35 — Share and enforce permissions

**[SCREEN: Switch back to Maya's walkthrough document. Open Share; select Noah Patel, choose Can edit, and grant access.]**

"Every document has an owner. An owner can give another seeded user editing or viewing access."

**[SCREEN: Switch top-right account from Maya to Noah. Click Shared with me; open the document; add a short line; wait for save.]**

"Noah now sees the document under Shared with me and can edit it. Changes persist for the owner, too."

**[SCREEN: Switch to Maya, open Share, change Noah's role to Can view. Switch to Noah and reopen the document; point out that editing is disabled.]**

"With viewer permission, Noah can read but not edit. These checks also run in the backend, not just in the interface. Authentication is mocked through a two-user switcher for this demo; it is not production login security."

## 2:35–3:15 — PDF export and saved versions (optional stretch)

**[SCREEN: In the document, click the ⋯ menu → Export to PDF; select Save as PDF in the Chrome print preview. Then open ⋯ → Version history. Click an earlier save and show its formatted preview. As Maya, restore an older revision and show the updated editor.]**

"I added two scoped enhancements after the core app was working. Export to PDF uses a print-friendly layout and the browser's Save as PDF option. Version history keeps the most recent 30 saved revisions, lets anyone with document access preview them, and lets only the owner restore an older revision. Restoring creates a new version, so the previous latest state isn't destroyed."

## 3:15–3:55 — Architecture, tests, and persistence

**[SCREEN: Show GitHub repository, then briefly `main.py`, `storage.py`, and `tests/test_app.py`. Optional: show a terminal with `12 passed` if you have run the tests locally.]**

"The backend is Python FastAPI. The frontend is plain JavaScript and Quill, so there's no bundler to set up. SQLite works locally, while the deployed Render service connects to Turso for durable storage. The backend validates inputs and checks owner, editor, and viewer permissions. I also added revision checks so stale saves are rejected instead of silently overwriting newer content. Twelve automated tests cover the API, version snapshots, restore permissions, migration, and conflicts."

**[SCREEN: Show live `/healthz` returning `storage: turso`. Show Turso's documents table and the saved walkthrough document. Never show database tokens.]**

"I verified the live connection both through the health endpoint and by reading the saved document directly in Turso."

## 3:55–4:45 — AI usage, fixes, and trade-offs

**[SCREEN: Show AI_WORKFLOW.md, then quickly highlight the italic fix in `static/styles.css` and `static/index.html`; finish on the live Scribe dashboard.]**

"I used ChatGPT to accelerate project scoping, API and UI scaffolding, test creation, and debugging. I didn't treat generated output as automatically correct. For example, italic formatting initially failed because the font settings suppressed italics. I corrected the CSS and loaded the proper font variants, then retested the editor. I also switched the deployed storage from local SQLite to Turso because Render's free disk isn't durable."

"I intentionally skipped real-time editing, comments, and real authentication. Given another few hours, I'd add genuine login, better edit-conflict recovery, and automated browser tests. After finishing the core requirements, I added PDF export and limited version history. The result is a focused, working product slice. Thanks for watching."

## After recording

1. Verify the video is **3–5 minutes** and visible without logging into your personal account (unlisted Loom/YouTube works).
2. Paste the link into `walkthrough_url.txt`, `SUBMISSION.md`, and your final submission message.
3. Keep the live Render URL and GitHub source link separately visible in `SUBMISSION.md`.
