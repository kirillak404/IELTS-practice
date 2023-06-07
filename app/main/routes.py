from flask import render_template, request, redirect, url_for
from flask_login import login_required, current_user

from app.api_utils import batch_transcribe_and_assess_pronunciation, \
    gpt_evaluate_speaking, transcribe_audio_file, assess_pronunciation
from app.main import bp
from app.models import *
from app.utils import get_current_subsection_and_last_topic, get_practice_data, \
    get_audio_files, commit_changes


@bp.route('/')
def index():
    if current_user.is_authenticated:
        return render_template("dashboard.html")
    return render_template("index.html")


@login_required
@bp.route('/section/<name>')
def render_section(name):
    section = Section.get_by_name(name)
    subsections = Subsection.query.filter_by(section=section).all()

    return render_template("section.html",
                           section=section,
                           subsections=subsections)


@login_required
@bp.route('/section/speaking/practice', methods=["GET"])
def speaking_practice_get():
    # Retrieve the 'speaking' section
    section = Section.get_by_name("speaking")
    # Get the current user's progress in this section
    user_progress = current_user.get_section_progress(section.id)
    # Determine the current subsection and last topic based on user's progress
    subsection, last_topic = get_current_subsection_and_last_topic(
        user_progress, section)
    # Get data required for the practice page
    practice = get_practice_data(subsection, last_topic)
    # Render the practice page with obtained data
    return render_template("speaking.html",
                           subsections=section.subsections,
                           current_subsection=subsection,
                           practice=practice)


@login_required
@bp.route('/section/speaking/practice', methods=["POST"])
def speaking_practice_post():
    # Validate the question set ID from the request
    question_set_id = request.form.get('question_set_id')
    questions_set = QuestionSet.validate_question_set(question_set_id)

    # Process audio files from the request
    audio_files = get_audio_files(questions_set)
    # audio_files = [audio_files[0]]  # TODO delete

    # Transcribe audio files and access pronunciation
    transcriptions_and_pron_assessments = batch_transcribe_and_assess_pronunciation(audio_files)

    # return render_template(url_for('main.speaking_practice_get'))

    # Get the 'speaking' section
    section = Section.get_by_name("speaking")
    # Get the current user's progress in this section
    user_progress = current_user.get_section_progress(section.id)

    # Update or create user's progress based on previous section progress
    subsection_id, user_progress = UserProgress.create_or_update_user_progress(
        current_user, user_progress, section, question_set_id)

    # Create a new record for the user's attempt at this subsection
    subsection_attempt = UserSubsectionAttempt(
        user_progress=user_progress,
        subsection_id=subsection_id,
        question_set_id=question_set_id)
    db.session.add(subsection_attempt)

    # Insert user's answers for this attempt
    questions_and_answers = UserSubsectionAnswer.insert_user_answers(
        subsection_attempt,
        questions_set,
        transcriptions_and_pron_assessments)

    # Evaluate user's speaking ability and insert the result
    gpt_speaking_result = gpt_evaluate_speaking(questions_and_answers)
    UserSpeakingAttemptResult.insert_speaking_result(subsection_attempt, gpt_speaking_result)

    # Commit changes to the database
    commit_changes()
    # Redirect to the page displaying the results of the speaking attempt
    return redirect(url_for('main.get_speaking_attempt',
                            user_subsection_attempt_id=subsection_attempt.id))



@login_required
@bp.route('/section/speaking/attempt/<int:user_subsection_attempt_id>/')
def get_speaking_attempt(user_subsection_attempt_id):
    return render_template("results_new.html")


    user_subsection_attempt = UserSubsectionAttempt.query.get(
        user_subsection_attempt_id)
    if not user_subsection_attempt:
        abort(404)

    # check that the user requests his answer
    user_progress = user_subsection_attempt.user_progress
    if current_user != user_progress.user:
        abort(403)

    speaking_result = user_subsection_attempt.speaking_result
    questions_and_answers = user_subsection_attempt.get_questions_answer()
    return render_template('section_results.html',
                           result=speaking_result,
                           questions_and_answers=questions_and_answers)


@login_required
@bp.route('/section/speaking/result/<int:id>/')
def get_speaking_result():
    pass


@bp.route('/upload', methods=["POST"])
def upload():
    audio_file = request.files['file']
    transcript = transcribe_audio_file(audio_file)
    pron = assess_pronunciation(audio_file, transcript)
    return redirect(url_for('main.index'))
