import base64
from concurrent.futures import ThreadPoolExecutor
import json
import os
import time

import openai
import requests
from werkzeug.datastructures import FileStorage

from app.utils import measure_time, get_chunk, convert_audio, convert_dialogue_to_string


@measure_time
def transcribe_audio_file(audio_file: FileStorage) -> str:
    audio_file.name = "audio.webm"
    try:
        transcript = openai.Audio.transcribe(model="whisper-1",
                                             file=audio_file,
                                             language="en")
        audio_file.seek(0)
    except Exception as e:
        print(e)
        return ""
    else:
        return transcript["text"]


def transcribe_and_assess_pronunciation(audio_file: FileStorage) -> dict:
    transcript = transcribe_audio_file(audio_file).strip()
    if not transcript or transcript == 'Thank you.':
        result = {"transcript": None, "pronunciation": None}
    else:
        pronunciation_data = azure_assess_pronunciation(audio_file, transcript)
        result = {"transcript": transcript,
                  "pronunciation": pronunciation_data}
    return result


@measure_time
def batch_transcribe_and_assess_pronunciation(audio_files: list) -> list:
    with ThreadPoolExecutor() as executor:
        result = list(
            executor.map(transcribe_and_assess_pronunciation, audio_files))
    return result


@measure_time
def check_grammar(text: str) -> str:
    grammar_check = check_grammar_via_ginger(text)
    corrections = grammar_check["data"]["corrections"]
    corrections = sorted(corrections, key=lambda x: x["startIndex"],
                         reverse=True)
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
    for _ in range(10):
        try:
            completion = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )
            print(completion["usage"])
            gpt_response_json_string = completion.choices[0].message["content"]
            gpt_response_dict = json.loads(gpt_response_json_string)
        except (openai.error.APIError, openai.error.RateLimitError, openai.error.APIError, openai.error.ServiceUnavailableError) as e:
            print(e.error['message'])
            time.sleep(1)
        except json.decoder.JSONDecodeError as e:
            print(gpt_response_json_string)
            print("JSON decoding error, message::", str(e))
            break
        else:
            return gpt_response_dict


@measure_time
def azure_assess_pronunciation(audio_file, transcript: str) -> dict:
    audio_file = convert_audio(audio_file)
    language = "en-US"
    region = "southeastasia"
    subscription_key = os.getenv("AZURE_API_KEY")

    pron_assessment_params = json.dumps({
        "ReferenceText": transcript,
        "GradingSystem": "HundredMark",
        "Dimension": "Comprehensive",
        "Granularity": "Word",
        "EnableMiscue": "True"
    })
    pron_assessment_params = base64.b64encode(
        pron_assessment_params.encode('utf-8')).decode("utf-8")

    url = f"https://{region}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language={language}&usePipelineVersion=0"
    headers = {
        'Accept': 'application/json;text/xml',
        'Connection': 'Keep-Alive',
        'Content-Type': 'audio/webm; codecs=opus; samplerate=16000',
        'Ocp-Apim-Subscription-Key': subscription_key,
        'Pronunciation-Assessment': pron_assessment_params,
        'Transfer-Encoding': 'chunked',
        'Expect': '100-continue'
    }

    for i in range(1, 6):
        response = requests.post(url=url, data=get_chunk(audio_file),
                                 headers=headers)
        if response.status_code != 200:
            print("Azure response:", response.status_code, response.text)
            audio_file.seek(0)
            time.sleep(i)
        else:
            response = response.json()
            return response if response.get(
                "RecognitionStatus") == "Success" else None


# speaking evaluating v2.0

@measure_time
def gpt_evaluate_speaking_criterion(dialogue: str, criterion: str) -> dict:
    system = "You act as a professional IELTS examiner."
    json_schema = """{"type":"object","properties":{"score":{"type":"integer","minimum":0,"maximum":9},"feedback":{"type":"string","maxLength":200},"errors":{"type":"array","items":{"type":"string","maxLength":140}},"recommendations":{"type":"array","items":{"type":"string","maxLength":140}}},"required":["score","feedback","errors","recommendations"]}"""
    prompt = f"""\
As an AI model operating in the role of a professional IELTS examiner, you are tasked with evaluating a transcription of a student's dialogue from the IELTS Speaking Part 1.
The evaluation should be specifically based on the IELTS criterion "{criterion}", using the standard IELTS assessment methodologies.

Your response should be a single-line JSON object, following these specifications, and should not contain any additional text, annotations, unnecessary spaces, or line breaks:

1. "score": An integer from 0 to 9, indicating the student's performance on the "{criterion}" as per the IELTS scale.
2. "feedback": A string of up to 200 characters, summarizing the student's performance on the "{criterion}", as per IELTS assessment criteria.
3. "errors": An array, where each entry is a brief description (up to 140 characters long) of a specific error that impacted the student's performance on the "{criterion}", in line with IELTS assessment standards. Each entry should include the type of error, the incorrect phrase/word, and the correct version of the phrase/word.
4. "recommendations": An array of strings, each entry offering a concise piece of advice (up to 140 characters long) for the student on how to improve their performance on the "{criterion}".

Input:
'''
{dialogue}
'''

The expected JSON schema for your response is as follows:
'''
{json_schema}
'''"""
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt}
    ]
    result = get_gpt_json_completion(messages)
    result["criterion"] = criterion
    return result


@measure_time
def gpt_evaluate_speaking_pronunciation(dialogue: str, score: int, words: list):
    score = round((score / 100) * 9)
    system = "You act as a professional IELTS examiner."
    json_schema = """{"type":"object","properties":{"score":{"type":"integer","minimum":0,"maximum":9},"feedback":{"type":"string","maxLength":200},"required":["score","feedback"]}}"""
    prompt = f"""\
Given the examiner's questions, the student's responses, a provided 'score', and a list of incorrectly pronounced words as input, your task as an AI model is to create feedback for the student's performance specifically on the criterion "Pronunciation".
You need to generate a JSON response with no additional text.

Your response should include:

1. The provided pronunciation 'score': {score}.
2. A 'feedback' string that provides a general overview of the student's performance, limited to 180 characters.

Dialogue:
'''
{dialogue}
'''

Mispronounced words:
'''
{words}
'''

Your response should contain JSON and only JSON, with no additional text or notes.
Here is the expected JSON schema:
'''
{json_schema}
'''"""
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt}
    ]
    result = get_gpt_json_completion(messages)
    result["criterion"] = "Pronunciation"
    result["score"] = score
    return result


def batch_gpt_evaluate_speaking_new(questions_and_answers: list, score: int, misspelled_words: list):
    dialogue = convert_dialogue_to_string(questions_and_answers)
    tasks = [
        ("speaking_fluency", gpt_evaluate_speaking_criterion, (dialogue, "Fluency & Coherence")),
        ("speaking_lexis", gpt_evaluate_speaking_criterion, (dialogue, "Lexical Resource")),
        ("speaking_grammar", gpt_evaluate_speaking_criterion, (dialogue, "Grammatical Range and Accuracy")),
        ("speaking_pronunciation", gpt_evaluate_speaking_pronunciation, (dialogue, score, misspelled_words))
    ]

    results = {}
    futures = []
    with ThreadPoolExecutor() as executor:
        for name, func, args in tasks:
            future = executor.submit(func, *args)
            futures.append((name, future))

        for name, future in futures:
            results[name] = future.result()
    gpt_evaluate_all_speaking_criteria(dialogue)
    return results


@measure_time
def gpt_evaluate_all_speaking_criteria(dialogue: str) -> dict:
    system = "You act as a professional IELTS examiner."
    json_schema = """{"type":"object","properties":{"Fluency and Coherence":{"type":"object","properties":{"score":{"type":"integer","minimum":0,"maximum":9},"feedback":{"type":"string","maxLength":200},"errors":{"type":"array","items":{"type":"string","maxLength":140}},"recommendations":{"type":"array","items":{"type":"string","maxLength":140}}}},"Lexical Resource":{"type":"object","properties":{"score":{"type":"integer","minimum":0,"maximum":9},"feedback":{"type":"string","maxLength":200},"errors":{"type":"array","items":{"type":"string","maxLength":140}},"recommendations":{"type":"array","items":{"type":"string","maxLength":140}}}},"Grammatical Range and Accuracy":{"type":"object","properties":{"score":{"type":"integer","minimum":0,"maximum":9},"feedback":{"type":"string","maxLength":200},"errors":{"type":"array","items":{"type":"string","maxLength":140}},"recommendations":{"type":"array","items":{"type":"string","maxLength":140}}}},"Pronunciation":{"type":"object","properties":{"score":{"type":"integer","minimum":0,"maximum":9},"feedback":{"type":"string","maxLength":200},"errors":{"type":"array","items":{"type":"string","maxLength":140}},"recommendations":{"type":"array","items":{"type":"string","maxLength":140}}}},"General Feedback":{"type":"string","maxLength":500}},"required":["Fluency and Coherence","Lexical Resource","Grammatical Range and Accuracy","Pronunciation","General Feedback"]}"""
    prompt = f"""\
As an AI model operating in the role of a professional IELTS examiner, you are tasked with evaluating a transcription of a student's dialogue from the IELTS Speaking Part 1. The evaluation should be based on the following IELTS criteria: "Fluency and Coherence", "Lexical Resource", "Grammatical Range and Accuracy", and "Pronunciation", using the standard IELTS assessment methodologies.

For each criterion, your response should include:

1. "score": An integer from 0 to 9, indicating the student's performance on the criterion as per the IELTS scale.
2. "feedback": A string of up to 200 characters, summarizing the student's performance on the criterion, as per IELTS assessment criteria.
3. "errors": An array, where each entry is a brief description (up to 140 characters long) of a specific error that impacted the student's performance on the criterion, in line with IELTS assessment standards. Each entry should include the type of error, the incorrect phrase/word, and the correct version of the phrase/word.
4. "recommendations": An array of strings, each entry offering a concise piece of advice (up to 140 characters long) for the student on how to improve their performance on the criterion.

Furthermore, you should provide a "General Feedback" section, which provides an overall evaluation of the student's performance and highlights any significant trends or issues not addressed in the individual criterion evaluations.

Input:
'''
{dialogue}
'''

The expected JSON schema for your response is as follows:
'''
{json_schema}
'''"""
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt}
    ]
    result = get_gpt_json_completion(messages)
    print(result)
    return result
