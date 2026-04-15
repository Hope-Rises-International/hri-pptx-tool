"""CLI script: reads sample input, produces sample.pptx."""
from parser import parse_markdown
from builder import build_deck

with open("tests/fixtures/sample_input.md") as f:
    md = f.read()

slides = parse_markdown(md)
pptx_bytes = build_deck(slides, "assets/presentation_template.pptx")

with open("sample_output.pptx", "wb") as f:
    f.write(pptx_bytes)

print(f"Generated {len(slides)} slides -> sample_output.pptx")
for i, s in enumerate(slides):
    print(f"  [{i}] {s.slide_type}: {s.title[:60]}")
