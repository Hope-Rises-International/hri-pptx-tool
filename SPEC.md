# HRI Deck Builder — Build Specification v1.0

**Date:** April 14, 2026
**Repo:** `Hope-Rises-International/hri-deck-builder`
**GCP Project:** `hri-receipt-automation`
**Service:** `hri-deck-builder` (Cloud Run)
**Owner:** Bill Simmons

---

## Problem

Producing branded PPTX presentations from claude.ai is slow, expensive, and unreliable. The skill-based approach burns 30%+ of a Pro session on multi-step tool chains (HTML rendering, thumbnail validation loops, slide-by-slide adjustments). Output quality varies by session. The branded template exists and works — the bottleneck is the generation pipeline, not the design.

## Solution

A Cloud Run web service that accepts structured markdown and produces a branded PPTX in one HTTP request. The user pastes markdown from any claude.ai session into a web form, clicks Generate, and downloads a finished deck. All brand rules (colors, layouts, master elements) are baked into the template and code — not re-derived per request.

## Architecture

```
User (browser)
  ↓ paste markdown + click Generate
Cloud Run (Python/Flask)
  ↓ parse markdown → map to slide types → inject into template
  ↓ return PPTX as file download
User's Downloads folder
```

**No external dependencies.** No Salesforce, no Google Sheets, no Secret Manager, no scheduled jobs. Stateless: markdown in, PPTX file out.

## Data Flow

1. User opens `https://hri-deck-builder-[hash]-ue.a.run.app` (linked from Internal Tools Portal)
2. Pastes structured markdown into a textarea
3. Clicks "Generate Deck"
4. Frontend POSTs markdown to `/generate` endpoint
5. Backend parses markdown into slide objects
6. python-pptx loads `presentation_template.pptx`, adds slides from the appropriate layouts, injects content into placeholders
7. Deletes the 12 sample slides that ship with the template
8. Returns PPTX with `Content-Disposition: attachment` header
9. Chrome downloads the file

---

## Markdown Schema

The markdown schema defines how claude.ai session output maps to slide types. This is the contract between the person writing content and the builder. It must be simple enough to produce in conversation without a reference card.

### Syntax

```
---
title: Deck Title Here
subtitle: Optional Subtitle
date: April 2026
---

# TITLE: Main Presentation Title
subtitle: A supporting statement

# SECTION: First Major Section
color: tide

# CONTENT: Revenue Grew 40% Driven by Enterprise Expansion
- First supporting point with detail
- Second supporting point with detail
- Third supporting point with detail

# TWO-COL: Pipeline Results Show Clear Segmentation Advantage
left:
- Left column point one
- Left column point two
right:
- Right column point one
- Right column point two

# KPI: Q3 Performance Exceeded All Benchmarks
- $4.8M | Public Fundraising Revenue
- 12% | Year-over-Year Growth
- 340 | New Donors Acquired
- 87% | Retention Rate

# QUOTE: Words of Affirmation
quote: We haven't failed to execute the plan — we've failed to become the kind of people who can obey.
attribution: Bill Simmons

# CONTENT: Closing Recommendations for the Board
- Recommendation one with rationale
- Recommendation two with rationale
```

### Slide Type Mapping

| Markdown Keyword | Template Layout | Master | Description |
|---|---|---|---|
| `TITLE` | Layout 0 (TITLE) | Master 0 | Opening slide. Light blue bg, star watermark. |
| `SECTION` | Restore/Golden/Tide/Rising Sun | Master 2 | Section divider. `color:` selects variant. Default: Tide. |
| `CONTENT` | Layout 0 (OBJECT) | Master 1 | Full-width content slide. Title + bullets. |
| `TWO-COL` | Layout 15 (TWO_OBJECTS) | Master 1 | Side-by-side columns. |
| `KPI` | Layout 3 (TITLE_ONLY) | Master 1 | Metric cards built as shapes. |
| `QUOTE` | Layout 2 (Pullquote) | Master 1 | Quote right, optional body left. |
| `PHOTO` | Layout 1 (Photo 1) | Master 1 | Content left, photo placeholder right. |
| `BLANK` | Layout 17 (BLANK) | Master 1 | Empty canvas, master elements only. |

### Content Rules (enforced by parser)

- Title line after `#` keyword = the slide headline (complete sentence, not a topic label)
- Bullets: max 5 per slide, each displayed as-is (no word count enforcement — that's the author's job)
- KPI format: `- VALUE | LABEL` where VALUE is the big number and LABEL is the descriptor
- SECTION `color:` accepts: `tide`, `golden`, `restore`, `risingsun` (case-insensitive)
- Lines starting with `subtitle:`, `quote:`, `attribution:`, `left:`, `right:`, `color:` are metadata, not content
- Everything else on a line is body content

### Parser Behavior

- Frontmatter (`---` delimited YAML) is optional. If present, `title` populates a generated title slide as the first slide.
- Each `# KEYWORD:` line starts a new slide. Everything between two `#` lines belongs to the preceding slide.
- Unknown keywords default to CONTENT layout.
- Empty slides (keyword with no content below it) are skipped.
- The parser is forgiving: extra blank lines, inconsistent indentation, missing metadata keys — all handled gracefully. The goal is to accept anything a claude.ai session would reasonably produce.

---

## Template Integration

### Source Template

`presentation_template.pptx` (11MB) — the existing HRI branded template from the project's brand assets. Contains 3 slide masters, 26 layouts, and 12 sample slides.

### How Slide Generation Works

python-pptx's `prs.slides.add_slide(layout)` creates a new slide from a layout. The slide inherits all master-level elements automatically:

- Watercolor blue wave (full-width at bottom)
- HRI compact logo (bottom-right)
- Golden decorative underline (under title)
- Slide number

These elements do NOT need to be manually added. If they're missing, the template wasn't loaded correctly.

### Placeholder Injection

For each slide, the builder:
1. Selects the layout by index from the correct master
2. Calls `prs.slides.add_slide(layout)`
3. Accesses placeholders by `idx` (title is always `idx=0`, body is `idx=1`)
4. Sets `placeholder.text` for simple content, or iterates `text_frame.paragraphs` for bullet lists
5. For KPI slides (TITLE_ONLY layout), creates shapes programmatically: colored rectangles with large-font numbers and small-font labels

### Sample Slide Cleanup

The template ships with 12 example slides. After generating all new slides, delete the originals. The builder tracks the original slide count on load and removes slides at indices 0 through (original_count - 1) after appending new content.

### Font Handling

The template specifies Golos Text. python-pptx writes the font name into the XML. The font renders correctly on any machine that has Golos Text installed (all HRI machines via Google Fonts). On machines without it, PowerPoint substitutes automatically — acceptable for external distribution.

---

## Frontend

A single HTML page served by the same Flask app at `/`.

### Elements

- HRI branded header (Tide background, white text, logo)
- Textarea (full width, ~20 rows) with placeholder text showing the markdown schema
- "Generate Deck" button (Rising Sun background, white text)
- Optional: filename input (defaults to `deck.pptx`)
- Footer with version number

### Behavior

- POST to `/generate` with markdown body
- On success: browser downloads PPTX file
- On error: display error message inline (red text below button)
- No JavaScript frameworks. Vanilla HTML/CSS/JS. The entire frontend is one file served inline.

### Brand Compliance

- Background: White with Cleanse (#F7EDE8) accent sections
- Header bar: Tide (#1E5773) background
- Button: Rising Sun (#F26044) with white text
- Body text: Black (#000000)
- Font: System fonts (the frontend doesn't need Golos Text — the PPTX output does)
- Logo: HRI star icon in header

---

## Backend

### Stack

- Python 3.11+
- Flask (HTTP server)
- python-pptx (PPTX generation)
- PyYAML (frontmatter parsing)
- gunicorn (production server)

### Endpoints

| Route | Method | Purpose |
|---|---|---|
| `/` | GET | Serve the HTML frontend |
| `/generate` | POST | Accept markdown, return PPTX |
| `/health` | GET | Health check (returns 200) |

### `/generate` Logic

1. Read raw markdown from request body
2. Parse frontmatter (if present) with PyYAML
3. Split on `# KEYWORD:` lines to produce a list of slide objects
4. For each slide object:
   - Map keyword to layout index
   - Parse content (bullets, metadata lines, KPI values)
5. Load `presentation_template.pptx` from the repo's `assets/` directory
6. Record the count of existing sample slides
7. For each slide object, add a slide from the mapped layout and inject content
8. Delete the original sample slides (indices 0 through original_count - 1)
9. Save to BytesIO buffer
10. Return buffer as response with PPTX content type and attachment disposition

### Error Handling

- Empty markdown → 400 with message "No content provided"
- No valid slide keywords found → 400 with message "No slides detected. Each slide starts with # KEYWORD: Title"
- python-pptx errors → 500 with generic message + server-side logging
- Template file missing → 500 with message (this is a deployment error, not user error)

### File Structure

```
hri-deck-builder/
├── CLAUDE.md
├── SPEC.md
├── ARCHITECTURE.md
├── REVIEW.md
├── Dockerfile
├── requirements.txt
├── main.py              # Flask app with all endpoints
├── parser.py            # Markdown → slide objects
├── builder.py           # Slide objects → PPTX via python-pptx
├── templates/
│   └── index.html       # Frontend (served inline by Flask)
├── assets/
│   ├── presentation_template.pptx
│   └── logo_icon.png    # For frontend header
└── tests/
    ├── test_parser.py
    ├── test_builder.py
    └── fixtures/
        └── sample_input.md
```

---

## GCP Deployment

### Cloud Run Configuration

- **Service name:** `hri-deck-builder`
- **Region:** `us-east1`
- **Memory:** 512 MB (the 11MB template loads into memory per request)
- **CPU:** 1
- **Timeout:** 60 seconds
- **Concurrency:** 10
- **Min instances:** 0 (scale to zero when idle)
- **Max instances:** 3
- **Invoker:** `allUsers` — no IAM gate (consistent with other portal tools; Google Workspace login on the portal itself provides the access boundary)
- **No Secret Manager needed** — no external API credentials
- **No Cloud Scheduler needed** — on-demand only

### Dockerfile

Standard Python Cloud Run pattern:
- Base: `python:3.11-slim`
- Copy requirements.txt, install
- Copy application code + assets
- Expose port 8080
- CMD: gunicorn

### Portal Integration

Add a new card to the Internal Tools Portal (Apps Script web app):
- Card title: "Deck Builder"
- Card description: "Generate branded presentations from markdown"
- Card link: Cloud Run service URL
- Badge: "Live"
- Icon: presentation/slides emoji

---

## Phased Build Plan

### Phase 1: Parser + Builder Core (no frontend, no deployment)

**Scope:** Build the markdown parser and PPTX builder as standalone Python modules. Test locally with a sample markdown file producing a PPTX on disk.

**What to build:**
- `parser.py` — Markdown string → list of SlideSpec dataclass objects
- `builder.py` — List of SlideSpec objects + template path → PPTX bytes
- `tests/test_parser.py` — Unit tests for all slide types, edge cases (empty content, unknown keywords, missing frontmatter)
- `tests/test_builder.py` — Integration tests that produce actual PPTX files and verify slide count, title text, layout indices
- `tests/fixtures/sample_input.md` — A 10-slide sample covering all 8 slide types

**SlideSpec dataclass:**
```
@dataclass
class SlideSpec:
    slide_type: str          # TITLE, SECTION, CONTENT, TWO-COL, KPI, QUOTE, PHOTO, BLANK
    title: str               # Headline text
    bullets: list[str]       # Body bullet points
    metadata: dict           # subtitle, color, quote, attribution, left, right
    kpi_items: list[tuple]   # [(value, label), ...] for KPI slides
```

**Template handling:**
- Copy `presentation_template.pptx` from brand assets into `assets/`
- First action in builder: load template, enumerate all layouts across all masters, print layout index + name + master index + placeholder indices
- This diagnostic output becomes the definitive layout map. If the indices don't match the brand skill's documentation, the brand skill's indices govern and the code adapts.

**Validation gate:**
- [ ] Parser correctly identifies all 8 slide types from sample input
- [ ] Parser handles: missing frontmatter, extra blank lines, unknown keywords (defaults to CONTENT)
- [ ] Builder produces a valid PPTX that opens in PowerPoint without repair prompts
- [ ] All sample slides use correct layouts (verify by opening in PowerPoint and checking slide master assignments)
- [ ] Master elements (watercolor wave, logo, golden underline) appear on all Master 1 slides
- [ ] KPI cards render as colored rectangles with correct brand colors
- [ ] Sample slides from template are deleted — only generated slides remain
- [ ] Slide dimensions are 13.333" x 7.500"

**STOP after Phase 1.** Bill opens the generated PPTX in PowerPoint, reviews every slide, and confirms layout/brand compliance before proceeding. This is the critical gate — if the template integration is wrong, nothing downstream matters.

---

### Phase 2: Flask App + Frontend

**Scope:** Wrap the parser and builder in a Flask web server. Build the HTML frontend. Test locally with `flask run`.

**What to build:**
- `main.py` — Flask app with `/`, `/generate`, `/health` routes
- `templates/index.html` — Branded frontend page
- `requirements.txt` — Flask, python-pptx, PyYAML, gunicorn

**Frontend details:**
- The textarea should include placeholder text showing the full markdown schema as an example
- The Generate button should disable during processing and show a spinner or "Generating..." text
- Error messages appear below the button in Rising Sun (#F26044) text
- The page should include a collapsible "Markdown Reference" section below the textarea showing the syntax guide

**Validation gate:**
- [ ] `flask run` serves the frontend at localhost
- [ ] Pasting markdown and clicking Generate downloads a PPTX
- [ ] Error cases (empty input, no slides) display user-friendly messages
- [ ] Frontend renders correctly on Chrome desktop and mobile (Bill uses both)
- [ ] PPTX output from Flask endpoint is identical to Phase 1 CLI output

**STOP after Phase 2.** Bill tests locally — pastes real content from a recent claude.ai session, generates, opens in PowerPoint. Confirms the end-to-end flow works before deploying.

---

### Phase 3: Cloud Run Deployment + Portal

**Scope:** Containerize, deploy to Cloud Run, add to portal.

**What to build:**
- `Dockerfile`
- Cloud Run deployment via `gcloud run deploy`
- IAM: `allUsers` invoker permission
- Portal card addition (update the Apps Script portal code to add the new card)

**Post-deploy verification:**
- [ ] Cloud Run service responds to `/health`
- [ ] Frontend loads at the Cloud Run URL
- [ ] Generate flow produces and downloads a PPTX
- [ ] PPTX opens in PowerPoint without repair prompts
- [ ] Portal card links to the service and opens correctly
- [ ] **Collateral damage check:** List all Cloud Scheduler jobs in `hri-receipt-automation`, force-run each, confirm successful invocation in Cloud Run logs
- [ ] Systems Registry updated with new service entry

**STOP after Phase 3.** Service is live. Bill does a full test from the portal link.

---

## Future Enhancements (not in scope for initial build)

- **Photo injection:** Accept image URLs or uploaded images for PHOTO slide type (requires file upload handling)
- **Chart generation:** Accept data tables in markdown and produce matplotlib charts embedded in slides
- **Template selection:** Multiple templates (board deck, staff presentation, external pitch) with a dropdown
- **Batch mode:** Accept a Google Doc ID, fetch content via Drive API, generate deck (requires Secret Manager for OAuth)
- **Edit mode:** Upload an existing PPTX + markdown corrections, produce an updated deck

---

## Dependencies

| Dependency | Status | Notes |
|---|---|---|
| `presentation_template.pptx` | Exists in brand assets (11MB) | Copy to repo `assets/` |
| `logo_icon.png` | Exists in brand assets | Copy to repo `assets/` for frontend |
| `hri-receipt-automation` GCP project | Active | Same project as all FIS services |
| Internal Tools Portal | Active | Apps Script web app, needs new card |
| python-pptx library | PyPI, stable | v1.0.0 current |
| No Salesforce access needed | — | — |
| No Secret Manager needed | — | — |
| No Google Sheets needed | — | — |

---

## Risk Assessment

**Low risk overall.** This is the simplest Cloud Run service in the portfolio — no external API dependencies, no credentials, no scheduled jobs, no data to corrupt.

**Primary risk:** Template layout indices may not match the brand skill documentation. The Phase 1 diagnostic (enumerate all layouts) eliminates this on first run. If indices differ, the code adapts to actual indices.

**Secondary risk:** python-pptx's handling of complex template masters (watercolor wave is a grouped shape, golden underline is an image, logo is an image). These are on the slide master, not individual slides, so `add_slide()` from a layout should inherit them. Phase 1 validation confirms this. If inheritance fails for specific elements, fallback is to add them programmatically per slide — ugly but functional.

**Not a risk:** Font rendering. Golos Text is specified in the template XML. python-pptx preserves it. PowerPoint handles substitution on machines without the font.

---

## Spec Quality Checklist

- [x] Can Claude Code build this without asking any clarifying questions?
- [x] Are all data transformations specified at the field level? (N/A — no data pipeline)
- [x] Are error cases handled explicitly?
- [x] Is the expected scale stated? (Single-user, on-demand, <10 requests/day)
- [x] Are acceptance criteria testable?
- [x] Is the build chunked into phases with clear boundaries?
- [x] Are all external dependencies identified and their status known?
