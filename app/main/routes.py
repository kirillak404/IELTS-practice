import os
import time

from flask import render_template, request, jsonify
from flask_login import login_required, current_user

from app.utils import transcript_file
from app.main import bp


@bp.route('/')
def index():
    # user = session.get('user')
    if current_user.is_authenticated:
        return render_template("dashboard.html")
    return render_template("index.html")


@login_required
@bp.route("/upload_audio", methods=["POST"])
def upload_audio():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file found in request"}), 400

    audio_file = request.files["audio"]

    if audio_file.filename == "":
        return jsonify({"error": "No audio file selected"}), 400

    file_name = f"recording_{int(time.time())}.webm"
    audio_path = os.path.join(bp.config["UPLOAD_FOLDER"], file_name)
    audio_file.save(audio_path)

    # transcription audio
    transcript = transcript_file(audio_path)

    return render_template("result.html", transcript=transcript)


@bp.route('/practice/speaking/', methods=["GET", "POST"])
@login_required
def practice_speaking():
    if request.method == "GET":
        return render_template("speaking.html")