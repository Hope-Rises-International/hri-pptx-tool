"""Flask app for HRI Deck Builder. Serves frontend and generates PPTX from markdown."""
import os
import traceback
from flask import Flask, request, render_template, send_file, jsonify
from io import BytesIO

from parser import parse_markdown
from builder import build_deck

app = Flask(__name__)

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "assets", "presentation_template.pptx")


@app.route("/")
def index():
    """Serve the branded frontend."""
    return render_template("index.html")


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"}), 200


@app.route("/generate", methods=["POST"])
def generate():
    """Accept markdown, return PPTX file."""
    markdown = request.get_data(as_text=True)

    if not markdown or not markdown.strip():
        return jsonify({"error": "No content provided"}), 400

    slides = parse_markdown(markdown)
    if not slides:
        return jsonify({"error": "No slides detected. Each slide starts with # KEYWORD: Title"}), 400

    try:
        pptx_bytes = build_deck(slides, TEMPLATE_PATH)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Failed to generate presentation. Please check your markdown and try again."}), 500

    filename = request.args.get("filename", "deck.pptx")
    if not filename.endswith(".pptx"):
        filename += ".pptx"

    buf = BytesIO(pptx_bytes)
    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        as_attachment=True,
        download_name=filename,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
