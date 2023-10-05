from concurrent.futures import ThreadPoolExecutor
from typing import Optional
import json

import openai
from flask import abort, flash
from tenacity import retry, stop_after_attempt, wait_fixed, RetryError
from werkzeug.datastructures import FileStorage

from app.models import QuestionSet


class SpeechEvaluator:
    def __init__(self, questions_set: QuestionSet, audio_files: tuple):
        self.questions_set = questions_set
        self.audio_files = audio_files

        self.evaluate_speaking()

    def evaluate_speaking(self):
        # Step 1: Transcribing audio files with OpenAI Whisper
        self.transcribe_audio_files_in_bulk()
        print(self.evaluate_speech_with_chatgpt())
        # TODO save gpt speech evaluation and next step is Azure evaluation...

    def transcribe_audio_files_in_bulk(self):
        with ThreadPoolExecutor() as executor:
            try:
                self.transcribed_user_answers = tuple(executor.map(
                    self.transcribe_single_audio_file,
                    self.audio_files))
            except RetryError:
                flash('Transcription error. Please try again.')
                abort(500)

    @staticmethod
    @retry(stop=stop_after_attempt(5), wait=wait_fixed(1))
    def transcribe_single_audio_file(audio_file: FileStorage) -> Optional[str]:
        transcript = openai.Audio.transcribe(model='whisper-1',
                                             file=audio_file,
                                             language='en',
                                             response_format='text')
        audio_file.seek(0)
        transcript = transcript.strip()
        # Checking that the answer exists
        if not transcript or transcript in ('you', 'Thank you.'):
            flash('Not all questions answered. Please try again.')
            abort(400)
        return transcript

    def evaluate_speech_with_chatgpt(self):
        system_message = "You act as a professional IELTS examiner."
        response_json_schema = """{"type":"object","properties":{"coherence":{"type":"object","properties":{"score":{"type":"integer","minimum":0,"maximum":9}}},"lexicalResource":{"type":"object","properties":{"score":{"type":"integer","minimum":0,"maximum":9}}},"grammaticalRangeAndAccuracy":{"type":"object","properties":{"score":{"type":"integer","minimum":0,"maximum":9}}},"generalFeedback":{"type":"string","maxLength":300}},"required":["coherence","lexicalResource","grammaticalRangeAndAccuracy","generalFeedback"]}"""
        dialogue_text = self.get_dialog_text()
        subsection = self.questions_set.subsection
        prompt = f"""\
As an AI model simulating a professional IELTS examiner, your task is to evaluate a transcription of a student's dialogue from the IELTS Speaking Part {subsection.part_number}: {subsection.name}.
Your evaluation should strictly adhere to the official IELTS Speaking Band Descriptors for the following criteria: "Coherence" (a component of "Fluency and Coherence"), "Lexical Resource", "Grammatical Range and Accuracy", and "Pronunciation". Use the standard IELTS scoring methodology, but specifically for the "Fluency and Coherence" criterion, evaluate only "Coherence".

Provide a "score" for each mentioned criterion. This score should be a number from 0 to 9, representing the student's performance on that criterion in accordance with the official IELTS Speaking Band Descriptors for Academic and General Training tests.

In addition, provide a "generalFeedback" text of up to 300 characters. It should be a friendly and personalized note directly addressing the student. Craft it to encapsulate your overall impressions about the student's performance without mentioning specific criteria, and focus instead on providing a broader picture of their achievements.

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

        # Getting a response from ChatGPT and deserializing it
        try:
            chatgpt_response_text = self.get_chatgpt_response(chatgpt_messages)
            return json.loads(chatgpt_response_text)
        except RetryError as e:
            flash("An error has occurred, please try again")
            abort(500)
        except json.decoder.JSONDecodeError:
            flash("An error has occurred, please try again")
            abort(500)

    def get_dialog_text(self) -> str:
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

    @staticmethod
    @retry(stop=stop_after_attempt(5), wait=wait_fixed(1))
    def get_chatgpt_response(messages: list,
                             model="gpt-3.5-turbo",
                             temperature=0) -> str:
        completion = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature)
        return completion.choices[0].message["content"]
