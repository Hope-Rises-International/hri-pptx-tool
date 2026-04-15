"""Tests for the markdown parser."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parser import parse_markdown


def test_frontmatter_generates_title_slide():
    md = "---\ntitle: Test Deck\nsubtitle: Sub\ndate: April 2026\n---\n"
    slides = parse_markdown(md)
    assert len(slides) == 1
    assert slides[0].slide_type == "TITLE"
    assert slides[0].title == "Test Deck"
    assert slides[0].metadata["subtitle"] == "Sub"
    assert slides[0].metadata["date"] == "April 2026"


def test_missing_frontmatter():
    md = "# CONTENT: A Slide\n- Bullet one\n"
    slides = parse_markdown(md)
    assert len(slides) == 1
    assert slides[0].slide_type == "CONTENT"


def test_content_slide():
    md = "# CONTENT: Revenue Grew 40%\n- Point one\n- Point two\n- Point three\n"
    slides = parse_markdown(md)
    assert len(slides) == 1
    assert slides[0].title == "Revenue Grew 40%"
    assert len(slides[0].bullets) == 3
    assert slides[0].bullets[0] == "Point one"


def test_section_slide_with_color():
    md = "# SECTION: Financial Performance\ncolor: tide\n"
    slides = parse_markdown(md)
    assert len(slides) == 1
    assert slides[0].slide_type == "SECTION"
    assert slides[0].metadata["color"] == "tide"


def test_section_default_color():
    md = "# SECTION: No Color Specified\n"
    slides = parse_markdown(md)
    assert len(slides) == 1
    assert slides[0].slide_type == "SECTION"


def test_kpi_slide():
    md = "# KPI: Key Metrics\n- $4.8M | Revenue\n- 12% | Growth\n- 340 | New Donors\n"
    slides = parse_markdown(md)
    assert len(slides) == 1
    assert slides[0].slide_type == "KPI"
    assert len(slides[0].kpi_items) == 3
    assert slides[0].kpi_items[0] == ("$4.8M", "Revenue")
    assert slides[0].kpi_items[1] == ("12%", "Growth")
    assert slides[0].kpi_items[2] == ("340", "New Donors")


def test_two_col_slide():
    md = """# TWO-COL: Comparison
left:
- Left point one
- Left point two
right:
- Right point one
- Right point two
"""
    slides = parse_markdown(md)
    assert len(slides) == 1
    assert slides[0].slide_type == "TWO-COL"
    assert slides[0].metadata["left_bullets"] == ["Left point one", "Left point two"]
    assert slides[0].metadata["right_bullets"] == ["Right point one", "Right point two"]


def test_quote_slide():
    md = "# QUOTE: Words of Hope\nquote: The future is bright.\nattribution: Bill Simmons\n"
    slides = parse_markdown(md)
    assert len(slides) == 1
    assert slides[0].slide_type == "QUOTE"
    assert slides[0].metadata["quote"] == "The future is bright."
    assert slides[0].metadata["attribution"] == "Bill Simmons"


def test_blank_slide():
    md = "# BLANK:\n"
    slides = parse_markdown(md)
    assert len(slides) == 1
    assert slides[0].slide_type == "BLANK"


def test_photo_slide():
    md = "# PHOTO: Field Work\n- Caption point one\n- Caption point two\n"
    slides = parse_markdown(md)
    assert len(slides) == 1
    assert slides[0].slide_type == "PHOTO"
    assert len(slides[0].bullets) == 2


def test_unknown_keyword_defaults_to_content():
    md = "# CHART: Revenue Breakdown\n- Item one\n- Item two\n"
    slides = parse_markdown(md)
    assert len(slides) == 1
    assert slides[0].slide_type == "CONTENT"


def test_empty_slide_skipped():
    md = "# CONTENT: Has Content\n- A bullet\n\n# CONTENT:\n\n# CONTENT: Also Has Content\n- Another bullet\n"
    slides = parse_markdown(md)
    assert len(slides) == 2
    assert slides[0].title == "Has Content"
    assert slides[1].title == "Also Has Content"


def test_extra_blank_lines():
    md = "\n\n# CONTENT: Spaced Out\n\n\n- Bullet one\n\n- Bullet two\n\n"
    slides = parse_markdown(md)
    assert len(slides) == 1
    assert len(slides[0].bullets) == 2


def test_full_sample_input():
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "sample_input.md")
    with open(fixture_path) as f:
        md = f.read()
    slides = parse_markdown(md)
    assert len(slides) == 10

    # Check slide types in order
    expected_types = ["TITLE", "SECTION", "CONTENT", "KPI", "TWO-COL",
                      "QUOTE", "SECTION", "CONTENT", "CONTENT", "BLANK"]
    for i, (slide, expected) in enumerate(zip(slides, expected_types)):
        assert slide.slide_type == expected, f"Slide {i}: expected {expected}, got {slide.slide_type}"


def test_empty_input():
    assert parse_markdown("") == []
    assert parse_markdown("   ") == []


def test_frontmatter_only():
    md = "---\ntitle: Just a Title\n---\n"
    slides = parse_markdown(md)
    assert len(slides) == 1
    assert slides[0].slide_type == "TITLE"


def test_case_insensitive_keyword():
    md = "# content: Lower Case\n- A bullet\n"
    slides = parse_markdown(md)
    assert len(slides) == 1
    assert slides[0].slide_type == "CONTENT"
