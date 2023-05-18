from flask import render_template
from flask_login import login_required, current_user
from sqlalchemy import func

from app.main import bp
from app import models


@bp.route('/')
def index():
    if current_user.is_authenticated:
        return render_template("dashboard.html")
    return render_template("index.html")


@login_required
@bp.route('/section/<name>')
def render_section(name):
    section = models.Section.query.filter(func.lower(models.Section.name) ==
                                          func.lower(name)).first_or_404()
    subsections = models.Subsection.query.filter_by(section=section).all()

    return render_template("section.html",
                           section=section,
                           subsections=subsections)


@login_required
@bp.route('/section/speaking/practice')
def speaking_practice():
    section = models.Section.query.filter(func.lower(models.Section.name) ==
                                          func.lower("Speaking")).first()

    subsections = models.Subsection.query.filter_by(section=section).all()

    return render_template("speaking.html", subsections=subsections, stage=1)












# @login_required
# @bp.route("/upload_audio", methods=["POST"])
# def upload_audio():
#     if "audio" not in request.files:
#         return jsonify({"error": "No audio file found in request"}), 400
#
#     audio_file = request.files["audio"]
#
#     if audio_file.filename == "":
#         return jsonify({"error": "No audio file selected"}), 400
#
#     file_name = f"recording_{int(time.time())}.webm"
#     audio_path = os.path.join(bp.config["UPLOAD_FOLDER"], file_name)
#     audio_file.save(audio_path)
#
#     # transcription audio
#     transcript = transcript_file(audio_path)
#
#     return render_template("result.html", transcript=transcript)