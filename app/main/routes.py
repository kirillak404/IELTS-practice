from flask import render_template, request, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func

from app.main import bp
from app import models, db


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
@bp.route('/section/speaking/practice', methods=["GET", "POST"])
def speaking_practice():
    if request.method == "GET":
        section = models.Section.query.filter_by(name="Speaking").first()
        subsection = models.Subsection.query.filter_by(section=section,
                                                       part=1).first()

        question_set = models.QuestionSet.query.filter_by(
            subsection=subsection).order_by(func.random()).first()

        return render_template("speaking.html",
                               subsections=section.subsections,
                               current_subsection=subsection,
                               question_set=question_set)

    # handling POST request
    answer_text = request.form.get('answers')
    question_set_id = int(request.form.get('question_set_id'))  # TODO TRY

    # if not user_progress
    section = models.Section.query.filter_by(name="Speaking").first()
    subsection = models.Subsection.query.filter_by(section=section,
                                                   part=1).first()

    # inserting user_progress
    user_progress = models.UserProgress(user=current_user,
                                        section_id=section.id,
                                        current_subsection_id=subsection.id)
    db.session.add(user_progress)

    # inserting user_answer
    user_answer = models.UserAnswer(user_progress=user_progress,
                                    question_set_id=question_set_id,
                                    answer_text=answer_text)
    db.session.add(user_answer)
    db.session.commit()

    return redirect(url_for('main.speaking_practice'))

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
