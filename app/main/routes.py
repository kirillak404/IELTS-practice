from flask import render_template, request, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func, desc

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

        # set subsection from user_progress
        if user_progress:
            subsection = models.Subsection.query.get(
                user_progress.next_subsection_id)

            # getting last topic id
            last_user_answer = db.session.query(models.UserAnswer).filter(
                models.UserAnswer.user_progress_id == user_progress.id
            ).order_by(desc(models.UserAnswer.id)).first()

            last_topic_id = models.QuestionSet.query.get(
                last_user_answer.question_set_id).topic_id

        # set subsection part 1 if progress not found
        else:
            subsection = models.Subsection().query.filter_by(
                section=section, part=1).first()
            last_topic_id = None

        if last_topic_id:
            # getting question_set with particular topic_id
            question_set = models.QuestionSet.query.filter_by(
                subsection=subsection, topic_id=last_topic_id).order_by(
                func.random()).first()
        else:
            # getting any question_set
            question_set = models.QuestionSet.query.filter_by(
                subsection=subsection).order_by(func.random()).first()

        return render_template("speaking.html",
                               subsections=section.subsections,
                               current_subsection=subsection,
                               question_set=question_set)

    # handling POST request

    # TODO
    '''
    1. Check that question_set_id is in NEXT subsection (or section)
    2. int -> add TRY EXCEPT
    '''

    # getting POST request args
    answer_text = request.form.get('answers')
    question_set_id = int(request.form.get('question_set_id'))

    section = models.Section.get_by_name("speaking")
    user_progress = current_user.get_section_progress(section.id)

    # creating new user_progress record
    if not user_progress:
        user_progress = models.UserProgress(user=current_user,
                                            section_id=section.id)
        db.session.add(user_progress)

    else:
        user_progress.update_next_subsection(section)

    # inserting new user_answer
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
