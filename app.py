"""
PackGuard AI - Flask Web Server & API Routes (app.py)
A clean, robust packaging artwork and compliance checker.
Exposes:
- GET  /              : Serves the single-page application dashboard
- POST /api/analyze   : Multipart upload endpoint for packaging artwork & rulebook
- POST /api/followup  : Follow-up question endpoint regarding findings and regulations
- GET  /api/status    : System status, Gemini API configuration state
- GET  /api/sample    : Returns sample rulebook specification
"""

import os
import json
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

# Load environment configuration
load_dotenv()

import analyzer

app = Flask(__name__, template_folder="templates", static_folder="static")

# Enable reverse proxy support for Render, Cloudflare, Nginx
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# File upload restrictions: 32MB max
MAX_CONTENT_LENGTH = 32 * 1024 * 1024
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH


@app.after_request
def apply_security_headers(response):
    """Inject production HTTP security headers."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

ALLOWED_ARTWORK_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf", ".webp"}
ALLOWED_RULEBOOK_EXTENSIONS = {".txt", ".json", ".pdf", ".xlsx"}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SAMPLE_PRESETS = {
    "granola": {
        "id": "granola",
        "name": "Dancing Fish Granola Cereal Box",
        "badge": "Cereal Box",
        "artwork_path": os.path.join(BASE_DIR, "DancingFish_Granola_Berry_US_Carton (2)4def4e1.pdf"),
        "artwork_filename": "DancingFish_Granola_Berry_US_Carton.pdf",
        "rulebook_path": os.path.join(BASE_DIR, "sample_data", "sample_rulebook.json"),
        "rulebook_filename": "DancingFish_Granola_Rules.json",
        "description": "Standard cereal carton testing net weight dual unit declarations and FALCPA tree nut allergen disclosure."
    },
    "peakfuel": {
        "id": "peakfuel",
        "name": "PeakFuel Protein Bar (Intentional Violations)",
        "badge": "Snack Wrapper",
        "artwork_path": os.path.join(BASE_DIR, "sample_data", "peakfuel_protein_bar", "PeakFuel_ProteinBar_Wrapper.pdf"),
        "artwork_filename": "PeakFuel_ProteinBar_Wrapper.pdf",
        "rulebook_path": os.path.join(BASE_DIR, "sample_data", "peakfuel_protein_bar", "PeakFuel_Spec.json"),
        "rulebook_filename": "PeakFuel_Spec.json",
        "description": "Multi-discrepancy stress test: unapproved medical claim, FALCPA omission, barcode mismatch, trim overflow."
    },
    "apex_brew": {
        "id": "apex_brew",
        "name": "Apex Brew Cold Brew Latte (Compliant Beverage)",
        "badge": "Can Dieline",
        "artwork_path": os.path.join(BASE_DIR, "sample_data", "apex_cold_brew", "ApexBrew_ColdBrew_Can_Artwork.pdf"),
        "artwork_filename": "ApexBrew_ColdBrew_Can_Artwork.pdf",
        "rulebook_path": os.path.join(BASE_DIR, "sample_data", "apex_cold_brew", "ApexBrew_Spec.json"),
        "rulebook_filename": "ApexBrew_Spec.json",
        "description": "High-compliance ready-to-drink beverage dieline with fluid volume net quantity and certification marks."
    },
    "littlesprout": {
        "id": "littlesprout",
        "name": "LittleSprout Baby Puree (Infant Food Pouch)",
        "badge": "Infant Food",
        "artwork_path": os.path.join(BASE_DIR, "sample_data", "littlesprout_baby_puree", "LittleSprout_BabyPuree_Pouch.pdf"),
        "artwork_filename": "LittleSprout_BabyPuree_Pouch.pdf",
        "rulebook_path": os.path.join(BASE_DIR, "sample_data", "littlesprout_baby_puree", "LittleSprout_Spec.json"),
        "rulebook_filename": "LittleSprout_Spec.json",
        "description": "Infant food pouch with FDA choking hazard advisory, stage age verification, and BPA-free claims."
    }
}

SAMPLE_ARTWORK_PATH = SAMPLE_PRESETS["granola"]["artwork_path"]
SAMPLE_RULEBOOK_PATH = SAMPLE_PRESETS["granola"]["rulebook_path"]


def is_allowed_file(filename: str, allowed_extensions: set) -> bool:
    """Check if file has an allowed extension."""
    if not filename or "." not in filename:
        return False
    ext = os.path.splitext(filename)[1].lower()
    return ext in allowed_extensions


@app.route("/")
def index():
    """Serve the single-page dashboard."""
    return render_template("index.html")


@app.route("/health", methods=["GET"])
@app.route("/healthz", methods=["GET"])
def health():
    """Liveness/readiness health check for Render, load balancers, and monitoring."""
    return jsonify({
        "status": "healthy",
        "app_name": "PackGuard AI",
        "version": "1.0.0",
        "gemini_configured": bool(analyzer.get_gemini_api_key())
    }), 200


@app.route("/api/status", methods=["GET"])
def get_status():
    """Return backend status and Gemini configuration state without exposing key."""
    api_key_configured = bool(analyzer.get_gemini_api_key())
    return jsonify({
        "success": True,
        "app_name": "PackGuard AI",
        "version": "1.0.0",
        "gemini_configured": api_key_configured,
        "model": analyzer.get_gemini_model(),
        "supported_artwork": list(ALLOWED_ARTWORK_EXTENSIONS),
        "supported_rulebook": list(ALLOWED_RULEBOOK_EXTENSIONS)
    })


@app.route("/api/samples", methods=["GET"])
def list_sample_presets():
    """List available sample testing datasets."""
    presets = []
    for pid, pdata in SAMPLE_PRESETS.items():
        presets.append({
            "id": pid,
            "name": pdata["name"],
            "badge": pdata["badge"],
            "description": pdata["description"],
            "artwork_filename": pdata["artwork_filename"],
            "rulebook_filename": pdata["rulebook_filename"],
            "available": os.path.exists(pdata["artwork_path"]) and os.path.exists(pdata["rulebook_path"])
        })
    return jsonify({"success": True, "presets": presets})


@app.route("/api/sample", methods=["GET"])
def get_sample_spec():
    """Return sample rulebook JSON content for pre-viewing."""
    preset_id = request.args.get("preset", "granola").lower()
    preset = SAMPLE_PRESETS.get(preset_id, SAMPLE_PRESETS["granola"])
    rulebook_path = preset["rulebook_path"]

    if os.path.exists(rulebook_path):
        try:
            with open(rulebook_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return jsonify({
                "success": True,
                "preset_id": preset_id,
                "preset_name": preset["name"],
                "sample_rulebook": data
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    return jsonify({"success": False, "error": f"Sample rulebook for '{preset_id}' not found"}), 404


@app.route("/api/analyze", methods=["POST"])
def analyze_artwork_endpoint():
    """
    Handle packaging artwork and rulebook upload or sample preset.
    Runs text extraction, deterministic validation, and Gemini AI analysis.
    """
    preset_id = request.form.get("preset", "").strip().lower()
    use_sample = (request.form.get("use_sample", "").lower() in ("true", "1", "yes")) or bool(preset_id)

    artwork_bytes = None
    artwork_filename = ""
    rulebook_bytes = None
    rulebook_filename = ""

    if use_sample:
        target_preset_id = preset_id if preset_id in SAMPLE_PRESETS else "granola"
        preset = SAMPLE_PRESETS[target_preset_id]

        if not os.path.exists(preset["artwork_path"]):
            return jsonify({
                "success": False,
                "error": f"Sample artwork '{preset['artwork_filename']}' not found on server."
            }), 404
        if not os.path.exists(preset["rulebook_path"]):
            return jsonify({
                "success": False,
                "error": f"Sample rulebook '{preset['rulebook_filename']}' not found on server."
            }), 404

        with open(preset["artwork_path"], "rb") as f:
            artwork_bytes = f.read()
        artwork_filename = preset["artwork_filename"]

        with open(preset["rulebook_path"], "rb") as f:
            rulebook_bytes = f.read()
        rulebook_filename = preset["rulebook_filename"]

    else:
        # File validations
        if "artwork" not in request.files or "rulebook" not in request.files:
            return jsonify({
                "success": False,
                "error": "Both 'artwork' and 'rulebook' files are required."
            }), 400

        art_file = request.files["artwork"]
        rb_file = request.files["rulebook"]

        if not art_file or art_file.filename == "":
            return jsonify({"success": False, "error": "No artwork file provided."}), 400
        if not rb_file or rb_file.filename == "":
            return jsonify({"success": False, "error": "No rulebook file provided."}), 400

        artwork_filename = secure_filename(art_file.filename)
        rulebook_filename = secure_filename(rb_file.filename)

        if not is_allowed_file(artwork_filename, ALLOWED_ARTWORK_EXTENSIONS):
            return jsonify({
                "success": False,
                "error": f"Invalid artwork format '{artwork_filename}'. Allowed: PNG, JPG, PDF."
            }), 400

        if not is_allowed_file(rulebook_filename, ALLOWED_RULEBOOK_EXTENSIONS):
            return jsonify({
                "success": False,
                "error": f"Invalid rulebook format '{rulebook_filename}'. Allowed: TXT, JSON, PDF."
            }), 400

        artwork_bytes = art_file.read()
        rulebook_bytes = rb_file.read()

        if len(artwork_bytes) == 0:
            return jsonify({"success": False, "error": "Uploaded artwork file is empty."}), 400
        if len(rulebook_bytes) == 0:
            return jsonify({"success": False, "error": "Uploaded rulebook file is empty."}), 400

    # Execute analysis pipeline
    try:
        analysis_result = analyzer.analyze_packaging(
            artwork_bytes=artwork_bytes,
            artwork_filename=artwork_filename,
            rulebook_bytes=rulebook_bytes,
            rulebook_filename=rulebook_filename
        )

        return jsonify({
            "success": True,
            "data": analysis_result
        })

    except Exception as e:
        app.logger.error(f"Analysis error: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Analysis encountered an error: {str(e)}"
        }), 500


@app.route("/api/followup", methods=["POST"])
def followup_endpoint():
    """Handle follow-up questions about packaging findings or regulations."""
    data = request.get_json(silent=True)
    if not data or "question" not in data:
        return jsonify({"success": False, "error": "Missing question in request body."}), 400

    question = str(data.get("question", "")).strip()
    if not question:
        return jsonify({"success": False, "error": "Question cannot be empty."}), 400

    context = data.get("context")

    try:
        answer = analyzer.answer_followup(question=question, context=context)
        return jsonify({
            "success": True,
            "answer": answer
        })
    except Exception as e:
        app.logger.error(f"Follow-up error: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Could not answer question: {str(e)}"
        }), 500


@app.errorhandler(413)
def handle_large_file(e):
    """Handle file upload exceeding maximum size."""
    return jsonify({
        "success": False,
        "error": "File size exceeds the 32MB limit. Please upload a smaller packaging artwork or rulebook file."
    }), 413


@app.errorhandler(404)
def handle_not_found(e):
    return jsonify({"success": False, "error": "Endpoint not found"}), 404


@app.errorhandler(500)
def handle_internal_error(e):
    return jsonify({"success": False, "error": "Internal server error. Please check server logs."}), 500


if __name__ == "__main__":
    # Render and cloud platforms supply $PORT; fallback to FLASK_PORT or 5000
    port = int(os.getenv("PORT", os.getenv("FLASK_PORT", 5000)))
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    debug = os.getenv("FLASK_DEBUG", "false").lower() in ("true", "1", "yes")
    print(f"==================================================")
    print(f"  PackGuard AI - Packaging Artwork Checker")
    print(f"  Listening on: http://{host}:{port}")
    print(f"  Gemini Configured: {bool(analyzer.get_gemini_api_key())}")
    print(f"==================================================")
    app.run(host=host, port=port, debug=debug)
