# ADR-001: Site Architecture (v1)

**Status**: Proposed

**Date**: 11-10-2025

**Y-Statement**: I will pull source docs from Google Drive in CI, compile them to Hugo content with Python, and publish via GitHub Pages, accepting reliance on GitHub Secrets and Google Drive availability.

## Context
I am building a Hugo site with 5 main tabs: Grammar, Vocabulary, Verbs, Writing, Phrases. 

Tools allowed: Hugo, Bootstrap, GitHub, GitHub Actions, GitHub Pages, Hugo theme, Python.

## Decision
Deployment:
Trigger is push to main. Steps are fetch Drive, validate schema, split with Python, Hugo build, deploy with `actions/deploy-pages`. If any step fails, the job stops. no partial deploy.
  
Theme strategy:
Only navbar/footer partials and site color tokens; no layout rewrites in v1.

Classification:
Authors choose values in `sectionmeta` from controlled vocabulary provided in `template`; Python compiles those values into `tags` in front matter; `taxonomies: {tag: 'tags'}` are enabled. Tag index pages exist but are not linked in the v1 UI.

URLs/Nav:
Use sectioned URLs: /grammar/<slug> etc. Content lives under `content/grammar`, `content/vocabulary`, etc. Hugo permalinks map sections accordingly. Slugs must be unique per section. Generator enforces and CI fails on duplicates. 

## Rationale
- Decision drivers
  - low authoring friction: authors edit single Drive doc. no Git/Hugo/CI
  - maintainability by one dev: no repeated time consuming maintainance
  - future theme swap: allow customization of website visuals in the future
- Constraints and context
  - solo maintainer: no repeated maintainance 
  - time-box for v1: deliver a working prototype in two days
  - no server auth on Pages: static hosting; no login without an external gate
- Options considered
  - manual local build: automated CI preferred to reduce errors and increase reproducibility
  - netlify pages: adds new platform and increases time cost
  - flat URLs: sectioned URLs reduce slug collisions and improve navigation clarity under time constraints
- Why this option wins 
  - this separates content (Drive) from site code (Hugo) and deploy (Pages). minimizing lock-in and keeping theme swaps cheap
  - fastest path to working prototype
- Reversibility
  - theme swap: low-cost (partials + styles only)
  - URL model change later to flat: medium cost (generator path change + `permalinks` + redirects)
  - host move: low-cost (reuse build; change deploy step)

## Consequences
- Positive impacts
  - authors only touch one doc
  - theme is replaceable or overwritable even within v1
  - filtered lists (for tags) are given for free by Hugo
- Negative impacts/trade-offs
  - GitHub Pages provides no built-in authentication. The site is public unless protected by an external gate or moved to a different host
  - CI depends on drive availability
- Operational
  - Secrets in GitHub secrets (`DRIVE_SA_JSON`, `DRIVE_FOLDER_ID`) with least privilege and rotated quarterly
  - Drive fetch retries on HTTP 429/5xx with exponential backoff (e.g., 1s, 2s, 4s, then fail) 
  - cache downloads by file ID/etag to reduce API calls while skipping unchanged files 
  - fail loud: if fetch/split/validate fails, deploy stops and surface logs
  - nightly scheduled run saves a zipped source snapshots as a build artifact
- Risks and mitigations
  - credentials leak: mitigated via least-privileged Secret Authorization and Secret rotation
  - Drive quota: compressed sources
  - schema drift: CI schema validator
  - Drive permission/expiry: monitor fetch failures. Document manual re-run. Keep a minimal `how to re-authorize` runbook.
- Debt
  - SEO pass deferred
  - search deferred
  - performance tuning deferred (will be revisited when performance is very bad)