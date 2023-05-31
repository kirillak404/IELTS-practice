import json
import time

import openai
import concurrent.futures

from app.utils import convert_list_to_string


def transcribe_audio(audio_file):
    audio_file.name = "audio.webm"
    transcript = openai.Audio.transcribe("whisper-1",
                                         file=audio_file,
                                         language="en")
    return transcript["text"]


questions = [
    "What is your favorite hobby?",
    "Do you enjoy cooking?",
    "How often do you exercise?",
    "What kind of music do you like?",
    "What is your favorite season?"
]
answers = """
My favorite hobby is playing football. I likes to play football every weekend with my friends. It's very fun and keep me active. \
Yes, I enjoy cooking sometimes. I often cooks dinner for my family. My mother teach me some recipes and I tries to cook them. It's a good way to relax.\
I don't exercise very regular. I tries to go to the gym once a week, but sometimes I'm too busy and not have enough time. I know it's important to stay healthy, so I need to make more time for it.\
I likes all kinds of music. I listens to pop, rock, and sometimes classic music. Music helps me to relax and forget about problems. I usually listens to music when I am study or cleaning the house.\
My favorite season is summer. I likes the hot weather and go to the beach. I can swims in the ocean and gets a nice tan. Summer is the best time of the year for me.
"""


class ChatGPT:
    def __init__(self, model="gpt-3.5-turbo"):  # gpt-4 | gpt-3.5-turbo
        self.model = model

    def get_response(self, messages: list):
        start = time.time()

        for _ in range(10):
            try:
                completion = openai.ChatCompletion.create(
                    model=self.model,
                    messages=messages
                )
                result = completion.choices[0].message["content"]
                result_json = json.loads(result)
            except openai.error.APIError as e:
                print(e.error['message'])
                time.sleep(1)
            except json.decoder.JSONDecodeError as e:
                print(result)
                print("JSON decoding error, message::", str(e))
            else:
                print(result)
                with open('gpt_response_check_answers.json', "w") as file:
                    file.write(result)
                break

        finish = time.time()
        time_result = f"Execution time: {int(finish - start)} seconds"
        print(time_result)

    def evaluate_speaking(self, questions: list, answers: str):
        system = "You are an AI functioning as a professional IELTS examiner. Your output will consist solely of a JSON object, without any additional text."
        json_example = '''{"fluency_and_coherence":5,"lexical_resource":6,"grammatical_range_and_accuracy":4,"pronunciation":5,"data":[{"q":"Can you tell me a little about yourself?","a":"I lives in Moscow. I has a big family. They is very kind and smart."},{"q":"Where are you from?","a":"I from Russia. Is very big country."}]}'''
        questions = convert_list_to_string(questions)
        prompt = f"""
Your task is to perform the following actions: 

1. Pair the examiner's questions with the corresponding student's responses.
2. As an AI examiner, similar to an IELTS professional, evaluate the student's answers in terms of "fluency and coherence", "lexical resource", "grammatical range and accuracy", and "pronunciation". Assign scores on a scale from 0 to 9 for each criterion, as per the IELTS scoring guidelines.
3. Compile the IELTS scores, examiner's questions, student's responses into a JSON object. Use the following structure for the JSON object:
'''
{json_example}
'''
Additionally, please remove unnecessary whitespace and line breaks from the JSON object as JSON does not require formatting with indentation and line breaks.

Examiner's questions:
'''
{questions}
'''

Student's answers:
'''
{answers}
'''
"""
        self.get_response(system, prompt)

    def analyze_text_find_errors(self, text: str):
        system = "As an AI language model, your role is akin to Grammarly. Your key task is to scrutinize text data for language errors including, but not limited to, spelling, grammar, punctuation, and word usage. Please respond in JSON format, using <err></err> tags to highlight the errors in the original text."

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
4. Assemble the analysed text, tagged errors, and their explanations into a JSON object.


The JSON object should resemble the following example:
'''
{json_example_prompt}
'''

Please analyze the text below:
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

        text_example_2 = "I from Russia. Is very big country. Have lot of cities. I lives in capital, Moscow. Is big and crowded city."
        json_answer_example_2 = """
{
	"text": "I <err>from</err> Russia. Is <err>very</err> big country. Have <err>lot</err> of cities. I <err>lives</err> in <err>capital</err>, Moscow. Is <err>big</err> and crowded city.",
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

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": json_answer_example},
            {"role": "user", "content": text_example_2},
            {"role": "assistant", "content": json_answer_example_2},
            {"role": "user", "content": text},
        ]

        self.get_response(messages)

    def analyze_texts(self, texts: list):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(self.analyze_text_find_errors, texts)


sentences = [
    "He don't knows how to cook, so he always eat out or orders takeout.",
    "We was suppose to meet at the café, but I forgot the time and missed are appointment.",
    "She seen the movie last night and she said it was the best she ever watched.",
    "They don't wants to go on vacation because they thinks it's a waste of moneys.",
    "I was talking to my friend on the phone when suddenly the call gets dropped.",
    "He don't have no clue about the latest fashion trends, so he always wear outdated clothes.",
    "We was walking in the park when we seen a squirrels chasing its tails.",
    "She don't likes to read books because she finds them boring and a waste of times.",
    "They was arguing all nights and it was driving me crazies.",
    "I don't got no ideas how to fix a leaky faucet, so I'll have to call a plumbers."
]

chat_gpt = ChatGPT()
chat_gpt.analyze_texts(sentences)
