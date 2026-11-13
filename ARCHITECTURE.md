# Architecture and engineering trade-offs — Scribe

**Project:** Scribe — lightweight shared document workspace  
**Assignment:** Ajaia AI-Native Full Stack Developer  
**Source:** https://github.com/Ajay26krishna/scribe-document-editor

## Product scope and priorities

I scoped the app to two complete, testable workflows: **create → format → autosave → reopen** and **owner → share → switch user → enforce a viewer/editor role**. A usable editor, durable persistence, and backend permission checks matter more here than half-built Google Docs features.

## Architecture

```text
Browser (HTML, CSS, JavaScript, Quill 2)
          | REST JSON + multipart import
          v
FastAPI: validation / document routes / permission checks
          |
          v
SQL adapter (storage.py)
     /               \
SQLite locally       Turso/libSQL over HTTPS on Render
```

- **Frontend:** Quill handles text selection, formatting, headings, and lists. Vanilla JS manages account switching, document lists, editor state, save indicators, sharing, import, and error feedback.
- **Persistence:** document structure is stored as **Quill Delta JSON** rather than untrusted HTML, preserving formatting. The same SQL schema is used with local SQLite and hosted Turso.
- **Schema:** `users(id, name, email)`, `documents(id, owner_id, title, delta_json, revision, created_at, updated_at)`, and `shares(doc_id, user_id, role)`, and `document_versions(doc_id, revision, title, delta_json, saved_at)`.
- **Identity model:** Maya Chen and Noah Patel are seeded demo users. A cookie-backed account selector simulates authentication, explicitly **not a production security boundary**.
- **Access:** owners can edit, delete, and manage sharing; editors can read/edit; viewers can only read. Backend routes enforce authorization and return not-found/forbidden-style responses rather than trusting disabled UI buttons.
- **Autosave:** text is saved after a roughly 700 ms debounce. A `revision` integer enables optimistic concurrency: stale writes produce HTTP 409 instead of silently replacing newer content.
- **File handling:** UTF-8 `.txt` and a documented subset of `.md` are parsed into safe Quill Delta operations; uploads are size-checked. Full Markdown and `.docx` imports were excluded to stay within the timebox.

## Why these technology choices?

**FastAPI + SQLite:** simple routes, minimal local setup, built-in validation, and meaningful integration tests without a large framework. **Quill:** solves rich-text cursor/selection issues reliably, avoiding a fragile custom `contenteditable` implementation. **Turso:** keeps SQLite-compatible query semantics while providing durable hosted storage; Render's free instance disk would not be suitable for long-lived documents. **Render:** simple, accessible public Python deployment with a reusable `render.yaml`.

## Verification performed

- Twelve automated pytest cases covering document data, formatting persistence, permissions, role changes/revocation, conflicts, imports, the Turso adapter protocol, snapshots, restore, history permissions, migration, and retention.
- Candidate-tested local editor including the italic-font correction, content saving/reopening, and sharing.
- Candidate-tested live Render deployment, account-based sharing, and remote persistence. `/healthz` reported `{"status":"ok","storage":"turso"}`; a newly created test document was confirmed in Turso's actual `documents` table.
- Turso's dashboard usage counters are not used as proof of data integrity; direct database reads and application behavior provide the verification.

## Intentional cuts and next 2–4 hours

- **Added after the core scope was stable:** browser print-to-PDF and a bounded (30-save) history with formatted preview and owner-only restore.
- **Not built:** real login/OAuth, emailed invitations, simultaneous live editing, comments, complete Markdown or `.docx`, and production hardening.
- **Version history design:** SQLite/libSQL `AFTER INSERT` and `AFTER UPDATE` triggers atomically snapshot a document each time its data is saved. The `document_versions` table stores `(doc_id, revision, title, delta_json, saved_at)`; it keeps the newest 30 revisions. On upgrade, existing documents are backfilled from their current state once. Restoring an old snapshot increments the current revision and also saves the restored state as a new version. A `current_revision` precondition prevents racing another editor. Anyone with access can preview history; only the owner can restore.
- **PDF design:** a frontend print action and `@media print` CSS remove the app chrome and let the rich-text page flow across printed sheets. No PDF library, backend storage, or build step is needed. Users select Save as PDF in the browser dialog.
- **Next:** (1) real authentication and invitations, (2) improved stale-draft conflict recovery and diff/compare UI, (3) browser-level Playwright tests and accessibility improvements.
- **Verification boundary:** history endpoints and SQLite migration are covered by automated tests; the new features still require a manual production-browser check against the configured Turso database before presenting them as verified live.

**Operational warning:** Because the identity switcher is available to all demo visitors, the live environment is a functional evaluation demo, not a private document store. Do not enter confidential information.
