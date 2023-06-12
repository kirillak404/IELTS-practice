import time
from io import BytesIO

from flask import request, abort
from pydub import AudioSegment
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


# for azure assess_pronunciation func
def get_chunk(audio_source, chunk_size=1024):
    while True:
        chunk = audio_source.read(chunk_size)
        if not chunk:
            break
        yield chunk


def convert_audio(file_storage):
    # Конвертировать FileStorage в Bytes
    blob = BytesIO(file_storage.read())

    # Загрузить файл в формате webm
    audio = AudioSegment.from_file(blob, format="webm")

    # Установить параметры аудио
    audio = audio.set_frame_rate(16000)
    audio = audio.set_channels(1)

    # Конвертировать обратно в BytesIO
    output_blob = BytesIO()
    audio.export(output_blob, format="opus")

    # Переустановить указатель в начало BytesIO, чтобы считывать с начала
    output_blob.seek(0)

    return output_blob


def convert_answer_object_to_html(answer):
    pronunciation_assessment_json = answer.pronunciation_assessment_json
    if not pronunciation_assessment_json:
        return "You didn't give an answer ❌"

    words = pronunciation_assessment_json["NBest"][0]["Words"]

    word_list = []
    for word in words:
        word_text = word["Word"]
        error_type = word["ErrorType"]

        if word["ErrorType"] == "Mispronunciation":
            word = f"""<span class="error red-background" data-error-type="{error_type}" data-accuracy-score="{int(word["AccuracyScore"])}" data-error-long-description="The word was mispronounced">{word_text}</span>"""
        elif word["ErrorType"] == "Omission":
            word = f"""<span class="error gray-background" data-error-type="{error_type}" data-error-long-description="This word was omitted">{word_text}</span>"""
        elif word["ErrorType"] == "Insertion":
            word = f"""<span class="error yellow-background" data-error-type="{error_type}" data-error-long-description="This word is probably redundant">{word_text}</span>"""
        else:
            word = word_text

        word_list.append(word)

    return " ".join(word_list)