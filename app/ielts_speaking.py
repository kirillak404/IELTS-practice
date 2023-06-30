import base64
import json
import os
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from typing import Optional

import openai
import requests
from flask import abort, flash
from tenacity import retry, stop_after_attempt, wait_fixed, RetryError
from werkzeug.datastructures import FileStorage

from app.models import QuestionSet
from app.utils import get_chunk, convert_audio_to_opus_bytesio, \
    get_dialog_text, add_pronunciation_score, add_fluency_and_coherence_score, measure_time


@measure_time
def evaluate_ielts_speaking(question_set: QuestionSet, audio_files_list: list) -> tuple:
    """Evaluate IELTS speaking responses with transcript generation and pronunciation assessment.

    This function transcribes audio responses to IELTS speaking questions,
    validates that all questions have been answered, and then evaluates the
    responses using ChatGPT and Azure's pronunciation API.

    Args:
        question_set (object): The set of IELTS speaking questions.
        audio_files_list (list): A list of audio files containing spoken responses.

    Returns:
        tuple: A tuple containing two elements - the first is the speech evaluation results,
               the second is the question-answer data with pronunciation assessments.

    Raises:
        RetryError: If all attempts to transcribe the audio files fail.
        HTTPException: If a user doesn't answer all questions (HTTP 400) or
                       if an error occurs during the transcription process (HTTP 500).
    """
    # Transcribe all audio files, retrying as necessary
    try:
        transcriptions_list = transcribe_audio_files_in_bulk(audio_files_list)
    except RetryError as e:
        print("Failed to transcribe all audio files after multiple attempts. Last attempt:", e.last_attempt)
        flash("An error occurred while transcribing the audio files. Please try again.")
        abort(500)

    # Validate that all questions have received an answer
    if not all(transcriptions_list):
        flash("It seems you did not answer all the questions, please try again")
        abort(400)

    # Combine audio files, transcriptions, and questions into a list of dictionaries
    zipped = zip(audio_files_list, transcriptions_list, question_set.questions)
    qa_data = tuple({'answer_audio': file,
                     'answer_transcription': transcript,
                     'question': question}
                    for file, transcript, question in zipped)

    # Collect attempt info for future needs
    attempt_info = {'subsection': question_set.subsection,
                    'question_set': question_set,
                    'topic': question_set.topic}

    # Evaluate the spoken responses using ChatGPT and Azure's pronunciation API
    gpt_speech_evaluation, qa_data = get_chatgpt_and_azure_speech_assessment(qa_data, attempt_info)
    add_pronunciation_score(gpt_speech_evaluation, qa_data)
    add_fluency_and_coherence_score(gpt_speech_evaluation, qa_data)

    return gpt_speech_evaluation, qa_data


@measure_time
def transcribe_audio_files_in_bulk(audio_files: list) -> tuple:
    """Transcribe multiple audio files in parallel.

    Args:
        audio_files (list): A list of audio files to transcribe.

    Returns:
        tuple: A tuple containing transcriptions of all the audio files.
    """
    with ThreadPoolExecutor() as executor:
        return tuple(executor.map(transcribe_single_audio_file, audio_files))


@retry(stop=stop_after_attempt(5), wait=wait_fixed(1))
def transcribe_single_audio_file(audio_file: FileStorage) -> Optional[str]:
    """Transcribe a single audio file using the OpenAI Whisper API.

    Args:
        audio_file (FileStorage): The audio file to be transcribed.

    Returns:
        str: The transcribed text if successful, 'None' if not.

    Raises:
        RetryError: If all attempts to transcribe the audio file fail.
    """
    audio_file.name = "audio.webm"
    audio_transcript = openai.Audio.transcribe(model="whisper-1",
                                               file=audio_file,
                                               language="en")
    audio_file.seek(0)
    audio_transcript = audio_transcript.get("text")
    if not audio_transcript or audio_transcript in ('you', 'Thank you.'):
        return None
    return audio_transcript


def get_chatgpt_and_azure_speech_assessment(qa_data: tuple, attempt_info: dict) -> tuple:
    """Perform parallel assessment of user answers using ChatGPT and Azure's pronunciation assessment.

    Args:
        qa_data (tuple): A tuple containing data for each question-answer pair.
        attempt_info (dict): A dict with subsection, question_set and topic

    Returns:
        tuple: A tuple containing the updated question-answer data and the ChatGPT speech evaluation.
    """
    with ThreadPoolExecutor() as executor:
        chatgpt_assessment_future = executor.submit(
            evaluate_speech_with_chatgpt, qa_data, attempt_info)
        azure_pronunciation_assessment_future = executor.submit(
            assess_pronunciation_in_bulk, qa_data)

        gpt_speaking_eval = chatgpt_assessment_future.result()
        qa_data = azure_pronunciation_assessment_future.result()

    return gpt_speaking_eval, qa_data


@measure_time
def evaluate_speech_with_chatgpt(qa_data: tuple, attempt_info: dict) -> dict:
    """Evaluate a user's speech using ChatGPT.

    Args:
        qa_data (tuple): A tuple containing data for each question-answer pair.
        attempt_info (dict): A dict with subsection, question_set and topic

    Returns:
        dict: A dictionary containing the ChatGPT evaluation.

    Raises:
        RetryError: If all attempts to get a response from ChatGPT fail.
        JSONDecodeError: If there is an error deserializing the JSON response from ChatGPT.
    """
    system_message = "You act as a professional IELTS examiner."
    response_json_schema = """{"type":"object","properties":{"coherence":{"type":"object","properties":{"score":{"type":"integer","minimum":0,"maximum":9}}},"lexicalResource":{"type":"object","properties":{"score":{"type":"integer","minimum":0,"maximum":9}}},"grammaticalRangeAndAccuracy":{"type":"object","properties":{"score":{"type":"integer","minimum":0,"maximum":9}}},"generalFeedback":{"type":"string","maxLength":300}},"required":["coherence","lexicalResource","grammaticalRangeAndAccuracy","generalFeedback"]}"""
    dialogue_text = get_dialog_text(qa_data, attempt_info)
    subsection = attempt_info['subsection']
    prompt = f"""\
As an AI model simulating a professional IELTS examiner, your task is to evaluate a transcription of a student's dialogue from the IELTS Speaking Part {subsection.part_number}: {subsection.name}.
Your evaluation should strictly adhere to the official IELTS Speaking Band Descriptors for the following criteria: "Coherence" (a component of "Fluency and Coherence"), "Lexical Resource", "Grammatical Range and Accuracy", and "Pronunciation". Use the standard IELTS scoring methodology, but specifically for the "Fluency and Coherence" criterion, evaluate only "Coherence".

Provide a "score" for each mentioned criterion. This score should be a number from 0 to 9, representing the student's performance on that criterion in accordance with the official IELTS Speaking Band Descriptors for Academic and General Training tests.

In addition, provide "generalFeedback" string of up to 300 characters. This is an overall evaluation of the student's performance, based on all the criteria, and should highlight any significant trends or issues not addressed in the individual criterion evaluations.

Input:
'''
{dialogue_text}
'''

The expected JSON schema for your response is as follows:
'''
{response_json_schema}
'''
Your answer should be a straightforward JSON object without extra spaces or lines, adhering to the above JSON schema.\
"""
    chatgpt_messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt}
    ]

    # Getting a response from ChatGPT
    try:
        chatgpt_response_text = get_chatgpt_response(chatgpt_messages)
    except RetryError as e:
        print("All attempts failed. Last attempt:", e.last_attempt)
        flash("An error has occurred, please try again")
        abort(500)

    # Deserializing JSON and return result
    try:
        return json.loads(chatgpt_response_text)
    except json.decoder.JSONDecodeError:
        print("JSON deserialization error")
        flash("An error has occurred, please try again")
        abort(500)


@retry(stop=stop_after_attempt(5), wait=wait_fixed(1))
def get_chatgpt_response(messages: list, model="gpt-3.5-turbo", temperature=0) -> str:
    """Get a response from ChatGPT.

    Args:
        messages (list): A list of messages to send to ChatGPT.
        model (str, optional): The ChatGPT model to use. Defaults to "gpt-3.5-turbo".
        temperature (float, optional): The temperature parameter for the ChatGPT model. Defaults to 0.

    Returns:
        str: The text content of the response from ChatGPT.

    Raises:
        RetryError: If all attempts to get a response from ChatGPT fail.
        JSONDecodeError: If there is an error deserializing the JSON response from ChatGPT.
    """
    completion = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
    chatgpt_response_text = completion.choices[0].message["content"]
    return chatgpt_response_text


@measure_time
def assess_pronunciation_in_bulk(qa_data: tuple) -> tuple:
    """Assess pronunciation for multiple audio responses in parallel using Azure's pronunciation API.

    Args:
        qa_data (tuple): A tuple containing data for each question-answer pair.

    Returns:
        tuple: A tuple containing the updated question-answer data with pronunciation assessments.
    """
    with ThreadPoolExecutor() as executor:
        executor.map(get_azure_pronunciation_assessment, qa_data)
    return qa_data


def get_azure_pronunciation_assessment(qa_data: dict) -> None:
    """Request a pronunciation assessment for a single answer from Azure's pronunciation API.

    Args:
        qa_data (dict): A dictionary containing data for a single question-answer pair.

    Raises:
        RetryError: If all attempts to get a response from Azure's pronunciation API fail.
        Exception: If an unexpected error occurs.
    """
    audio_file = convert_audio_to_opus_bytesio(qa_data['answer_audio'])
    transcription_text = qa_data['answer_transcription']

    try:
        pronunciation_evaluation = request_azure_pronunciation_assessment(
            audio_file, transcription_text)
    except RetryError as e:
        print('All attempts failed. Last attempt:', e.last_attempt)
        flash('An error has occurred, please try again')
        abort(500)
    else:
        if pronunciation_evaluation['RecognitionStatus'] != 'Success':
            print('RecognitionStatus != Success')
            flash('An error occurred while trying to transcribe your speech, please try again.')
            abort(500)
        else:
            qa_data['pronunciation_assessment'] = pronunciation_evaluation


@retry(stop=stop_after_attempt(5), wait=wait_fixed(1))
def request_azure_pronunciation_assessment(audio_file: BytesIO,
                                           transcript: str) -> dict:
    """Send a request to Azure's pronunciation API to assess the pronunciation of a transcribed audio file.

    Args:
        audio_file (BytesIO): The audio file to be assessed.
        transcript (str): The transcribed text of the audio file.

    Returns:
        dict: A dictionary containing the pronunciation assessment.

    Raises:
        RetryError: If all attempts to get a response from Azure's pronunciation API fail.
    """
    language_code = "en-US"
    azure_region = "southeastasia"
    azure_api_key = os.getenv("AZURE_API_KEY")

    pronunciation_assessment_params = json.dumps({
        "ReferenceText": transcript,
        "GradingSystem": "HundredMark",
        "Dimension": "Comprehensive",
        "Granularity": "Word",
        "EnableMiscue": "True"
    })
    pronunciation_assessment_params = base64.b64encode(
        pronunciation_assessment_params.encode('utf-8')).decode("utf-8")

    azure_api_url = f"https://{azure_region}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language={language_code}&usePipelineVersion=0"
    azure_api_headers = {
        'Accept': 'application/json;text/xml',
        'Connection': 'Keep-Alive',
        'Content-Type': 'audio/webm; codecs=opus; samplerate=16000',
        'Ocp-Apim-Subscription-Key': azure_api_key,
        'Pronunciation-Assessment': pronunciation_assessment_params,
        'Transfer-Encoding': 'chunked',
        'Expect': '100-continue'
    }

    azure_api_response = requests.post(url=azure_api_url,
                                       data=get_chunk(audio_file),
                                       headers=azure_api_headers)
    audio_file.seek(0)
    return azure_api_response.json()
