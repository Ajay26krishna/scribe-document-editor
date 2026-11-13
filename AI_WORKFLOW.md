# AI-native workflow and verification — Scribe

**Candidate:** Ajay Krishna Devulapally  
**Project:** Scribe, Ajaia AI-Native Full Stack Developer assignment

## Tools and roles

- **ChatGPT (GPT-6):** helped narrow the assignment into a manageable product slice; drafted the initial FastAPI API, storage adapter, Quill-based interface, test scaffolding, and documentation; helped diagnose errors and explain deployment steps.
- **pytest + FastAPI TestClient:** ran the automated checks. **Chrome/browser:** used for local and live end-to-end manual testing. These are verification tools, not AI tools.
- **GitHub, Render, Turso:** source hosting, deployment, and durable cloud persistence. These are infrastructure services, not AI tools.

## Where AI saved time

ChatGPT reduced initial boilerplate work, including routes, validations, the document/sharing interface, persistence wiring, and test cases. More importantly, it helped sequence the work: first get creation, editing, autosave, importing, and sharing working locally; then deploy and prove remote persistence before preparing the final handoff.

## AI output I reviewed, fixed, or rejected

1. **Italic formatting bug:** bold and other editor formats worked, but italic did not display correctly. I tested the problem in the browser and changed `font-synthesis: none` to `auto`, plus loaded actual italic font variants from Google Fonts. I confirmed italic rendering worked afterward.
2. **Test setup:** initial pytest import/discovery needed a `pythonpath` configuration in `pytest.ini`. The test suite was rerun after the correction.
3. **Persistence/deployment decision:** local SQLite was appropriate for development but not sufficient on Render's ephemeral free filesystem. I used Turso for the deployed database instead of accepting a demo that would lose documents on service restarts.
4. **Scope choices:** rejected an attempt to recreate full Google Docs features. Real-time coauthoring, `.docx`, comments, OAuth, and version history were postponed in favor of working role-based sharing and saved rich text.

## How I verified the result

- Ran the local automated tests: **7 passing tests**, including document operations, formatted content round trips, sharing permissions, and remote-adapter serialization.
- Tested Scribe locally on Windows, including document creation, formatting, italic, save/reopen, import, and the two demo accounts.
- Deployed the project using GitHub and Render, configured the database via environment variables, and tested the live website's primary workflows.
- Opened `/healthz` on the deployed service and confirmed the storage mode was **`turso`**.
- Created a persistence test document through the live website and verified that the corresponding row was present in the hosted Turso database. I treated that readback as stronger evidence than a dashboard usage counter.

## Limits and judgment

The tests do not prove full production security or simultaneous collaboration. Demo account switching is intentionally simulated. The remote adapter has protocol-level automated coverage and live manual verification, but not an automated end-to-end integration suite against a disposable Turso instance. The next quality additions would be actual identity enforcement, better conflict recovery, and Playwright UI regression tests.

**Use of AI was disclosed rather than hidden.** I treated generated code as a starting implementation, checked behavior manually, fixed defects, and made the deployment and scope decisions needed to ship a working product slice.
