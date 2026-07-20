# Jiak website

Public website, privacy notice, support information, terms, and account-deletion instructions for Jiak.

## Local preview

The site is static and has no runtime dependencies. From the repository root:

```sh
python3 -m http.server 4173
```

Then open `http://localhost:4173`.

Run the dependency-free structural and internal-link checks with:

```sh
python3 scripts/validate_site.py
```

## Pre-publication checklist

- Replace every `[CONTROLLER NAME — REPLACE BEFORE PUBLISHING]` placeholder.
- Resolve and document Jiak's intended age audience and children's-data approach.
- Obtain appropriate legal review of the privacy notice and terms.
- Confirm production processor regions, transfer arrangements, and retention settings.
- Confirm all internal links and required URLs on the deployed domain.
- Keep the draft legal pages out of search results until their placeholders and open legal decisions are resolved.
- Do not change DNS until the exact records have been shown and approved.

## Required public URLs

- `/`
- `/privacy/`
- `/delete-account/`
- `/support/`
- `/terms/`
