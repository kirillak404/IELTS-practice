import concurrent.futures
import json
import os
import time

import openai
import requests

from app.utils import measure_time


@measure_time
def transcribe_audio(audio_file) -> str:

    timestamp = str(time.time()).replace(".", "")
    audio_file.name = f"audio{timestamp}.webm"
    prompt = "Uh, right now I'm, um... (unintelligible)... Yeah, I'm a student at Moscow State University. I'm studying... umm... Computer (unintelligible)."
    transcript = openai.Audio.transcribe(model="whisper-1",
                                         prompt=prompt,
                                         file=audio_file,
                                         language="en")

    # save file
    path = os.path.join("audio_files", audio_file.name)
    audio_file.save(path)
    return transcript["text"]


def transcribe_audio_and_check_grammar(audio_file):
    transcript = transcribe_audio(audio_file).strip()
    if not transcript or transcript == 'Thank you.':
        result = {"transcript": "", "errors": ""}
    else:
        transcript_with_errors = check_grammar(transcript)
        result = {"transcript": transcript, "errors": transcript_with_errors}
    return result


@measure_time
def transcribe_and_check_errors_in_multiple_files(audio_files: list) -> list:
    with concurrent.futures.ThreadPoolExecutor() as executor:
        result = list(executor.map(transcribe_audio_and_check_grammar, audio_files))
    return result


@measure_time
def check_grammar(text: str) -> str:
    grammar_check = check_grammar_via_ginger(text)
    corrections = grammar_check["data"]["corrections"]
    corrections = sorted(corrections, key=lambda x: x["startIndex"], reverse=True)
    for correction in corrections:
        if correction.get("correctionText"):

            # get data about mistake
            data_error_type = correction["type"]
            data_error_short_description = correction["shortDescription"]
            data_error_long_description = correction["longDescription"]
            data_corrected_text = correction["correctionText"]
            mistake_text = correction["mistakeText"]

            # updating part of text
            prefix = text[:correction['startIndex']]
            suffix = text[correction['endIndex'] + 1:]
            replacement = f'''\
    <span class="error" \
    data-error-type="{data_error_type}" \
    data-error-short-description="{data_error_short_description}" \
    data-error-long-description="{data_error_long_description}" \
    data-corrected-text="{data_corrected_text}">\
    {mistake_text}\
    </span>'''
            text = prefix + replacement + suffix

    return text


def check_grammar_via_ginger(text: str) -> dict:
    url = "https://ginger3.p.rapidapi.com/correctAndRephrase"
    rapid_api_key = os.getenv("RAPID_API_KEY")
    querystring = {"text": text}
    headers = {
        "X-RapidAPI-Key": rapid_api_key,
        "X-RapidAPI-Host": "ginger3.p.rapidapi.com"
    }
    for _ in range(10):
        response = requests.get(url, headers=headers, params=querystring)
        response = response.json()
        if response['message'] == "Success":
            return response
        else:
            time.sleep(1)


def get_gpt_json_completion(messages: list,
                            model="gpt-3.5-turbo",
                            temperature=0) -> dict:
    gpt_response_dict = None
    for _ in range(10):
        try:
            completion = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )
            gpt_response_json_string = completion.choices[0].message[
                "content"]
            gpt_response_dict = json.loads(gpt_response_json_string)
        except (openai.error.APIError, openai.error.RateLimitError) as e:
            print(e.error['message'])
            time.sleep(1)
        except json.decoder.JSONDecodeError as e:
            print(gpt_response_json_string)
            print("JSON decoding error, message::", str(e))
        else:
            with open('gpt_last_response.json', "w") as file:
                file.write(gpt_response_json_string)
            break
    return gpt_response_dict


@measure_time
def gpt_evaluate_speaking(questions_and_answers: list) -> dict:

    # formatting questions and answer
    formatted_questions_and_answers = {}
    for number, qa in enumerate(questions_and_answers, start=1):
        formatted_questions_and_answers[f"Q{number}"] = qa["question"]
        formatted_questions_and_answers[f"A{number}"] = qa["answer"]

    system = "You act as a professional IELTS examiner."
    json_example = """\
{
	"generalFeedback": "Provide general feedback on the student's overall performance in this section. (string)",
	"criteria": {
		"fluency": {
			"score": "Evaluate the student's fluency and coherence on a scale of 0 to 9. (integer)",
			"feedback": "Evaluate the student's ability to maintain a smooth and natural flow of speech, as well as the organization and logical connection of ideas. (string)"
		},
		"grammar": {
			"score": "Evaluate the student's grammatical range and accuracy on a scale of 0 to 9. (integer)",
			"feedback": "Evaluate the student's grammatical accuracy, including the correct use of various sentence structures. Assess their command of grammar. (string)"
		},
		"lexic": {
			"score": "Evaluate the student's lexical resource on a scale of 0 to 9. (integer)",
			"feedback": "Evaluate the student's range and appropriateness of vocabulary usage. Consider the precision and command of lexical resources. (string)"
		},
		"pron": {
			"score": "Evaluate the student's pronunciation on a scale of 0 to 9. (integer)",
			"feedback": "Evaluate the student's pronunciation, including the clarity, accuracy, intonation, and stress patterns in their speech. (string)"
		}
	}
}
"""
    prompt = f"""
Your task is to evaluate the student's responses to IELTS Speaking Part 1: Introduction and Interview using the standard criteria: "Fluency and Coherence", "Grammatical Range and Accuracy", "Lexical Resources", and "Pronunciation". For each criterion, provide a score on a scale of 0 to 9 and corresponding feedback.

1. Fluency and Coherence: Evaluate the student's ability to maintain a smooth and natural flow of speech, as well as the organization and logical connection of ideas.
2. Grammatical Range and Accuracy: Evaluate the student's grammatical accuracy, including the correct use of various sentence structures. Assess their command of grammar.
3. Lexical Resources: Evaluate the student's range and appropriateness of vocabulary usage. Consider the precision and command of lexical resources.
4. Pronunciation: Evaluate the student's pronunciation, including the clarity, accuracy, intonation, and stress patterns in their speech.

In addition to the criterion evaluation, provide general feedback on the student's overall performance in this section. Length no longer than 280 characters.

Please provide evaluations and feedback for each criterion accordingly. Length no longer than 140 characters.

Here is a list of questions and answers received from the student:
'''
{str(formatted_questions_and_answers)}
'''
Your response should be a single JSON object following this format:
{str(json_example)}
"""
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt}
    ]

    result = get_gpt_json_completion(messages)
    return result
