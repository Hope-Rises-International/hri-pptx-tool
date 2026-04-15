# Claude Code — Project Instructions

> **Repository Visibility:** All HRI repos MUST be set to **Private**.
> When creating a new repo from this template, verify the visibility
> is set to Private in the GitHub creation dialog. Public repos risk
> exposing hardcoded credentials, Sheet IDs, and internal email addresses.

## About this project

<!-- Replace this section with a brief description of what this project is,
     how it's deployed, and what systems it connects to. Keep it to 5-10 lines.
     This is the first thing a new session reads — make it count. -->

## Authentication

This project authenticates via GCP service account impersonation. All API calls
(Sheets, Cloud Run, Salesforce, Secret Manager) go through:

    hri-sfdc-sync@hri-receipt-automation.iam.gserviceaccount.com

Developers authenticate with their own @hoperises.org account and impersonate
the service account. Setup:

    gcloud auth application-default login \
      --impersonate-service-account hri-sfdc-sync@hri-receipt-automation.iam.gserviceaccount.com

Do NOT use personal ADC (`gcloud auth application-default login` without
impersonation). Do NOT create or download service account key files.

## Comprehension Artifacts (required for every build)

**The full protocol lives in one place:** `comprehension-artifacts.md` in `hri-template-repository`.

Every build must produce three files: `SPEC.md` (committed before implementation), then `ARCHITECTURE.md` + `REVIEW.md` (generated after implementation, held for user review before committing). For Phase 2+ work, update rather than regenerate.

At build start, fetch and follow it:

```bash
gh api /repos/Hope-Rises-International/hri-template-repository/contents/comprehension-artifacts.md \
  --jq '.content' | base64 -d > /tmp/comprehension-artifacts.md
```

Then read `/tmp/comprehension-artifacts.md` and execute all steps.

## Stack Learnings (canonical source)

Stack-level learnings live in ONE place:
- Repo: `Hope-Rises-International/hri-template-repository`
- File: `hri-stack-learnings.md`
- Read before any infrastructure, auth, deployment, or tooling work.
- Update directly via GitHub API when you discover a stack-level gotcha. See session-end protocol below.

Do NOT create a local `learnings.md` or `hri-stack-learnings.md` in this repo. If one exists, merge any unique content upstream and delete the local copy.

## Project knowledge

<!-- This section grows over time. Every session that makes meaningful changes
     should append what it learned. This is where compound value accrues.

     Good entries answer: What would the NEXT session need to know?
     - Decisions made and WHY (not just what changed — git log has that)
     - Things that are fragile or non-obvious
     - What was tried and didn't work (so nobody tries it again)
     - Patterns discovered in the data or the APIs
     - Gotchas that aren't obvious from reading the code

     Bad entries: "Updated foo.py" (that's a commit message, not knowledge) -->

2026-04-13: SF API credentials migrated from bsimmons@hoperises.org to gcpuser@hoperises.org (API Only User profile). Three secrets updated in Secret Manager: sfdc-username, sfdc-password, sfdc-security-token. Connected App (HRI_Cloud_Sync) unchanged.

2026-04-15: Phase 1-3 complete. Markdown parser (8 slide types), PPTX builder using python-pptx with template txBody deep-copy (fixes Google Slides export artifacts — bare bodyPr/lstStyle blocking inheritance, 222% line spacing), Flask frontend, Cloud Run deploy. Key learnings:
- python-pptx placeholder dict access (`0 in slide.placeholders`) fails on Google Slides templates — must iterate
- `.text` setter clobbers layout bodyPr/lstStyle with bare elements, blocking inheritance. Fix: deep-copy entire txBody from layout, inject text, replace slide-level txBody
- Google Slides exports 222% line spacing on title placeholders — override anything >150% to 100%
- Org policy blocks `allUsers` IAM on Cloud Run. Use `--no-invoker-iam-check` for browser-facing tools
- Service URL: https://hri-pptx-tool-1049804221584.us-east1.run.app
- Portal card added under Comms & Info in hri-internal-portal
- Brand skill updated with Deck Builder decision gate and markdown schema (replaces old PPTX build instructions)

---

## Session Start

**The full protocol lives in one place:** `session-start-protocol.md` in `hri-template-repository`.

At session start, fetch and follow it:

```bash
gh api /repos/Hope-Rises-International/hri-template-repository/contents/session-start-protocol.md \
  --jq '.content' | base64 -d > /tmp/session-start-protocol.md
```

Then read `/tmp/session-start-protocol.md` and execute all steps.

---

## Session-End Protocol

**The full protocol lives in one place:** `session-end-protocol.md` in `hri-template-repository`.

At session close, fetch and follow it:

```bash
gh api /repos/Hope-Rises-International/hri-template-repository/contents/session-end-protocol.md \
  --jq '.content' | base64 -d > /tmp/session-end-protocol.md
```

Then read `/tmp/session-end-protocol.md` and execute all steps.

This ensures every repo uses the latest protocol without needing per-repo updates.
