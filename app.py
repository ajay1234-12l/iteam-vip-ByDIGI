# app.py
import os
import re
import mimetypes
from flask import Flask, request, send_file, jsonify, abort, make_response

app = Flask(__name__)

# Config
IMAGE_FOLDER = "images"
EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp", ".gif"]
CACHE_MAX_AGE = 86400  # seconds

# Allowed id pattern: digits, letters, underscore, dash
ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def safe_path(base, *paths):
    """Return absolute path if inside base, otherwise None."""
    final = os.path.abspath(os.path.join(base, *paths))
    base_abs = os.path.abspath(base)
    if not final.startswith(base_abs + os.sep) and final != base_abs:
        return None
    return final


def find_image(itemid):
    """Return (full_path, ext) or (None, None)."""
    for ext in EXTENSIONS:
        filename = f"{itemid}{ext}"
        candidate = safe_path(IMAGE_FOLDER, filename)
        if candidate and os.path.isfile(candidate):
            return candidate, ext
    return None, None


@app.route("/image", methods=["GET"])
def image_by_itemid():
    itemid = (request.args.get("itemid") or "").strip()

    # provide helpful error if missing
    if not itemid:
        return jsonify({"error": "missing itemid query parameter. e.g. /image?itemid=909050019"}), 400

    # validate pattern
    if not ID_PATTERN.match(itemid):
        return jsonify({
            "error": "invalid itemid format",
            "itemid": itemid,
            "allowed_pattern": r"^[A-Za-z0-9_-]+$",
            "note": "Only letters, digits, underscore and dash allowed. No spaces or slashes."
        }), 400

    # find file
    path, ext = find_image(itemid)
    if not path:
        return jsonify({
            "error": "image not found",
            "itemid": itemid,
            "checked_extensions": EXTENSIONS,
            "hint": "Use /debug?itemid=... to see exact paths checked or /list to list available files."
        }), 404

    # send file
    mime, _ = mimetypes.guess_type(path)
    if not mime:
        mime = "application/octet-stream"
    resp = make_response(send_file(path, mimetype=mime))
    resp.headers["Cache-Control"] = f"public, max-age={CACHE_MAX_AGE}, immutable"
    return resp


@app.route("/debug", methods=["GET"])
def debug_item():
    """Return candidate file paths checked for the itemid and existence boolean."""
    itemid = (request.args.get("itemid") or "").strip()
    if not itemid:
        return jsonify({"error": "missing itemid query parameter"}), 400

    candidates = []
    for ext in EXTENSIONS:
        filename = f"{itemid}{ext}"
        candidate = safe_path(IMAGE_FOLDER, filename)
        exists = bool(candidate and os.path.isfile(candidate))
        candidates.append({
            "filename": filename,
            "path": candidate,
            "exists": exists
        })
    return jsonify({"itemid": itemid, "candidates": candidates})


@app.route("/list", methods=["GET"])
def list_images():
    """List files in image folder (filenames only)."""
    try:
        files = []
        if os.path.isdir(IMAGE_FOLDER):
            for fname in os.listdir(IMAGE_FOLDER):
                # optionally filter by our extensions
                if any(fname.lower().endswith(ext) for ext in EXTENSIONS):
                    files.append(fname)
        files.sort()
        return jsonify({"image_folder": IMAGE_FOLDER, "count": len(files), "files": files})
    except Exception as e:
        return jsonify({"error": "failed to list images", "detail": str(e)}), 500


@app.route("/", methods=["GET"])
def index():
    return (
        "Image API running. Use /image?itemid=909050019\n"
        + f"Images folder: {IMAGE_FOLDER}"
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # debug True for local troubleshooting; set False in production
    app.run(host="0.0.0.0", port=port, debug=True)