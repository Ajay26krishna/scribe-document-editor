# Architecture and trade-offs — Scribe

## Problem framing

The most valuable deliverable within 4–6 hours is not a Google Docs clone; it is a trustworthy document workflow. I prioritized *create → edit → autosave → reopen* and *owner → share → switch account → confirm enforcement*. Both are demonstrable in a short video.

## High-level flow

```text
Browser (HTML/CSS/JS, Quill editor)
            |
        JSON + multipart
            |
      FastAPI REST routes
            |
    Server-side validation
    + authorization checks
            |
      Storage abstraction
      /               \
SQLite file (local)   Turso/libSQL HTTP (deployed)
```

- **Document data** is stored as **Quill Delta JSON**, not raw HTML; formatting is preserved, and only approved text operations and attributes can be saved.
- **Users** are two seeded accounts (`maya`, `noah`). A demo cookie chooses the identity; this is a simulated sign-in by design. This is not secure authentication.
- **Roles:** owner (read/edit/share/delete), editor (read/edit), viewer (read only), and unshared (no access).
- **Authorization:** GET, PATCH, DELETE and sharing routes re-evaluate document ownership or membership in the `shares` table. Documents inaccessible to the acting user return `404`.
- **Autosave:** client debounces by 700 ms and sends the latest title and Delta. `revision` supports optimistic concurrency; stale saves return HTTP 409 rather than silently overwriting the document. Writes in flight are serialized in the client.
- **Import:** uploaded bytes are UTF-8 decoded, length-checked, and converted into safe Delta text operations. Markdown uses a limited, documented parser rather than arbitrary uploaded HTML.
- **Persistence:** the storage interface accepts bound parameters for both local SQLite and remote Turso. A hosted database avoids losing data when a free Render web service restarts.

## Schema

```text
users(id PK, name, email UNIQUE)
documents(id PK, owner_id FK, title, delta_json, revision, created_at, updated_at)
shares(doc_id FK, user_id FK, role, PRIMARY KEY(doc_id, user_id))
```

All access is evaluated on the server; the account selected in the browser is never accepted as a free-form `owner_id` in write payloads.

## Why this stack?

- **FastAPI + SQLite:** minimal setup, fast iteration, good request-validation support, real integration tests, and easy deployability as one web service.
- **Quill 2:** handles cursor behavior, formatting, lists, and Delta persistence much better than inventing a `contenteditable` editor under time pressure.
- **Vanilla browser JavaScript:** avoids a bundler and keeps the product slice inspectable. For a larger team/product I would choose a component framework and client data-fetching library.
- **Turso for deployment:** retains SQLite semantics while providing persistent storage without paying for a Render disk. No database token is sent to the browser.

## Correctness and limits

- Seven automated tests cover local API behavior and remote Turso protocol serialization. Local API tests validate ownership, shared editing, read-only denial, revocation, rename/format persistence, conflict handling, and import rules.
- The remote Turso path uses the documented Hrana HTTP pipeline protocol; an actual remote-database smoke test is still needed with a real database token.
- Browser rich-text usability needs candidate-led visual/manual testing on a machine with internet access. Browser-based end-to-end automation has not yet been claimed.
- Scope cuts: no simultaneous editing, Google Docs-format import, threaded comments, emailed invites, OAuth, version snapshots, or link-based permission bypass.
- Production hardening would include real identity, CSRF protections, structured audit events, rate limits, file scanning if attachments are added, durable migrations, and observability.
