import time
from datetime import datetime
from io import BytesIO

from flask import request, abort
from humanize import naturaltime
from pydub import AudioSegment
from sqlalchemy.exc import IntegrityError, OperationalError

from app import db
from app.ielts_seeds import SECTIONS, SUBSECTIONS, QUESTIONS, TOPICS
from app.models import QuestionSet, Subsection

LOW_PRON_ACCURACY_SCORE = 90


def create_and_fill_out_tables(models):
    # inserting sections
    for section in SECTIONS:
        new_section = models.Section(**section)
        db.session.add(new_section)

    db.session.commit()

    # inserting subsections
    for subsection in SUBSECTIONS:
        section = models.Section.query.filter_by(
            name=subsection["section"]).first()
        subsection["section"] = section
        new_subsection = models.Subsection(**subsection)
        db.session.add(new_subsection)
    db.session.commit()

    # inserting PART 1 topics
    for question_set in QUESTIONS:
        subsection = models.Subsection.query.filter_by(
            name=question_set["subsection"]).first()

        # inserting new subsection_question
        new_question_set = models.QuestionSet(subsection=subsection)
        db.session.add(new_question_set)

        # inserting questions inside topic
        for question in question_set["questions"]:
            new_question = models.Question(text=question,
                                           question_set=new_question_set)
            db.session.add(new_question)

    db.session.commit()

    # inserting PART 2-3 topics
    for topic in TOPICS:
        subsection = models.Subsection.query.filter_by(
            name=topic["subsection"]).first()

        # inserting new topic
        new_topic = models.Topic(name=topic["name"],
                                 description=topic["description"])
        db.session.add(new_topic)

        # inserting topic GENERAL questions
        new_question_set = models.QuestionSet(subsection=subsection,
                                              topic=new_topic)
        db.session.add(new_question_set)

        for question in topic["general_questions"]:
            new_question = models.Question(text=question,
                                           question_set=new_question_set)
            db.session.add(new_question)

        # inserting topic DISCUSSION questions
        subsection = models.Subsection.query.filter_by(
            name="Two-way Discussion").first()
        new_question_set = models.QuestionSet(subsection=subsection,
                                              topic=new_topic)

        for question in topic["discussion_questions"]:
            new_question = models.Question(text=question,
                                           question_set=new_question_set)
            db.session.add(new_question)

    db.session.commit()


def measure_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"🕐 Function {func.__name__} executed in {int(execution_time)} seconds.")
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

def get_audio_files(questions_set) -> tuple:
    audio_files = tuple(request.files[key] for key in request.files.keys() if key.startswith('audio_'))
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
        score = word.get("AccuracyScore")
        if score:
            score = int(score)

        if word["ErrorType"] == "Mispronunciation":
            word = f"""<span data-toggle="tooltip" title="Accuracy: {score}%" class="word_mispronunciation">{word_text}</span>"""
        elif word["ErrorType"] == "Omission":
            word = f"""<span data-toggle="tooltip" title="This word was omitted" class="word_omitted">{word_text}</span>"""
        elif word["ErrorType"] == "Insertion":
            word = f"""<span data-toggle="tooltip" title="This word is probably redundant" class="word_insertion">{word_text}</span>"""
        elif score < LOW_PRON_ACCURACY_SCORE:
            word = f"""<span data-toggle="tooltip" title="Accuracy: {score}%" class="score-low">{word_text}</span>"""
        else:
            word = f"""<span data-toggle="tooltip" title="Accuracy: {score}%">{word_text}</span>"""

        word_list.append(word)

    return " ".join(word_list)


def convert_dialogue_to_string(questions_and_answers: list) -> str:
    res = [f"Examiner: {qa['question']}\nStudent: {qa['answer']}" for qa in questions_and_answers]
    return "\n\n".join(res)


def get_misspelled_words(transcriptions_and_pron_assessments: list):
    misspelled_words = set()
    for item in transcriptions_and_pron_assessments:
        try:
            words = item["pronunciation"]['NBest'][0]['Words']
        except (KeyError, IndexError, TypeError):
            continue
        else:
            for word in words:
                if word.get('ErrorType') == 'Mispronunciation':
                    misspelled_words.add(word.get('Word'))
    return list(misspelled_words)


def get_words_low_pron_accuracy(answers: list) -> tuple:
    mispronounced_words, low_accuracy_words = set(), set()

    for answer in answers:
        pron_json = answer.pronunciation_assessment_json
        if pron_json and pron_json['RecognitionStatus'] == 'Success':
            try:
                words = pron_json['NBest'][0]['Words']
            except (KeyError, IndexError, TypeError):
                continue

            for word in words:
                word_text = word.get('Word')
                if word_text and word.get('AccuracyScore'):
                    if word.get('ErrorType') == 'Mispronunciation':
                        mispronounced_words.add(word_text)
                    elif word.get('AccuracyScore') < LOW_PRON_ACCURACY_SCORE:
                        if word_text not in mispronounced_words:
                            low_accuracy_words.add(word_text)

    return mispronounced_words, low_accuracy_words


def get_pron_errors_and_recommendations(answers: list) -> dict:
    mispronounced_words, low_accuracy_words = get_words_low_pron_accuracy(answers)

    if mispronounced_words:
        mispronounced_words = f'Mispronounced words: {", ".join(mispronounced_words)}'
    else:
        mispronounced_words = "Wow, you don't have any errors!"

    if low_accuracy_words:
        low_accuracy_words = f'Words with low pronunciation accuracy: {", ".join(low_accuracy_words)}'
    else:
        low_accuracy_words = "Sorry, no recommendations in this case..."

    return {'errors': mispronounced_words, 'recommendations': low_accuracy_words}


def time_ago_in_words(dtime: datetime) -> str:
    past_time = datetime.utcnow() - dtime
    return naturaltime(past_time)