import time

from flask import request, abort
from sqlalchemy.exc import IntegrityError, OperationalError

from app import db
from app.models import QuestionSet, Subsection


def validation_class(field):
    if field.errors:
        return "is-invalid"
    elif field.data or field.raw_data:
        return "is-valid"
    return ""


def highlight_errors(content, mistakes):
    for error in mistakes:
        content = content.replace(error['IncorrectText'], f'<span class="highlight" data-bs-toggle="tooltip" title="{error["Explanation"]}">{error["IncorrectText"]}</span>')
    return content


def measure_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Function {func.__name__} executed in {int(execution_time)} seconds.")
        return result
    return wrapper


# speaking_practice_get helpers

def get_current_subsection_and_last_topic(user_progress, section):
    if user_progress:
        subsection = Subsection.query.get(user_progress.next_subsection_id)
        last_topic = user_progress.get_last_topic()
    else:
        subsection = Subsection.get_by_section_and_part(section, 1)
        last_topic = None
    return subsection, last_topic


def get_practice_data(subsection, last_topic):
    question_set = QuestionSet.get_random_for_subsection(subsection, last_topic)
    topic_name = question_set.topic.name if question_set.topic else None
    topic_desc = question_set.topic.description if question_set.topic else None
    practice = {"part": subsection.part_number,
                "topic_name": topic_name,
                "topic_desc": topic_desc,
                "answer_time_limit": subsection.time_limit_minutes,
                "question_id": question_set.id,
                "questions": [q.text for q in question_set.questions]}
    return practice


# speaking_practice_post helpers

def get_audio_files(questions_set):
    audio_files = [request.files[key] for key in request.files.keys() if key.startswith('audio_')]
    if len(audio_files) != len(questions_set.questions):
        abort(400, "Audio recordings do not match question count.")
    return audio_files


def commit_changes():
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        abort(400, "Database integrity error")
    except OperationalError:
        db.session.rollback()
        abort(500, "Database operational error")