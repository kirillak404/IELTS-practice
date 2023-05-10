import os
import time

from flask import render_template, request, jsonify, redirect

from app import app
from app.utils import transcript_file
from app.forms import LoginForm


@app.route('/')
def hello_world():
    return render_template("practice.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        print("valid")
        return redirect('/')
    print("invalid")
    return render_template('login.html', form=form)


@app.route("/upload_audio", methods=["POST"])
def upload_audio():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file found in request"}), 400

    audio_file = request.files["audio"]

    if audio_file.filename == "":
        return jsonify({"error": "No audio file selected"}), 400

    file_name = f"recording_{int(time.time())}.webm"
    audio_path = os.path.join(app.config["UPLOAD_FOLDER"], file_name)
    audio_file.save(audio_path)

    # transcription audio
    transcript = transcript_file(audio_path)

    return render_template("result.html", transcript=transcript)