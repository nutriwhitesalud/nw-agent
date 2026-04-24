# Knowledge Sources

Place approved company documents here before running the ingest worker.

Supported formats in this scaffold:

- `.md`
- `.txt`
- `.json`

For `.json`, the worker expects either:

- `{ "title": "...", "content": "...", "metadata": { ... } }`
- or a top-level array of objects with the same keys

Only put content here that the customer service agent is allowed to quote or rely on.

