"""Markdown parser for HRI Deck Builder. Converts structured markdown to SlideSpec objects."""
import re
import yaml
from dataclasses import dataclass, field
from typing import Optional


VALID_KEYWORDS = {"TITLE", "SECTION", "CONTENT", "TWO-COL", "KPI", "QUOTE", "PHOTO", "BLANK"}
METADATA_KEYS = {"subtitle", "color", "quote", "attribution", "left", "right", "date"}

# Pattern: # KEYWORD: title text
SLIDE_HEADER_RE = re.compile(r"^#\s+([A-Z][A-Z0-9-]*)\s*:\s*(.*)", re.IGNORECASE)


@dataclass
class SlideSpec:
    slide_type: str  # TITLE, SECTION, CONTENT, TWO-COL, KPI, QUOTE, PHOTO, BLANK
    title: str  # Headline text
    bullets: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    kpi_items: list = field(default_factory=list)


def parse_markdown(text: str) -> list:
    """Parse structured markdown into a list of SlideSpec objects."""
    slides = []
    text = text.strip()
    if not text:
        return slides

    # Extract frontmatter if present
    frontmatter = None
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1])
            except yaml.YAMLError:
                frontmatter = None
            body = parts[2]

    # Generate a TITLE slide from frontmatter
    if frontmatter and isinstance(frontmatter, dict) and frontmatter.get("title"):
        meta = {}
        if frontmatter.get("subtitle"):
            meta["subtitle"] = frontmatter["subtitle"]
        if frontmatter.get("date"):
            meta["date"] = frontmatter["date"]
        slides.append(SlideSpec(
            slide_type="TITLE",
            title=frontmatter["title"],
            metadata=meta,
        ))

    # Split body into slide blocks on # KEYWORD: lines
    blocks = _split_into_blocks(body)

    for keyword, title, content_lines in blocks:
        slide = _parse_block(keyword, title, content_lines)
        if slide:
            slides.append(slide)

    return slides


def _split_into_blocks(body: str) -> list:
    """Split markdown body into (keyword, title, content_lines) tuples."""
    blocks = []
    current = None

    for line in body.split("\n"):
        match = SLIDE_HEADER_RE.match(line.strip())
        if match:
            if current:
                blocks.append(current)
            keyword = match.group(1).upper()
            title = match.group(2).strip()
            current = (keyword, title, [])
        elif current:
            current[2].append(line)

    if current:
        blocks.append(current)

    return blocks


def _parse_block(keyword: str, title: str, content_lines: list) -> Optional[SlideSpec]:
    """Parse a single slide block into a SlideSpec."""
    # Normalize keyword
    if keyword not in VALID_KEYWORDS:
        keyword = "CONTENT"

    # BLANK slides are always valid even with no content
    if keyword == "BLANK":
        return SlideSpec(slide_type="BLANK", title=title)

    # For non-BLANK slides, skip if empty (no title and no content)
    lines = [l for l in content_lines if l.strip()]
    if not title and not lines:
        return None

    metadata = {}
    bullets = []
    kpi_items = []

    if keyword == "TWO-COL":
        _parse_two_col(lines, metadata, bullets)
    elif keyword == "KPI":
        _parse_kpi(lines, kpi_items, bullets)
    else:
        _parse_standard(lines, metadata, bullets)

    return SlideSpec(
        slide_type=keyword,
        title=title,
        bullets=bullets,
        metadata=metadata,
        kpi_items=kpi_items,
    )


def _parse_two_col(lines: list, metadata: dict, bullets: list):
    """Parse TWO-COL content into left and right bullet lists."""
    current_side = None
    left_bullets = []
    right_bullets = []

    for line in lines:
        stripped = line.strip()
        if stripped.lower().startswith("left:"):
            current_side = "left"
            # Check if there's content on the same line after "left:"
            rest = stripped[5:].strip()
            if rest and rest.startswith("- "):
                left_bullets.append(rest[2:])
            continue
        elif stripped.lower().startswith("right:"):
            current_side = "right"
            rest = stripped[6:].strip()
            if rest and rest.startswith("- "):
                right_bullets.append(rest[2:])
            continue

        if stripped.startswith("- "):
            bullet_text = stripped[2:]
            if current_side == "right":
                right_bullets.append(bullet_text)
            elif current_side == "left":
                left_bullets.append(bullet_text)
            else:
                bullets.append(bullet_text)
        elif ":" in stripped and not stripped.startswith("- "):
            key, _, val = stripped.partition(":")
            key = key.strip().lower()
            if key in METADATA_KEYS:
                metadata[key] = val.strip()

    metadata["left_bullets"] = left_bullets
    metadata["right_bullets"] = right_bullets


def _parse_kpi(lines: list, kpi_items: list, bullets: list):
    """Parse KPI content into value|label tuples."""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            bullet_text = stripped[2:]
            if " | " in bullet_text:
                value, _, label = bullet_text.partition(" | ")
                kpi_items.append((value.strip(), label.strip()))
            else:
                bullets.append(bullet_text)
        elif ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip().lower()
            if key in METADATA_KEYS:
                pass  # KPI slides don't use metadata besides title


def _parse_standard(lines: list, metadata: dict, bullets: list):
    """Parse standard slide content (CONTENT, SECTION, QUOTE, TITLE, PHOTO)."""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            bullets.append(stripped[2:])
        elif ":" in stripped and not stripped.startswith("- "):
            key, _, val = stripped.partition(":")
            key = key.strip().lower()
            if key in METADATA_KEYS:
                metadata[key] = val.strip()
