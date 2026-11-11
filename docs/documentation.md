# Documentation

> **Purpose:** Governs how documents under `docs/` are structured, so a reader can decide whether to open a file from its first lines.
> **Read when:** adding a document under `docs/`, or changing any document's header.
> **Owns:** the document header convention (Purpose / Read when / Owns) and the list of banned "Read when" phrases.

## Header convention

Every document under `docs/` opens with a blockquote header of at most three lines:

```
> **Purpose:** <one line: what this document is>
> **Read when:** <concrete trigger>
> **Owns:** <facts or rules this document is the source of truth for, or "nothing — index only">
```

- **Purpose** states what the document is, not what it contains.
- **Read when** names a concrete trigger a reader can match against their current task. Banned phrases: `when needed`, `as reference`, `for context`, `general guidance`, `overview`, `background`.
- **Owns** matches the owners chosen in the single-source-of-truth work: a document owns a fact only if it is the one place that fact is defined. Everything else links to the owner.

ADRs keep their existing template and `Status` field; the header is added above `## Status` without changing the status or decision text.

## Exclusions

- `AGENTS.md` and `README.md` are entry files and keep their own format.
- `docs/baselines/` holds measurement artifacts owned by the issue that removes them; they are not living documentation and carry no header.
