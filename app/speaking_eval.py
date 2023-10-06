from __future__ import annotations

import base64
import json
import os
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from typing import IO, Optional

import openai
import requests
from pydub import AudioSegment
from tenacity import retry, stop_after_attempt, wait_fixed, RetryError

from app.models import QuestionSet, Subsection


class SpeechEvaluator:
    def __init__(self, questions_set: QuestionSet, audio_files: tuple[IO[bytes]]):
        self.questions_set = questions_set
        self.subsection = questions_set.subsection
        self._audio_files = audio_files

        self.transcribed_user_answers = None
        self.azure_answers_evaluation = None
        self.chatgpt_speech_evaluation = None

    def evaluate_speaking(self):

        # Step 1: Transcribe audio with OpenAI Whisper
        self._transcribe_audio_files_in_bulk()

        # Step 2: Concurrently assess speech with ChatGPT and pronunciation with Azure
        self._parallel_evaluation_with_gpt_and_azure()

    def _transcribe_audio_files_in_bulk(self):
        with ThreadPoolExecutor() as executor:
            try:
                self.transcribed_user_answers = tuple(executor.map(
                    ChatGPT().transcribe_audio_file,
                    self._audio_files))
            except RetryError:
                raise SpeechEvaluationError('Transcription error. Please try again.')

    def _parallel_evaluation_with_gpt_and_azure(self):

        with ThreadPoolExecutor() as executor:
            # creating text dialog with questions and user answers
            dialog = self._get_dialog_text()

            chatgpt_future = executor.submit(ChatGPT().evaluate_speech, dialog, self.subsection)
            azure_future = executor.submit(self._assess_pronunciation_in_bulk)

            self.chatgpt_speech_evaluation = chatgpt_future.result()
            self.azure_answers_evaluation = azure_future.result()

    def _assess_pronunciation_in_bulk(self):
        with ThreadPoolExecutor() as executor:
            audiofile_and_transcript_pairs = zip(self._audio_files, self.transcribed_user_answers)
            return tuple(executor.map(AzurePronunciationAssessor().get_assessment_from_tuple,
                                audiofile_and_transcript_pairs))

    def _get_dialog_text(self) -> str:
        """Combining question and user answers into one text"""
        speaking_part_number = self.questions_set.subsection.part_number

        # Create cue card and answer for IELTS Speaking part 2
        if speaking_part_number == 2:
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
{self.transcribed_user_answers[0]}
###'''
            return dialog

        # Create dialog for IELTS Speaking part 1 or 3
        dialog = []
        for question, answer in zip(self.questions_set, self.transcribed_user_answers):
            question_and_answer = f'Q: {question.text}\nA: {answer}'
            dialog.append(question_and_answer)
        return "\n\n".join(dialog)


class ChatGPT:

    @staticmethod
    def evaluate_speech(dialog: str, subsection: Subsection):
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
        chatgpt_messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]

        # Getting a response from ChatGPT and deserializing it
        try:
            chatgpt_response_text = ChatGPT._get_chat_completion(chatgpt_messages)
            return json.loads(chatgpt_response_text)
        except (RetryError, json.decoder.JSONDecodeError):
            raise SpeechEvaluationError("Error during speech evaluation with ChatGPT")

    @staticmethod
    @retry(stop=stop_after_attempt(5), wait=wait_fixed(1))
    def _get_chat_completion(messages: list,
                             temperature=0,
                             model="gpt-3.5-turbo") -> str:
        completion = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature)
        return completion.choices[0].message["content"]

    @staticmethod
    @retry(stop=stop_after_attempt(5), wait=wait_fixed(1))
    def transcribe_audio_file(audio_file: IO[bytes]) -> Optional[str]:
        transcript = openai.Audio.transcribe(model='whisper-1',
                                             file=audio_file,
                                             language='en',
                                             response_format='text')
        audio_file.seek(0)
        transcript = transcript.strip()
        # Checking that the answer exists
        if not transcript or transcript in ('you', 'Thank you.'):
            raise SpeechEvaluationError('Not all questions answered. Please try again.')
        return transcript


class AzurePronunciationAssessor:
    _language_code = "en-US"
    _azure_api_key = os.getenv("AZURE_API_KEY")
    _azure_region = "germanywestcentral"

    def get_assessment(self, audio_file: IO, transcript: str):

        audio_file = self._convert_audio_to_opus_bytesio(audio_file)

        pronunciation_assessment_params = json.dumps({
            "ReferenceText": transcript,
            "GradingSystem": "HundredMark",
            "Dimension": "Comprehensive",
            "Granularity": "Word",
            "EnableMiscue": "True"
        })

        pronunciation_assessment_params = base64.b64encode(
            pronunciation_assessment_params.encode('utf-8')).decode("utf-8")

        azure_api_url = f"https://{self._azure_region}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language={self._language_code}&usePipelineVersion=0"
        azure_api_headers = {
            'Accept': 'application/json;text/xml',
            'Connection': 'Keep-Alive',
            'Content-Type': 'audio/webm; codecs=opus; samplerate=16000',
            'Ocp-Apim-Subscription-Key': self._azure_api_key,
            'Pronunciation-Assessment': pronunciation_assessment_params,
            'Transfer-Encoding': 'chunked',
            'Expect': '100-continue'
        }

        try:
            azure_api_response = self._get_azure_response(
                url=azure_api_url,
                data=self._get_chunk(audio_file),
                headers=azure_api_headers)
        except RetryError:
            raise SpeechEvaluationError('Error during Azure pronunciation evaluation')

        audio_file.seek(0)
        return azure_api_response.json()

    @staticmethod
    @retry(stop=stop_after_attempt(5), wait=wait_fixed(1))
    def _get_azure_response(url, data, headers):
        return requests.post(url=url, data=data, headers=headers)

    def get_assessment_from_tuple(self, audiofile_and_transcript: tuple):
        return self.get_assessment(*audiofile_and_transcript)

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