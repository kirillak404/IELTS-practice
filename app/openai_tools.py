import json
import time

import openai

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

    def get_response(self, system: str, prompt: str):
        start = time.time()

        for _ in range(10):
            try:
                completion = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt}
                    ]
                )
                result = completion.choices[0].message["content"]
                result_json = json.loads(result)
            except openai.error.APIError as e:
                print(e.error['message'])
                time.sleep(1)
            except json.decoder.JSONDecodeError as e:
                print("JSON decoding error, message::", str(e))
            else:
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

    def find_grammar_errors(self, texts: list):
        texts = json.dumps(texts)
        json_example = """{"data":[{"text":"I <err>from</err> Russia. Is <err>very</err> big country. Have <err>lot</err> of cities. I <err>lives</err> in <err>capital</err>, Moscow. Is <err>big</err> and crowded city.","errors":[{"err":"from","type":"grammar","desc":"It seems that you are missing a verb.","corr":"am from"},{"err":"very","type":"grammar","desc":"It seems that there is an article usage problem here.","corr":"a very"},{"err":"lot","type":"grammar","desc":"It appears that the phrase lot does not contain the correct article usage.","corr":"a lot"},{"err":"lives","type":"grammar","desc":"It appears that the subject pronoun I and the verb lives are not in agreement.","corr":"live"},{"err":"capital","type":"grammar","desc":"The noun phrase capital seems to be missing a determiner before it.","corr":"the capital"},{"err":"big","type":"grammar","desc":"It seems that there is an article usage problem here.","corr":"a big"}]},{"text":"I <err>likes</err> rock music. Sometimes, I <err>listens</err> to pop. I don't <err>enjoys</err> <err>classic</err> music. It is boring.","errors":[{"err":"likes","type":"grammar","desc":"It appears that the subject pronoun I and the verb likes are not in agreement.","corr":"like"},{"err":"listens","type":"grammar","desc":"It appears that the subject pronoun I and the verb listens are not in agreement.","corr":"listen"},{"err":"enjoys","type":"grammar","desc":"It appears that the verb enjoys is incorrectly used with the helping verb do.","corr":"enjoy"},{"err":"classic","type":"spelling","desc":"The word classic doesn’t seem to fit this context.","corr":"classical"}]}]}"""

        prompt = f"""
Your task is to perform the following actions:

1. Examine the following list of texts given in JSON format. Identify any spelling, grammar, punctuation, or word usage errors present in each text.
2. In each text, place <err> and </err> tags around the words or phrases where you find an error. This is an important step and must not be skipped. For example, if "I is happy" is the text, you should rewrite it as "I <err>is</err> happy" to indicate the error.
3. For each identified error, provide a detailed explanation. This should include the type of the error (spelling, grammar, punctuation, or word usage), a brief description explaining why it is considered an error, and the correct version of the word or phrase.
4. Compile all of the analyzed texts, the marked errors within the texts, and their descriptions into a JSON object.

Here is an example of a completed JSON object:
'''
{json_example}
'''

Please analyze the following list of texts provided in the JSON format below:
'''
{texts}
'''
"""
        system = "You are an AI language model similar to Grammarly. Your primary task is to analyze text data and identify any language errors present. This includes, but is not limited to, spelling, grammar, punctuation, and word usage errors. You must respond in a JSON format. The identified errors within the original text must be indicated with tags, like this: <err>error_here</err>. Your output should strictly adhere to this format."
        self.get_response(system, prompt)


answer_texts = ["I ain't got no time to waste on meaningless tasks.",
"The weather be so hot today, I can't even handle it.",
"She don't know nothing about cars, but she acts like she's an expert.",
"Me and my friends, we was hanging out at the mall and we saw this really cool band playing.",
"He don't want to go to the party 'cause he says it's gonna be boring.",
"They was talking all loud and stuff, disturbing everyone in the restaurant.",
"We was driving down the highway when we seen a huge accident.",
"My boss don't appreciate all the hard work I do for this company.",
"She ain't never been to Europe before, so she's really excited about the trip.",
"They don't got no idea what they're talking about, but they act like they're experts on the subject."]

# chat_gpt = ChatGPT()
# chat_gpt.evaluate_speaking(questions, answers)