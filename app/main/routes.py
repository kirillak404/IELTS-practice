from flask import render_template, request, redirect, url_for, abort
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError, OperationalError

from app import models, db
from app.main import bp


@bp.route('/')
def index():
    if current_user.is_authenticated:
        return render_template("dashboard.html")
    return render_template("index.html")


@login_required
@bp.route('/section/<name>')
def render_section(name):
    section = models.Section.get_by_name(name)
    subsections = models.Subsection.query.filter_by(section=section).all()

    return render_template("section.html",
                           section=section,
                           subsections=subsections)


@login_required
@bp.route('/section/speaking/practice', methods=["GET", "POST"])
def speaking_practice():
    if request.method == "GET":
        section = models.Section.get_by_name("speaking")
        user_progress = current_user.get_section_progress(section.id)

        if user_progress:
            subsection = models.Subsection.query.get(
                user_progress.next_subsection_id)
            last_topic_id = user_progress.get_last_topic()
        else:
            subsection = models.Subsection.get_by_section_and_part(section, 1)
            last_topic_id = None

        question_set = models.QuestionSet.get_random_for_subsection(
            subsection, last_topic_id)

        return render_template("speaking.html",
                               subsections=section.subsections,
                               current_subsection=subsection,
                               question_set=question_set)

    # handling POST request
    answer_text = request.form.get('answers')
    if not answer_text:
        abort(400, "Answer text is missing")

    question_set_id = request.form.get('question_set_id')
    try:
        question_set_id = int(question_set_id)
    except ValueError:
        return abort(400, "Question set must be an integer")

    section = models.Section.get_by_name("speaking")
    user_progress = current_user.get_section_progress(section.id)

    # creating new user_progress record
    if not user_progress:

        # checking that question_set_id from POST request is valid
        subsection = models.Subsection.get_by_section_and_part(section, 1)
        question_set_is_valid = models.QuestionSet.valid_for_subsection(
                question_set_id, subsection.id)
        if not question_set_is_valid:
            abort(400, "Invalid question_set_id")

        user_progress = models.UserProgress(user=current_user,
                                            section_id=section.id)
        db.session.add(user_progress)

    # updating user_progress record
    else:
        # checking that question_set_id from POST request is valid
        question_set_is_valid = models.QuestionSet.valid_for_subsection(
                question_set_id, user_progress.next_subsection_id)
        if not question_set_is_valid:
            abort(400, "Invalid question_set_id")

        user_progress.update_next_subsection(section)

    # inserting new user_answer
    user_answer = models.UserAnswer(user_progress=user_progress,
                                    question_set_id=question_set_id,
                                    answer_text=answer_text)
    db.session.add(user_answer)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        abort(400, "Database integrity error")
    except OperationalError:
        db.session.rollback()
        abort(500, "Database operational error")

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
