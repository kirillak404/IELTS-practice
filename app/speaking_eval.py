from __future__ import annotations

import base64
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from io import BytesIO
from types import MappingProxyType
from typing import IO, Optional

from openai import OpenAI

client = OpenAI()
import requests
from pydub import AudioSegment
from tenacity import retry, stop_after_attempt, wait_fixed, RetryError

from app.models import QuestionSet, Subsection


@dataclass(frozen=True)
class SpeakingResults:
    """
    A data container for IELTS speaking evaluation results.

    Stores various aspects of the speaking evaluation process, providing
    a structured format for results that facilitates further analysis
    and feedback presentation.

    Attributes:
    ------------
    questions_set : QuestionSet
        The set of questions presented during the IELTS speaking test.

    answers : tuple[str]
        Transcriptions of the user's spoken answers.

    answers_pron_scores : tuple[dict]
        Pronunciation scores associated with each spoken answer, represented
        as dictionaries.

    general_feedback : str
        General feedback generated from the speaking evaluation.

    ielts_scores : MappingProxyType
        An immutable mapping of evaluated IELTS scores in various categories
        (e.g., pronunciation, grammar).

    Properties:
    ------------
    subsection : Subsection
        A specific subsection of the IELTS speaking test.

    section : Section
        The corresponding section of the IELTS speaking test.
    """
    questions_set: QuestionSet
    answers: tuple[str]
    answers_pron_scores: tuple[dict]
    general_feedback: str
    ielts_scores: MappingProxyType

    @property
    def subsection(self):
        return self.questions_set.subsection

    @property
    def section(self):
        return self.questions_set.subsection.section


class SpeechEvaluator:
    """
    A class to evaluate IELTS speaking responses.

    This class orchestrates the evaluation of spoken responses to IELTS
    speaking test prompts. It leverages ChatGPT for transcribing and
    evaluating responses, and Azure Pronunciation Assessor for assessing
    pronunciation. The evaluations provide a comprehensive understanding of
    the speaker's capabilities in different aspects like pronunciation,
    lexical resources, grammatical range, and accuracy, which are
    consolidated into IELTS scores.

    Attributes:
    - questions_set: An instance of the QuestionSet class containing IELTS speaking questions.
    - audio_files: A tuple of audio file objects containing the user's spoken responses.
    """

    def __init__(self, questions_set: QuestionSet, audio_files: tuple[IO[bytes]]):
        self.questions_set = questions_set
        self.subsection = questions_set.subsection
        self._audio_files = audio_files

        self._transcribed_answers = None
        self._azure_pron_scores = None
        self._gpt_speech_evaluation = None
        self._ielts_scores = {}

    def evaluate_speaking(self) -> SpeakingResults:
        """Evaluate speaking by orchestrating transcription and assessments."""

        # Step 1: Transcribe audio with OpenAI Whisper
        self._transcribe_audio_files()

        # Step 2: Concurrently assess speech with ChatGPT and pronunciation with Azure
        self._concurrent_speech_and_pronunciation_evaluation()

        # Step 3: Calculate IELTS scores from ChatGPT and Azure responses
        self._calculate_ielts_scores()

        return SpeakingResults(questions_set=self.questions_set,
                               answers=self._transcribed_answers,
                               answers_pron_scores=self._azure_pron_scores,
                               general_feedback=self._gpt_speech_evaluation['generalFeedback'],
                               ielts_scores=MappingProxyType(self._ielts_scores))

    def _transcribe_audio_files(self) -> None:
        """Transcribe audio files using ChatGPT."""
        with ThreadPoolExecutor() as executor:
            try:
                self._transcribed_answers = tuple(executor.map(
                    ChatGPT.transcribe_audio_file,
                    self._audio_files))
            except RetryError:
                raise SpeechEvaluationError('Transcription error. Please try again.')

    def _concurrent_speech_and_pronunciation_evaluation(self) -> None:
        """Evaluate speech and pronunciation in parallel."""
        with ThreadPoolExecutor() as executor:
            # creating text dialog with questions and user answers
            dialog = self._get_dialog_text()

            chatgpt_future = executor.submit(ChatGPT.evaluate_speech, dialog, self.subsection)
            azure_future = executor.submit(self._assess_pronunciation_in_bulk)

            self._gpt_speech_evaluation = chatgpt_future.result()
            self._azure_pron_scores = azure_future.result()

    # def _assess_pronunciation_in_bulk(self) -> tuple:
    #     """Evaluate pronunciation with Azure of all transcribed answers in bulk."""
    #     with ThreadPoolExecutor() as executor:
    #         audiofile_and_transcript_pairs = zip(self._audio_files, self._transcribed_answers)
    #         return tuple(executor.map(AzurePronunciationAssessor.get_assessment_from_tuple,
    #                             audiofile_and_transcript_pairs))

    def _assess_pronunciation_in_bulk(self) -> tuple:
        results = []
        audiofile_and_transcript_pairs = zip(self._audio_files,
                                             self._transcribed_answers)

        for pair in audiofile_and_transcript_pairs:
            result = AzurePronunciationAssessor.get_assessment_from_tuple(pair)
            results.append(result)
            time.sleep(1)  # задержка между запросами

        return tuple(results)

    def _get_dialog_text(self) -> str:
        """Generate a dialog string using questions and transcribed answers."""

        # Create cue card and answer for IELTS Speaking part 2
        if self.subsection.part_number == 2:
            topic = self.questions_set.topic
            questions = "\n- ".join(question.text for question in self.questions_set)
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
{self._transcribed_answers[0]}
###'''
            return dialog

        # Create dialog for IELTS Speaking part 1 or 3
        dialog = []
        for question, answer in zip(self.questions_set, self._transcribed_answers):
            question_and_answer = f'Q: {question.text}\nA: {answer}'
            dialog.append(question_and_answer)
        return "\n\n".join(dialog)

    def _calculate_ielts_scores(self) -> None:
        """Calculate IELTS scores based on GPT and Azure evaluations."""

        self._ielts_scores['lexicalResource'] = self._gpt_speech_evaluation['lexicalResource']['score']
        self._ielts_scores['grammaticalRangeAndAccuracy'] = self._gpt_speech_evaluation['grammaticalRangeAndAccuracy']['score']
        self._ielts_scores['pronunciation'] = self._get_avg_score_from_azure_pron_eval('PronScore')
        self._ielts_scores['fluencyAndCoherence'] = self._get_fluency_and_coherence_score()

    def _get_avg_score_from_azure_pron_eval(self, score_name: str) -> int:
        """Calculate average pronunciation score from Azure assessments."""

        # Extract the specified scores from azure answers evaluation
        scores = tuple(score['NBest'][0][score_name] for score in self._azure_pron_scores)

        # Compute the average score on a 100-point scale
        avg_score = sum(scores) / len(scores)

        # Convert the score to a 9-point scale and round it
        return round(avg_score / 100 * 9)

    def _get_fluency_and_coherence_score(self) -> int:
        """Derive a fluency and coherence score from Azure and GPT evaluations."""

        # Calculate average fluency score from Azure pron evaluation
        fluency_score = self._get_avg_score_from_azure_pron_eval('FluencyScore')

        # Get the coherence score from ChatGPT evaluation
        coherence_score = self._gpt_speech_evaluation['coherence']['score']

        # Return the average of fluency and coherence scores
        return round((fluency_score + coherence_score) / 2)


class ChatGPT:
    """
    Utility for ChatGPT-based speech evaluation and transcription.
    """

    @classmethod
    def evaluate_speech(cls, dialog: str, subsection: Subsection) -> dict:
        """
        Evaluate an IELTS Speaking test dialog using ChatGPT.

        Parameters:
        - dialog (str): The IELTS Speaking test dialog.
        - subsection (Subsection): The subsection information.

        Returns:
        - dict: The ChatGPT evaluation response.

        Example of returned data:
        {
            'coherence': {'score': 2},
            'lexicalResource': {'score': 3},
            'grammaticalRangeAndAccuracy': {'score': 3},
            'generalFeedback': 'Overall, your responses lacked coherence...'
        }
        """

        # Preparing system and user messages for ChatGPT interaction
        system_message = "You act as a professional IELTS examiner."
        response_json_schema = """{"type":"object","properties":{"coherence":{"type":"object","properties":{"score":{"type":"integer","minimum":0,"maximum":9}}},"lexicalResource":{"type":"object","properties":{"score":{"type":"integer","minimum":0,"maximum":9}}},"grammaticalRangeAndAccuracy":{"type":"object","properties":{"score":{"type":"integer","minimum":0,"maximum":9}}},"generalFeedback":{"type":"string","maxLength":300}},"required":["coherence","lexicalResource","grammaticalRangeAndAccuracy","generalFeedback"]}"""
        prompt = f"""\
    As an AI model simulating a professional IELTS examiner, your task is to evaluate a transcription of a student's dialogue from the IELTS Speaking Part {subsection.part_number}: {subsection.name}.
    Your evaluation should strictly adhere to the official IELTS Speaking Band Descriptors for the following criteria: "Coherence" (a component of "Fluency and Coherence"), "Lexical Resource", "Grammatical Range and Accuracy", and "Pronunciation". Use the standard IELTS scoring methodology, but specifically for the "Fluency and Coherence" criterion, evaluate only "Coherence".

    Provide a "score" for each mentioned criterion. This score should be a number from 0 to 9, representing the student's performance on that criterion in accordance with the official IELTS Speaking Band Descriptors for Academic and General Training tests.

    In addition, provide a "generalFeedback" text of up to 300 characters. It should be a friendly and personalized note directly addressing the student. Craft it to encapsulate your overall impressions about the student's performance without mentioning specific criteria, and focus instead on providing a broader picture of their achievements.

    Input:
    '''
    {dialog}
    '''

    The expected JSON schema for your response is as follows:
    '''
    {response_json_schema}
    '''
    Your answer should be a straightforward JSON object without extra spaces or lines, adhering to the above JSON schema.\
    """

        # Structuring messages for sending to ChatGPT
        chatgpt_messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]

        try:
            # Obtaining a response from ChatGPT
            chatgpt_response_text = cls._get_chat_completion(chatgpt_messages)
            return json.loads(chatgpt_response_text)
        except (RetryError, json.decoder.JSONDecodeError):
            raise SpeechEvaluationError("Error during speech evaluation with ChatGPT")

    @classmethod
    @retry(stop=stop_after_attempt(5), wait=wait_fixed(1))
    def _get_chat_completion(cls, messages: list,
                             temperature=0,
                             model="gpt-3.5-turbo") -> str:
        """Retrieve a ChatGPT completion with retry logic."""

        completion = client.chat.completions.create(model=model,
        messages=messages,
        temperature=temperature)
        return completion.choices[0].message.content

    @classmethod
    @retry(stop=stop_after_attempt(5), wait=wait_fixed(1))
    def transcribe_audio_file(cls, audio_file: IO[bytes]) -> Optional[str]:
        """Transcribe an audio file using OpenAI Whisper."""
        # Transcribing audio file using OpenAI Whisper ASR API

        audio_file_bytes = BytesIO(audio_file.read())
        audio_file_bytes.name = 'audio.webm'

        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file_bytes,
            language='en',
            response_format='text'
        )

        # Resetting the file pointer after read operation
        audio_file.seek(0)
        transcript = transcript.strip()
        print(transcript)

        # Ensuring that the transcript is not empty or doesn't contain placeholder/fallback values
        if not transcript or transcript in ('you', 'Thank you.'):
            raise SpeechEvaluationError('Not all questions answered. Please try again.')
        return transcript


class AzurePronunciationAssessor:
    _LANGUAGE_CODE = "en-US"
    _AZURE_REGION = "germanywestcentral"
    _azure_api_key = os.getenv("AZURE_API_KEY")

    @classmethod
    @retry(stop=stop_after_attempt(5), wait=wait_fixed(1))
    def get_assessment(cls, audio_file: IO, transcript: str) -> dict:
        """
        Get the assessment of the pronunciation from Azure.

        Parameters:
        - audio_file (IO): An input audio file.
        - transcript (str): The transcript to assess against.

        Returns:
        - dict: The response from Azure API as a JSON.

        Example of returned data:
        {
            'RecognitionStatus': 'Success',
            'Offset': 6800000,
            'Duration': 22700000,
            'NBest': [
                {
                    'Lexical': 'what is your name',
                    'ITN': 'what is your name',
                    'MaskedITN': 'what is your name',
                    'Display': 'What is your name?',
                    'AccuracyScore': 99.0,
                    'FluencyScore': 99.0,
                    'CompletenessScore': 100.0,
                    'PronScore': 99.2,
                    'Words': [
                        {'Word': 'what', 'AccuracyScore': 98.0, 'ErrorType': 'None', 'Offset': 10100000, 'Duration': 4900000},
                        {'Word': 'is', 'AccuracyScore': 100.0, 'ErrorType': 'None', 'Offset': 15300000, 'Duration': 2300000},
                        {'Word': 'your', 'AccuracyScore': 100.0, 'ErrorType': 'None', 'Offset': 17700000, 'Duration': 2600000},
                        {'Word': 'name', 'AccuracyScore': 98.0, 'ErrorType': 'None', 'Offset': 20400000, 'Duration': 6700000}
                    ]
                }
            ]
        }
        """
        audio_file.seek(0)
        audio_file = cls._convert_audio_to_opus_bytesio(audio_file)

        pronunciation_assessment_params = json.dumps({
            "ReferenceText": transcript,
            "GradingSystem": "HundredMark",
            "Dimension": "Comprehensive",
            "Granularity": "Word",
            "EnableMiscue": "True"
        })

        pronunciation_assessment_params = base64.b64encode(
            pronunciation_assessment_params.encode('utf-8')).decode("utf-8")

        azure_api_url = f"https://{cls._AZURE_REGION}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language={cls._LANGUAGE_CODE}&usePipelineVersion=0"
        azure_api_headers = {
            'Accept': 'application/json;text/xml',
            'Connection': 'Keep-Alive',
            'Content-Type': 'audio/webm; codecs=opus; samplerate=16000',
            'Ocp-Apim-Subscription-Key': cls._azure_api_key,
            'Pronunciation-Assessment': pronunciation_assessment_params,
            'Transfer-Encoding': 'chunked',
            'Expect': '100-continue'
        }

        try:
            azure_api_response = cls._get_azure_response(
                url=azure_api_url,
                data=cls._get_chunk(audio_file),
                headers=azure_api_headers)
        except RetryError:
            raise SpeechEvaluationError('Error during Azure pronunciation evaluation')
        return azure_api_response.json()

    @classmethod
    def get_assessment_from_tuple(cls, audiofile_and_transcript: tuple) -> dict:
        return cls.get_assessment(*audiofile_and_transcript)

    @staticmethod
    @retry(stop=stop_after_attempt(5), wait=wait_fixed(1))
    def _get_azure_response(url, data, headers):
        print('_get_azure_response')
        time.sleep(1)
        response = requests.post(url=url, data=data, headers=headers)
        print(response.status_code)
        if response.status_code != 200:
            print(response.text)
            raise Exception("Ошибка при отправке файла: " + response.text)
        return response

    @staticmethod
    def _get_chunk(audio_file: IO, chunk_size=1024):
        while True:
            chunk = audio_file.read(chunk_size)
            if not chunk:
                break
            yield chunk

    @staticmethod
    def _convert_audio_to_opus_bytesio(audio_file: IO) -> BytesIO:
        """
        Convert audio file to OPUS format with a 16000 Hz frame rate and single channel,
        returning it as a BytesIO object.

        Parameters:
        - audio_file (IO): An input audio file.

        Returns:
        - BytesIO: The converted audio in OPUS format as a BytesIO object.
        """
        # Convert FileStorage to Bytes
        blob = BytesIO(audio_file.read())
        blob.name = 'audio.webm'

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


class SpeechEvaluationError(Exception):
    pass