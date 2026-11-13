# Scribe — 4–5 minute walkthrough narration

**Live demo:** https://scribe-document-editor.onrender.com/  
**Repository:** https://github.com/Ajay26krishna/scribe-document-editor  
**Length:** Target 4:30–4:55. Read spoken paragraphs naturally. **Instructions in square brackets are screen actions and should not be spoken.**

**Before recording:** Keep Chrome/Edge open on Scribe, have `sample-import.md` ready for upload, sign in to GitHub in another tab, and open the Turso documents table or SQL editor (without exposing tokens). Use Maya Chen initially. If you demonstrate the version restore, create at least two saved revisions before recording or do so on camera. Avoid confidential data.

## 0:00–0:25 — Introduction

**[SCREEN: Open https://scribe-document-editor.onrender.com/. Show the clean dashboard, New document, Import file, Owned by me, and Shared with me.]**

"Hi, I'm Ajay Krishna. This is Scribe, a lightweight shared document workspace built for Ajaia's AI-Native Full Stack Developer assignment. I focused on completing the document workflow end to end—editing, autosaving, importing, and sharing—rather than attempting to recreate every Google Docs feature."

## 0:25–1:10 — Editing and persistence

**[SCREEN: Click New document. Rename it Ajaia Walkthrough. Add a heading, two sentences, bold text, italic, underline, and a bulleted list. Show the save indicator. Return to the dashboard, reopen the same document, then refresh.]**

"Users can create and rename documents and apply familiar rich-text formatting using Quill. The editor stores structured Delta JSON so formatting survives saving and reopening. Changes autosave with a visible status. Even after refreshing, the content and formatting remain available."

## 1:10–1:30 — Import

**[SCREEN: Return to the dashboard, choose Import file, select sample-import.md, and briefly show the imported editable content.]**

"I also added a practical import flow for UTF-8 text and basic Markdown files. Imported content becomes a new editable document. I limited the formats intentionally to keep the workflow reliable."

## 1:30–2:20 — Sharing and roles

**[SCREEN: Open the walkthrough document as Maya. Click Share, select Noah Patel and Can edit, and grant access. Switch the account to Noah, open Shared with me, make an edit, and wait for autosave. Switch to Maya and set Noah to Can view, then switch back to show the read-only editor.]**

"Each document has an owner, and the owner can grant editing or viewing permissions. Noah can see a document shared with him, and his edits are reflected for Maya. When he's changed to a viewer, editing is disabled. The important point is that these permissions are checked in FastAPI, not only in the browser. Authentication is intentionally simulated with two seeded accounts for the demo."

## 2:20–3:05 — Two stretch features

**[SCREEN: As Maya, reopen the document. Click ⋯ → Export to PDF. In the browser print dialog select Save as PDF and show that only the document is printed. Return to Scribe and click ⋯ → Version history. Select an earlier revision to preview. Restore it as Maya and show the new current revision.]**

"After finishing the core requirements, I added two scoped enhancements. Export to PDF produces a print-friendly page through the browser's Save as PDF flow. Version history keeps up to thirty saved revisions and previews their formatting. Only an owner can restore an older revision, and restoring creates a new revision rather than deleting the more recent history."

## 3:05–3:50 — Architecture and verification

**[SCREEN: Open https://github.com/Ajay26krishna/scribe-document-editor. Show main.py, storage.py, and tests/test_version_history.py. Briefly show the terminal with `12 passed`. Then show https://scribe-document-editor.onrender.com/healthz and a Turso documents-table entry. Never show database credentials.]**

"The stack uses FastAPI for validation and REST APIs, vanilla JavaScript and Quill for the frontend, and SQLite-compatible storage. SQLite runs locally; the deployed Render service connects to Turso for durable cloud data. Autosaves use revision checks to reject stale writes. Twelve automated tests pass, covering document behavior, sharing, conflicts, migration, and version restoration. I also confirmed hosted persistence by finding a document created on the live site in Turso."

## 3:50–4:40 — AI-native workflow, bug fix, and trade-offs

**[SCREEN: Show AI_WORKFLOW.md on GitHub. Open static/styles.css to point at `font-synthesis:auto`; open static/index.html and point at Google Fonts italic variants. Return to Scribe.]**

"I used ChatGPT to help scope the assignment, accelerate the initial API and UI scaffolding, create test cases, debug issues, and plan deployment. I still verified the output myself. For example, italic formatting initially wasn't rendering because the font setup suppressed it. I adjusted the CSS and loaded real italic font variants, then tested it again. I also used Turso instead of relying on Render's temporary local storage, and added automated checks around history and permissions."

"I chose not to add real-time simultaneous editing, comments, or production authentication within this scope. With more time, my next improvements would be proper login, better conflict recovery, and automated browser tests. Thank you for watching."

## After recording

1. Keep the recording between **3 and 5 minutes**. Trim unused loading or print-dialog time.
2. Upload to Loom or YouTube as an unlisted or otherwise accessible video. Open the link in an Incognito window to verify reviewer access.
3. Paste its **actual URL** into `walkthrough_url.txt` and `SUBMISSION.md`, update those files in GitHub and Google Drive, and only then submit.
