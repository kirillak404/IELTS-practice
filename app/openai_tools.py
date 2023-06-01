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

    def match_questions_answers(self, questions: list, answers: str):

        system = """You are an artificial intelligence that strictly follows the instructions given and cannot deviate from them."""

        # creating prompt and first example of GPT response
        questions_example_prompt = json.dumps([
            "What is your favorite childhood memory?",
            "How do you envision your life in 10 years?",
            "What is the most challenging experience you've faced?",
            "If you could travel anywhere in the world, where would you go?",
            "What is your favorite book and why?"])
        answers_example_prompt = "My favorite childhood memory is when me and my friend go to the beach and we build sand castles. In 10 years, I envision myself living in a big house with a successful career. The most challenging experience I've faced was when I had to give a presentation in front of a large audience. If I could travel anywhere in the world, I would go to Paris because of its rich history and beautiful landmarks. My favorite book is 'Harry Potter' because it takes me to a magical world full of adventure and friendship."
        ai_response_example_prompt = json.dumps([
            "My favorite childhood memory is when me and my friend go to the beach and we build sand castles.",
            "In 10 years, I envision myself living in a big house with a successful career.",
            "The most challenging experience I've faced was when I had to give a presentation in front of a large audience.",
            "If I could travel anywhere in the world, I would go to Paris because of its rich history and beautiful landmarks.",
            "My favorite book is 'Harry Potter' because it takes me to a magical world full of adventure and friendship."])
        prompt = f"""
I have a list of questions and a string with a series of answers. I need you to match each question with its corresponding answer from the string and produce a JSON output. 

Please strictly adhere to the following rules:
1. The number of answers in the JSON output must strictly match the number of questions asked.
2. If there is no answer to a question in the answer string, represent the answer in the JSON as an empty string ("").
3. The order of the answers in the JSON should match the order in which the questions were asked.
4. The output of this task should be strictly the JSON format, with no additional text or information. You should only include the exact text from the answers, and if there was no answer for a question, strictly include an empty string ("").
5. Check that the JSON output contains only answers from the Answer String and no other information. If any other information is included, make the corresponding answer an empty string ("").

Questions:
'''
{questions_example_prompt}
'''

Answers:
'''
{answers_example_prompt}      
'''
"""

        # creating second example for GPT
        questions_example_2 = json.dumps([
            "What is your favorite hobby and why?",
            "If you could have any superpower, what would it be and why?",
            "Tell me about a memorable trip or vacation you have taken.",
            "What is your favorite cuisine and why?",
            "If you could meet any historical figure, who would it be and why?"])
        answer_example_2 = "My favorite hobby is painting because it allows me to express my creativity and relax. If I could meet any historical figure, it would be Albert Einstein. His contributions to science and his revolutionary ideas continue to inspire and fascinate me."
        prompt_example_2 = f"""
Questions:
'''
{questions_example_2}
'''

Answers:
'''
{answer_example_2}      
'''
"""
        ai_response_example_2 = json.dumps([
            "My favorite hobby is painting because it allows me to express my creativity and relax.",
            "",
            "",
            "",
            "If I could meet any historical figure, it would be Albert Einstein. His contributions to science and his revolutionary ideas continue to inspire and fascinate me."])

        # creating final prompt with real data
        real_prompt = f"""     
Questions:
'''
{json.dumps(questions)}
'''

Answers:
'''
{answers}      
'''
        """

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": ai_response_example_prompt},

            {"role": "user", "content": prompt_example_2},
            {"role": "assistant", "content": ai_response_example_2},

            {"role": "user", "content": real_prompt}
        ]

        return self.get_completion(messages)

    # TODO: separate func for pairing q/a and func for evaluating and recomendations
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

        speaking = self.get_completion(messages)
        answers = [pair['a'] for pair in speaking['data']]
        for a in answers:
            print(a)

        answers = self.check_multiple_texts_for_errors(answers)
        for a in answers:
            print(a)

    # TODO: it no errors, change gpt answer, return original string
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

        return self.get_completion(messages)

    def check_multiple_texts_for_errors(self, texts: list) -> list:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            result = list(executor.map(self.find_errors_in_text, texts))
        return result


new_questions = [
    "What you do yesterday?",
    "Why she don't likes the color blue?",
    "Where he goes for lunch every day?",
    "When they will be go to the concert?",
    "How much books you have in your collection?"
]

new_answers = "She don't likes the color blue because it make her feel sad. He goes to the restaurante near his office. They will be go to the concert next week. I have much books in my collection."



chat_gpt = ChatGPT()
answers_list = chat_gpt.match_questions_answers(new_questions, new_answers)

print(answers_list)
print()
for n, answer in enumerate(answers_list, start=1):
    print(f"{n}. {answer}")
