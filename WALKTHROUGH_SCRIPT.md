# Suggested 3–5 minute walkthrough (record after verifying the deployment)

**0:00–0:25 — Intent and scope**  
"I built Scribe as a focused document workspace. I prioritized a clean write-save-share flow rather than reimplementing every Google Docs feature."

**0:25–1:25 — Create, edit, autosave, reopen**  
Start as Maya. Create a document, rename it, type paragraphs, apply bold / heading / list formatting, wait for *All changes saved*, go back to the dashboard, reopen. Refresh the live page to demonstrate persistence.

**1:25–2:05 — File import**  
Import `sample-import.md` or a small `.txt` file. Explain that `.md` is limited to basic formatting and `.docx` support was intentionally excluded.

**2:05–3:10 — Share and permission check**  
Click Share as Maya; invite Noah with *Can edit*. Switch account from the top-right and find it in *Shared with me*. Modify the document as Noah. Switch back to Maya, set the permission to *Can view*. Switch to Noah; show disabled editing. Finally revoke access and demonstrate that Noah can no longer open the document.

**3:10–4:00 — Implementation choices**  
Mention FastAPI, SQLite locally, Turso remotely, Quill Delta JSON for formatting, backend authorization, revision-based conflict rejection, and automated tests. Explain why a hosted database is necessary on free Render.

**4:00–4:30 — AI and trade-offs**  
Explain which parts you accelerated with ChatGPT, what you changed or rejected, how you tested, what is missing (real auth, simultaneous editing, complete Markdown), and which improvement comes next.

**Before recording:** Use the actual deployed URL and visually verify everything. Keep the demo within five minutes. Share the recording as an unlisted Loom/YouTube link and put that URL in `walkthrough_url.txt`.
