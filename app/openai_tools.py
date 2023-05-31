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

    def get_response(self, messages: list) -> dict:
        gpt_response_dict = None
        start = time.time()
        for _ in range(10):
            try:
                completion = openai.ChatCompletion.create(
                    model=self.model,
                    messages=messages,
                    top_p=0.1
                )
                gpt_response_json_string = completion.choices[0].message["content"]
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

    def evaluate_speaking(self, questions: list, answers: str):
        system = "You are an AI functioning as a professional IELTS examiner. Your output will consist solely of a JSON object, without any additional text."
        json_example = '''
{
	"fluency_and_coherence": 5,
	"lexical_resource": 6,
	"grammatical_range_and_accuracy": 4,
	"pronunciation": 5,
	"data": [{
		"q": "Can you tell me a little about yourself?",
		"a": "I lives in Moscow. I has a big family. They is very kind and smart."
	}, {
		"q": "Where are you from?",
		"a": "I from Indonesia. Is very big country."
	}]
}
'''
        questions = convert_list_to_string(questions)
        prompt = f"""
Your task is to perform the following actions: 

1. Pair the examiner's questions with the corresponding student's responses. Do not make any changes to the texts.
2. As an AI examiner, similar to an IELTS professional, evaluate the student's answers in terms of "fluency and coherence", "lexical resource", "grammatical range and accuracy", and "pronunciation". Assign scores on a scale from 0 to 9 for each criterion, as per the IELTS scoring guidelines.
3. Compile the IELTS scores, examiner's questions, unmodified student's responses into a JSON object. Use the following structure for the JSON object:
'''
{json_example}
'''

Examiner's questions:
'''
{questions}
'''

Student's answers:
'''
{answers}
'''
"""

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ]

        speaking = self.get_response(messages)
        answers = [pair['a'] for pair in speaking['data']]
        for a in answers:
            print(a)

        answers = self.check_multiple_texts_for_errors(answers)
        for a in answers:
            print(a)

    def find_errors_in_text(self, text: str):
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

        text_example_2 = "My favorite hobby is playing football. I like to play football every weekend with my friends. It's very fun and keeps me active."
        json_answer_example_2 = """
{
	"text": "My favorite hobby is playing football. I like to play football every weekend with my friends. It's very fun and keeps me active.",
	"errors": []
}
        """

        text_example_3 = "I from Indonesia. Is very big country. Have lot of cities. I lives in capital, Moscow. Is big and crowded city."
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

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": json_answer_example},
            {"role": "user", "content": text_example_2},
            {"role": "assistant", "content": json_answer_example_2},
            {"role": "user", "content": text_example_3},
            {"role": "assistant", "content": json_answer_example_3},
            {"role": "user", "content": text}
        ]

        return self.get_response(messages)

    def check_multiple_texts_for_errors(self, texts: list) -> list:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            result = list(executor.map(self.find_errors_in_text, texts))
        return result


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

# chat_gpt = ChatGPT()
# chat_gpt.evaluate_speaking(questions, answers)
# chat_gpt.analyze_multiple_texts(sentences)