import openai
import json
import time


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

# json_example = '''{"fluency_and_coherence":5,"lexical_resource":6,"grammatical_range_and_accuracy":4,"pronunciation":5,"data":[{"q":"Can you tell me a little about yourself?","a":"I <span class=\"err\" data-type=\"grammar\" data-expl=\"It appears that the form of the verb <b>have</b> does not work with <b>am</b> in this sentence.\" data-corr=\"have\">am have</span> a work in <span class=\"err\" data-type=\"grammar\" data-expl=\"The noun phrase <b>company</b> seems to be missing a determiner before it.\" data-corr=\"the company OR a company\">company</span>, it called \"TechNova\". I <span class=\"err\" data-type=\"grammar\" data-expl=\"It appears that the subject pronoun <b>I</b> and the verb <b>lives</b> are not in agreement.\" data-corr=\"live\">lives</span> in Moscow. I <span class=\"err\" data-type=\"grammar\" data-expl=\"It appears that the subject pronoun <b>I</b> and the verb <b>has</b> are not in agreement.\" data-corr=\"have\">has</span>\n a big family. They <span class=\"err\" data-type=\"grammar\" data-expl=\"It appears that the subject pronoun <b>They</b> and the verb <b>is</b> are not in agreement.\" data-corr=\"are\">is</span> very kind and smart."},{"q":"Where are you from?","a":"I <span class=\"err\" data-type=\"grammar\" data-expl=\"It seems that you are missing a verb.\" data-corr=\"am from\">from</span>\n Russia. Is <span class=\"err\" data-type=\"grammar\" data-expl=\"It seems that there is an article usage problem here.\" data-corr=\"a very\">very</span> big country. Have <span class=\"err\" data-type=\"grammar\" data-expl=\"It appears that the phrase <b>lot</b> does not contain the correct article usage.\" data-corr=\"a lot\">lot</span> of cities. I <span class=\"err\" data-type=\"grammar\" data-expl=\"It appears that the subject pronoun <b>I</b> and the verb <b>lives</b> are not in agreement.\" data-corr=\"live\">lives</span> in <span class=\"err\" data-type=\"grammar\" data-expl=\"The noun phrase <b>capital</b> seems to be missing a determiner before it.\" data-corr=\"the capital\">capital</span>, Moscow. Is <span class=\"err\" data-type=\"grammar\" data-expl=\"It seems that there is an article usage problem here.\" data-corr=\"a big\">big</span> and crowded city."},{"q":"What do you do in your spare time?","a":"In <span class=\"err\" data-type=\"grammar\" data-expl=\"It seems that there is a pronoun problem here.\" data-corr=\"my free\">free</span> time, I <span class=\"err\" data-type=\"grammar\" data-expl=\"It appears that the subject pronoun <b>I</b> and the verb <b>likes</b> are not in agreement.\" data-corr=\"like\">likes</span> <span class=\"err\" data-type=\"grammar\" data-expl=\"It appears that your sentence or clause uses an incorrect form of the verb <b>play</b>.\" data-corr=\"playing\">play</span> computer games, <span class=\"err\" data-type=\"grammar\" data-expl=\"It appears that your sentence or clause uses an incorrect form of the verb <b>read</b>.\" data-corr=\"reading\">read</span> books, <span class=\"err\" data-type=\"grammar\" data-expl=\"It seems that conjunction use may be incorrect here.\" data-corr=\"and sometimes\">sometimes</span> <span class=\"err\" data-type=\"grammar\" data-expl=\"It appears that your sentence or clause uses an incorrect form of the verb <b>goes</b>.\" data-corr=\"going\">goes</span> to <span class=\"err\" data-type=\"grammar\" data-expl=\"The noun phrase <b>cinema</b> seems to be missing a determiner before it.\" data-corr=\"the cinema\">cinema</span>\n. I enjoy <span class=\"err\" data-type=\"grammar\" data-expl=\"The verb <b>do</b> is usually in the gerund form when following the word <b>enjoy</b>.\" data-corr=\"doing\">do</span>\n these activities."},{"q":"What kind of food do you like?","a":"I very <span class=\"err\" data-type=\"grammar\" data-expl=\"It appears that the subject pronoun <b>I</b> and the verb <b>likes</b> are not in agreement.\" data-corr=\"like\">likes</span> eat pizza and pasta. Also, I <span class=\"err\" data-type=\"grammar\" data-expl=\"It appears that the subject pronoun <b>I</b> and the verb <b>enjoys</b> are not in agreement.\" data-corr=\"enjoy\">enjoys</span> sushi. I don't <span class=\"err\" data-type=\"grammar\" data-expl=\"It seems that the verb <b>likes</b> does not agree with the subject.\" data-corr=\"like\">likes</span> vegetables. They taste not good."},{"q":"Do you prefer the city or the countryside?","a":"I <span class=\"err\" data-type=\"grammar\" data-expl=\"It appears that the subject pronoun <b>I</b> and the verb <b>prefers</b> are not in agreement.\" data-corr=\"prefer\">prefers</span> <span class=\"err\" data-type=\"grammar\" data-expl=\"It seems that there is an article usage problem here.\" data-corr=\"the city\">city</span>. <span class=\"err\" data-type=\"grammar\" data-expl=\"It seems that there is an article usage problem here.\" data-corr=\"The city\">City</span> <span class=\"err\" data-type=\"grammar\" data-expl=\"The plural verb <b>have</b> does not appear to agree with the singular subject <b>City</b>.\" data-corr=\"has\">have</span> many things <span class=\"err\" data-type=\"grammar\" data-expl=\"It seems that preposition use may be incorrect here.\" data-corr=\"to\">for</span> do. In <span class=\"err\" data-type=\"grammar\" data-expl=\"The noun phrase <b>countryside</b> seems to be missing a determiner before it.\" data-corr=\"the countryside\">countryside</span>, there <span class=\"err\" data-type=\"grammar\" data-expl=\"It seems that you are missing a verb.\" data-corr=\"are not\">not</span> <span class=\"err\" data-type=\"grammar\" data-expl=\"It seems that quantifier use may be incorrect here.\" data-corr=\"many\">much</span> things <span class=\"err\" data-type=\"grammar\" data-expl=\"It seems that preposition use may be incorrect here.\" data-corr=\"to\">for</span> do."}]}'''
json_example = '''{"fluency_and_coherence":5,"lexical_resource":6,"grammatical_range_and_accuracy":4,"pronunciation":5,"data":[{"q":"Can you tell me a little about yourself?","a":"I lives in Moscow. I has a big family. They is very kind and smart."},{"q":"Where are you from?","a":"I from Russia. Is very big country."}]}'''


class IELTSExaminer:
    def __init__(self, model="gpt-3.5-turbo"):  # gpt-4 | gpt-3.5-turbo
        # self.about = "You are an AI evaluator and corrector. Your output should be a valid JSON object only, without any extra text."
        self.about = "You are an AI functioning as a professional IELTS examiner. Your output will consist solely of a JSON object, without any additional text."
        self.model = model

    @staticmethod
    def convert_list_to_string(string_list: list) -> str:
        return "\n".join(f"{s[0]}. {s[1]}" for s in enumerate(string_list,
                                                              start=1))

    def evaluate_speaking(self, questions, answers):
        questions = IELTSExaminer.convert_list_to_string(questions)
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
        for _ in range(10):
            try:
                start_time = time.perf_counter()
                completion = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.about},
                        {"role": "user", "content": prompt}
                    ]
                )
                result = completion.choices[0].message["content"]
                result_json = json.loads(result)
            except openai.error.APIError as e:

                end_time = time.perf_counter()
                execution_time = end_time - start_time
                print(f"Время выполнения: {execution_time} секунд")
                print(e.error['message'])

                time.sleep(1)
            except json.decoder.JSONDecodeError as e:

                end_time = time.perf_counter()
                execution_time = end_time - start_time
                print(f"Время выполнения: {execution_time} секунд")
                print(result)

                print("JSON decoding error, message::", str(e))
            else:

                end_time = time.perf_counter()
                execution_time = end_time - start_time
                print(f"Время выполнения: {execution_time} секунд")

                print(result_json)
                with open('gpt_response.json', "w") as file:
                    file.write(result)
                break

    def get_gpt_response(self, system, prompt):
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
                print(result_json)
                with open('gpt_response_check_answers.json', "w") as file:
                    file.write(result)
                break

    def find_grammar_errors(self):
        answers = """{"data":[{"text":"My favorite hobby is playing football. I likes to play football every weekend with my friends. It's very fun and keep me active."},{"text":"Yes, I enjoy cooking sometimes. I often cooks dinner for my family. My mother teach me some recipes and I tries to cook them. It's a good way to relax."},{"text":"I don't exercise very regular. I tries to go to the gym once a week, but sometimes I'm too busy and not have enough time. I know it's important to stay healthy, so I need to make more time for it."},{"text":"I likes all kinds of music. I listens to pop, rock, and sometimes classic music. Music helps me to relax and forget about problems. I usually listens to music when I am study or cleaning the house."},{"text":"My favorite season is summer. I likes the hot weather and go to the beach. I can swims in the ocean and gets a nice tan. Summer is the best time of the year for me."}]}"""
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
{answers}
'''
"""
        system = "You are an AI language model similar to Grammarly. Your primary task is to analyze text data and identify any language errors present. This includes, but is not limited to, spelling, grammar, punctuation, and word usage errors. You must respond in a JSON format. The identified errors within the original text must be indicated with tags, like this: <err>error_here</err>. Your output should strictly adhere to this format."
        self.get_gpt_response(system, prompt)


examiner = IELTSExaminer()
examiner.find_grammar_errors()