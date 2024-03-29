import os
import time
import uuid
from collections import namedtuple
from io import BytesIO

from amplitude import Amplitude, BaseEvent
from flask import request, session, flash, abort
from pydub import AudioSegment
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import IntegrityError, OperationalError
from werkzeug.datastructures import FileStorage

from app.content.ielts_seeds import SECTIONS, SUBSECTIONS, QUESTIONS, TOPICS
from app.models import (Section, Subsection, QuestionSet, UserProgress,
                        UserSubsectionAttempt, UserSubsectionAnswer,
                        UserSpeakingAttemptResult)
from config.database import db

amplitude = Amplitude(os.environ.get('AMPLITUDE_API_KEY'))


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
        print(
            f"🕐 Function {func.__name__} executed in {int(execution_time)} seconds.")
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
    question_set = QuestionSet.get_random_for_subsection(subsection,
                                                         last_topic)
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
    """Retrieve audio files from POST request, validate and name them"""

    audio_files = []
    for name, file in request.files.items():
        if name.startswith('audio_') and file.content_type == 'audio/webm':
            file.name = f'{name}.webm'
            audio_files.append(file)
    audio_files = tuple(audio_files)

    # if Speaking part 2 (cue card)
    if questions_set.topic and len(audio_files) == 1:
        return audio_files

    # if Speaking part 1 or part 3
    if len(audio_files) == len(questions_set.questions):
        return audio_files

    flash("An error has occurred, please try again")
    abort(400, "Audio recordings do not match question count.")


def commit_changes():
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("An error has occurred, please try again")
        print('Database integrity error')
        abort(400, "Database integrity error")
    except OperationalError:
        db.session.rollback()
        flash("An error has occurred, please try again")
        print('Database operational error')
        abort(500, "Database operational error")


# for azure assess_pronunciation func
def get_chunk(audio_source, chunk_size=1024):
    while True:
        chunk = audio_source.read(chunk_size)
        if not chunk:
            break
        yield chunk


def convert_audio_to_opus_bytesio(file_storage: FileStorage) -> BytesIO:
    """
    Convert an audio file from FileStorage to BytesIO, change its parameters,
    and export it in opus format.

    Parameters:
    file_storage (FileStorage): The original audio file in FileStorage format.

    Returns:
    BytesIO: The converted audio file in opus format, stored in a BytesIO object.
    """
    # Convert FileStorage to Bytes
    blob = BytesIO(file_storage.read())

    # Load the file in webm format
    audio = AudioSegment.from_file(blob, format="webm")

    # Set audio parameters
    audio = audio.set_frame_rate(16000)
    audio = audio.set_channels(1)

    # Convert back to BytesIO
    output_blob = BytesIO()
    audio.export(output_blob, format="opus")

    # Reset the pointer to the start of BytesIO to read from the beginning
    output_blob.seek(0)

    return output_blob


def get_dialog_text(answers_data: tuple, attempt: namedtuple) -> str:
    question_set = attempt.question_set
    speaking_part_number = attempt.subsection.part_number

    # create cue card and answer for IELTS Speaking part 2
    if speaking_part_number == 2:
        topic = attempt.topic
        questions = "\n- ".join(q.text for q in question_set.questions)
        dialog = f'''\
Cue card:
###
Topic: {topic.name}
Task: {topic.description}
You should say:

{questions}
###

Student Answer:
###
{answers_data[0]['answer_transcription']}
###'''
        return dialog

    # create dialog for IELTS Speaking part 1 & 3
    res = (f"Q: {item['question'].text}\nA: {item['answer_transcription']}"
           for item in answers_data)
    return "\n\n".join(res)


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
                    elif word.get('AccuracyScore') < 90:
                        if word_text not in mispronounced_words:
                            low_accuracy_words.add(word_text)

    return mispronounced_words, low_accuracy_words


def add_pronunciation_score(gpt_speech_evaluation: dict,
                            qa_data: tuple) -> None:
    """
    Add pronunciation score to a speech evaluation dictionary.

    Args:
        gpt_speech_evaluation (dict): The dictionary to add pronunciation score to.
        qa_data (tuple): Tuple containing QA data used to compute the score.
    """
    # Compute average pronunciation score from QA data
    pron_score = get_avg_score_from_answers_speech_eval(qa_data, 'PronScore')

    # Add the pronunciation score to the evaluation dictionary
    gpt_speech_evaluation['pronunciation'] = {'score': pron_score}


def add_fluency_and_coherence_score(gpt_speech_evaluation: dict,
                                    qa_data: tuple) -> None:
    """
    Add fluency and coherence score to a speech evaluation dictionary.

    Args:
        gpt_speech_evaluation (dict): The dictionary to add fluency and coherence score to.
        qa_data (tuple): Tuple containing QA data used to compute the score.
    """
    # Compute average fluency score from QA data
    fluency_score = get_avg_score_from_answers_speech_eval(qa_data,
                                                           'FluencyScore')

    # Get the coherence score from the evaluation dictionary and remove it
    coherence_score = gpt_speech_evaluation.pop('coherence')['score']

    # Compute the average of fluency and coherence scores
    fluency_and_coherence_score = round((fluency_score + coherence_score) / 2)

    # Add the fluency and coherence score to the evaluation dictionary
    gpt_speech_evaluation['fluencyAndCoherence'] = {
        'score': fluency_and_coherence_score}


def get_avg_score_from_answers_speech_eval(qa_data: tuple, score_name: str) -> object:
    """
    Compute the average score of a particular criterion from QA data.

    Args:
        qa_data (tuple): Tuple containing QA data used to compute the score.
        score_name (str): Name of the score to compute.

    Returns:
        int: The computed average score, rounded and converted to a 9-point scale.
    """
    # Extract the specified scores from the QA data
    pron_scores = tuple(
        score['pronunciation_assessment']['NBest'][0][score_name]
        for score in qa_data)

    # Compute the average score on a 100-point scale
    pron_score = sum(pron_scores) / len(pron_scores)

    # Convert the score to a 9-point scale and round it
    return round(pron_score / 100 * 9)


def save_speaking_results_to_database(user, question_set, speaking_result,
                                      answers_evaluation):
    # Get the 'speaking' section
    section = Section.get_by_name("speaking")
    # Get the current user's progress in this section
    user_progress = user.get_section_progress(section.id)

    # Update or create user's progress based on previous section progress
    subsection_id, user_progress = UserProgress.create_or_update_user_progress(
        user, user_progress, section, question_set.id)

    # Create a new record for the user's attempt at this subsection
    subsection_attempt = UserSubsectionAttempt(
        user_progress=user_progress,
        subsection_id=subsection_id,
        question_set_id=question_set.id)
    db.session.add(subsection_attempt)

    # Insert user's answers for this attempt
    UserSubsectionAnswer.insert_user_answers(subsection_attempt,
                                             answers_evaluation)

    # Insert speaking attempt result
    UserSpeakingAttemptResult.insert_speaking_result(subsection_attempt,
                                                     speaking_result)

    # Commit changes to the database
    commit_changes()

    return subsection_attempt


def send_amplitude_event(user_id: UUID, event_name: str,
                         event_properties: dict[str, str] = None) -> None:
    """
    Sends an event to Amplitude with the specified properties if amplitude_device_id is available.

    Args:
        user_id: UUID of the user for whom the event is being sent.
        event_name: Name of the event being sent.
        event_properties: Additional properties associated with the event. Defaults to None.

    Raises:
        TypeError: If the user_id is not of UUID type.
    """

    # Check if the user_id is of UUID type
    if not isinstance(user_id, uuid.UUID):
        raise TypeError(
            f'user_id should be of type UUID, but got {type(user_id).__name__}')

    # Retrieve the amplitude device ID from the session
    amplitude_device_id = session.get('amplitude_device_id')

    if amplitude_device_id:
        # If the amplitude device ID exists, track the event with amplitude
        amplitude.track(
            BaseEvent(
                event_type=event_name.lower(),
                user_id=str(user_id),
                device_id=amplitude_device_id,
                event_properties=event_properties
            ))

        # Flush the tracked events to Amplitude
        amplitude.flush()
    else:
        print(f'amplitude_device_id not found, user: {user_id}')
