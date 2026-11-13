# AI-native development workflow — draft for candidate review

> **Please personalize before submitting.** This note identifies the AI assistance used in the provided starter implementation. Add only hands-on checks, decisions, and fixes you genuinely performed. Do not claim a deployment, browser walkthrough, or tools you have not used.

## Tools used

- **ChatGPT (GPT-6):** decomposed the assignment, evaluated scope/trade-offs, drafted the FastAPI/storage/frontend implementation, generated the API tests, and prepared initial documentation.
- **pytest / FastAPI TestClient:** executed integration-style HTTP tests with temporary SQLite databases to verify the implementation. These are verification tools, not AI tools.
- **Web documentation:** consulted Quill, Render, and Turso implementation/deployment docs to select a realistic editor and persistent deployment approach.

## Where AI materially accelerated work

AI shortened the time spent writing repetitive API routing, Delta validation, SQL setup, the document list/sharing UI, and test scaffolding. I used it to turn the prompt into a small end-to-end product slice instead of building a speculative set of features.

## AI-generated material that was changed or rejected

- Initially considered a more complex Next.js/Tiptap/ORM path. Chose FastAPI + Quill + SQLite-compatible storage to reduce setup, integrate tests quickly, and make the deployed stack straightforward.
- Intentionally rejected a raw HTML import/storage model. Kept Quill Delta JSON and server-side restrictions on inserted content to reduce script-injection risks.
- A generated test configuration initially failed to import the application when run with `pytest`; adding explicit `pythonpath` in `pytest.ini` corrected test discovery/imports.
- Rejected deploying a free Render service with local SQLite as a persistence solution because files are ephemeral; prepared a remote Turso configuration instead.

## What was actually verified so far

- `pytest -q`: **7 passing tests** on local SQLite, including permissions, sharing/revocation, file import, stale revision rejection, and formatted content round trips.
- `node --check static/app.js`: passed JavaScript syntax validation.
- Local `/healthz`: responded with status OK in the development environment.
- A local browser smoke check rendered the dashboard and exercised the owned/shared filter using a test API bridge; this is not a substitute for testing the live Quill editor in a normal browser.

## Candidate verification before submission — complete yourself

- [ ] Run the project locally in your normal browser and test **rich text formatting**, autosave after typing, refresh, and reopening.
- [ ] Verify the share invitation with both demo user accounts, including editor versus viewer restrictions.
- [ ] Upload sample `.txt` and `.md` files; check what happens with unsupported files.
- [ ] Deploy to Render with a persistent Turso database; perform a full remote persistence test.
- [ ] Inspect visual design on desktop and narrow screens; correct any UX issues found.
- [ ] Record the product walkthrough only after verifying these outcomes.

The AI was a coding accelerator, not the product owner or the source of truth. Decisions about scope and correctness should ultimately be supported by demonstrable behavior, tests, and a candid explanation of limitations.
