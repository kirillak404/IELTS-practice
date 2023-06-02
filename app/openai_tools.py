import json
import time

import openai
import concurrent.futures


def transcribe_audio(audio_file) -> str:
    audio_file.name = "audio.webm"
    transcript = openai.Audio.transcribe("whisper-1",
                                         file=audio_file,
                                         language="en")
    return transcript["text"]


def transcribe_audio_and_check_grammar(audio_file):
    transcript = transcribe_audio(audio_file).strip()
    if not transcript or transcript == 'Thank you.':
        result = {"transcript": "", "errors": ""}
    else:
        transcript_with_errors = check_grammar(transcript)
        result = {"transcript": transcript, "errors": transcript_with_errors}
    return result


def transcribe_and_check_errors_in_multiple_files(audio_files: list) -> list:
    with concurrent.futures.ThreadPoolExecutor() as executor:
        result = list(executor.map(transcribe_audio_and_check_grammar, audio_files))
    return result


questions = [
    "What is your favorite childhood memory?",
    "How do you envision your life in 10 years?",
    "What is the most challenging experience you've faced?",
    "If you could travel anywhere in the world, where would you go?",
    "What is your favorite book and why?"
]

answers = "My favorit childhood memory is when me and my friend goes to the beach and we builds sand castles. In 10 years, I envision myself living in a big houses with a successful careers. The most challenging experience I've faced was when I had to gives a presentation in front of a large audiences. If I could travel anywheres in the worlds, I would goes to Parises because of its rich historys and beautiful landmarks. My favorit book is 'Harry Potter' because it takes me to a magical worlds fulls of adventures and friendships."


class ChatGPT:
    def __init__(self, model="gpt-3.5-turbo"):  # gpt-4 | gpt-3.5-turbo
        self.model = model

    def get_completion(self, messages: list, temperature=0) -> dict:
        gpt_response_dict = None
        start = time.time()
        for _ in range(10):
            try:
                completion = openai.ChatCompletion.create(
                    model=self.model,
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

        finish = time.time()
        time_result = f"Execution time: {int(finish - start)} seconds"
        print(time_result)
        return gpt_response_dict

    def find_errors_in_text(self, text: str):
        system = "As an AI language model, your role is akin to Grammarly."

        text_example_prompt = "I don't exercise very regular. I tries to go to the gym once a week, but sometimes I'm too busy and not have enough time."
        json_example_prompt = """
{
	"text": "I <err>likes</err> rock music. Sometimes, I <err>listens</err> to pop. I don't <err>enjoys</err> <err>classic</err> music. It is boring.",
	"errors": [{
		"err": "likes",
		"type": "grammar",
		"desc": "It appears that the subject pronoun I and the verb likes are not in agreement.",
		"corr": "like"
	}, {
		"err": "listens",
		"type": "grammar",
		"desc": "It appears that the subject pronoun I and the verb listens are not in agreement.",
		"corr": "listen"
	}, {
		"err": "enjoys",
		"type": "grammar",
		"desc": "It appears that the verb enjoys is incorrectly used with the helping verb do.",
		"corr": "enjoy"
	}, {
		"err": "classic",
		"type": "spelling",
		"desc": "The word classic doesn’t seem to fit this context.",
		"corr": "classical"
	}]
}
        """
        prompt = f"""
Your task is to perform the following actions:

1. Scrutinize the given text for spelling, grammar, punctuation, and word usage errors.
2. Enclose erroneous words or phrases in <err></err> tags. For instance, "I <err>is</err> happy" indicates an error in the original text "I is happy".
3. Provide a comprehensive explanation for each error, detailing its type, the reason it's incorrect, and the correct version.
4. If there are no errors in the text, output JSON consisting of just the string ["no errors"].
5. Assemble the analysed text, tagged errors, and their explanations into a JSON object.

The JSON object should resemble the following example:
'''
{json_example_prompt}
'''

Analyze the text below, enclosed in triple single quotes:
'''
{text_example_prompt}
'''
        """
        json_answer_example = """
{
	"text": "I don't exercise very <err>regular</err>. I <err>tries</err> to go to the gym once a week, but sometimes I'm too busy and <err>not have</err> enough time.",
	"errors": [{
		"err": "regular",
		"type": "spelling",
		"desc": "The word regular doesn’t seem to fit this context.",
		"corr": "regularly"
	}, {
		"err": "tries",
		"type": "grammar",
		"desc": "It appears that the subject pronoun I and the verb tries are not in agreement.",
		"corr": "try"
	}, {
		"err": "not",
		"type": "grammar",
		"desc": "It seems that you are missing a verb.",
		"corr": "do not"
	}]
}
        """

        text_example_2 = """
Please analyze the text below:
'''
My favorite hobby is playing football. I like to play football every weekend with my friends. It's very fun and keeps me active.
'''
"""
        json_answer_example_2 = '["no errors"]'

        text_example_3 = """
Analyze the text below, enclosed in triple single quotes:
'''
I from Indonesia. Is very big country. Have lot of cities. I lives in capital, Moscow. Is big and crowded city.
'''
"""
        json_answer_example_3 = """
{
	"text": "I <err>from</err> Indonesia. Is <err>very</err> big country. Have <err>lot</err> of cities. I <err>lives</err> in <err>capital</err>, Moscow. Is <err>big</err> and crowded city.",
	"errors": [{
		"err": "from",
		"type": "grammar",
		"desc": "It seems that you are missing a verb.",
		"corr": "am from"
	}, {
		"err": "very",
		"type": "grammar",
		"desc": "It seems that there is an article usage problem here.",
		"corr": "a very"
	}, {
		"err": "lot",
		"type": "grammar",
		"desc": "It appears that the phrase lot does not contain the correct article usage.",
		"corr": "a lot"
	}, {
		"err": "lives",
		"type": "grammar",
		"desc": "It appears that the subject pronoun I and the verb lives are not in agreement.",
		"corr": "live"
	}, {
		"err": "capital",
		"type": "grammar",
		"desc": "The noun phrase capital seems to be missing a determiner before it.",
		"corr": "the capital"
	}, {
		"err": "big",
		"type": "grammar",
		"desc": "It seems that there is an article usage problem here.",
		"corr": "a big"
	}]
}
"""
        real_prompt = f"""
Analyze the text below, enclosed in triple single quotes:
'''
{text}
'''

Don't forget:
1. Your output should consist only of a JSON object, without any additional text.
2. Enclose erroneous words or phrases in <err></err> tags. 
"""

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": json_answer_example},
            {"role": "user", "content": text_example_2},
            {"role": "assistant", "content": json_answer_example_2},
            {"role": "user", "content": text_example_3},
            {"role": "assistant", "content": json_answer_example_3},
            {"role": "user", "content": real_prompt}
        ]

        text_errors = self.get_completion(messages)
        if text_errors == ['no errors']:
            text_errors = {"text": text, "errors": []}
        return text_errors

    def check_multiple_texts_for_errors(self, texts: list) -> list:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            result = list(executor.map(self.find_errors_in_text, texts))
        return result


def check_grammar(text: str) -> str:
    text = "I don't exercise very regular. I tries to go to the gym once a week, but sometimes I'm too busy and not have enough time."
    json_response = """{
"status": true,
"message": "Success",
"timestamp": 1685690933109,
"data": {
"id": "bf4f5890-178a-42a8-b331-7b4dcdabb42a",
"language": "eng",
"text": "I don't exercise very regularly. I try to go to the gym once a week, but sometimes I'm too busy and not have enough time.",
"engine": "Ginger",
"truncated": false,
"timeTaken": 670,
"corrections": [
  {
    "group": "AutoCorrected",
    "type": "Grammar",
    "shortDescription": "Grammar Mistake",
    "longDescription": "A wrong word form was used",
    "startIndex": 22,
    "endIndex": 28,
    "mistakeText": "regular",
    "correctionText": "regularly",
    "suggestions": [
      {
        "text": "regularly",
        "category": "Verb"
      }
    ]
  },
  {
    "group": "AutoCorrected",
    "type": "Grammar",
    "shortDescription": "Grammar Mistake",
    "longDescription": "Mismatch between the plurality of the verb and the subject",
    "startIndex": 33,
    "endIndex": 37,
    "mistakeText": "tries",
    "correctionText": "try",
    "suggestions": [
      {
        "text": "try",
        "category": "Verb"
      },
      {
        "text": "am trying",
        "category": "Verb"
      },
      {
        "text": "have tried",
        "category": "Verb"
      },
      {
        "text": "have been trying",
        "category": "Verb"
      }
    ]
  }
],
"sentences": [
  {
    "startIndex": 0,
    "endIndex": 29,
    "status": "Corrected"
  },
  {
    "startIndex": 31,
    "endIndex": 120,
    "status": "Corrected"
  }
],
"autoReplacements": [],
"stats": {
  "textLength": 121,
  "wordCount": 27,
  "sentenceCount": 2,
  "longestSentence": 90
}
}
}"""
    grammar = json.loads(json_response)
    corrections = grammar["data"]["corrections"]
    corrections = sorted(corrections, key=lambda x: x["startIndex"], reverse=True)
    for correction in corrections:
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
