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

        system = """You are an artificial intelligence that strictly follows the given instructions and responds only in JSON format."""

        # creating prompt and first example of GPT response
        questions_example_prompt = json.dumps([
            "What is your full name?",
            "Can you tell me where you are from?",
            "Do you work or are you a student?",
            "What do you enjoy doing in your free time?",
            "How often do you exercise?",
            "What is your favorite type of music?",
            "Tell me about your favorite book or movie.",
            "Do you prefer spending time with friends or alone?",
            "What kind of food do you like?",
            "Describe your favorite holiday or celebration."])
        answers_example_prompt = "My full name is John Smith. I am from London, England. I am currently a student. In my free time, I enjoy reading and playing the guitar. I try to exercise at least three times a week. My favorite type of music is rock. One of my favorite books is 'To Kill a Mockingbird' by Harper Lee. It's a powerful story about justice and equality. I enjoy spending time with both friends and alone, but sometimes I prefer to have some quiet time to myself. I love Italian cuisine, especially pasta and pizza. My favorite holiday is Christmas. I love the festive atmosphere, spending time with family, and exchanging gifts."
        ai_response_example_prompt = json.dumps([
            "My full name is John Smith.",
            "I am from London, England.",
            "I am currently a student.",
            "In my free time, I enjoy reading and playing the guitar.",
            "I try to exercise at least three times a week.",
            "My favorite type of music is rock.",
            "One of my favorite books is 'To Kill a Mockingbird' by Harper Lee. It's a powerful story about justice and equality.",
            "I enjoy spending time with both friends and alone, but sometimes I prefer to have some quiet time to myself.",
            "I love Italian cuisine, especially pasta and pizza.",
            "My favorite holiday is Christmas. I love the festive atmosphere, spending time with family, and exchanging gifts."])
        prompt = f"""
Your task is to match each question in the provided 'Questions' list with its corresponding answer from the 'Answers' text, and then generate a JSON-formatted output. This output should be a list of answers that directly corresponds to the order of the questions. If an answer can't be found for a specific question, substitute with the string "No answer".

Inputs:

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
            "What is your favorite type of food and why?",
            "Tell me about a memorable trip you have taken.",
            "Do you prefer living in a city or in the countryside?",
            "What is your favorite season and why?",
            "How do you usually spend your weekends?",
            "What is your favorite sport and why?",
            "Tell me about a hobby or activity you enjoy.",
            "Do you prefer watching movies at home or in the cinema?",
            "What is your favorite subject in school and why?",
            "Describe a person who has had a great influence on you."])
        answer_example_2 = "My favorite type of food is sushi because I love the combination of flavors and freshness of the ingredients. One memorable trip I took was to the Grand Canyon. The breathtaking views and the sense of wonder it evoked left a lasting impression on me. I prefer living in the countryside because I enjoy the peace and quiet, being close to nature, and having more space. On weekends, I usually spend time with family and friends, go for walks in the park, or relax at home with a good book or movie. My favorite sport is basketball because I enjoy the fast-paced nature of the game and the teamwork involved. I enjoy photography as a hobby. Capturing moments and exploring different perspectives through my camera brings me joy. My favorite subject in school is history because I find it fascinating to learn about past events, cultures, and how they have shaped the world. One person who has had a great influence on me is my grandfather. His wisdom, kindness, and work ethic inspire me to be a better person."
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
            "My favorite type of food is sushi because I love the combination of flavors and freshness of the ingredients.",
            "One memorable trip I took was to the Grand Canyon. The breathtaking views and the sense of wonder it evoked left a lasting impression on me.",
            "I prefer living in the countryside because I enjoy the peace and quiet, being close to nature, and having more space.",
            "No answer",
            "On weekends, I usually spend time with family and friends, go for walks in the park, or relax at home with a good book or movie.",
            "My favorite sport is basketball because I enjoy the fast-paced nature of the game and the teamwork involved.",
            "I enjoy photography as a hobby. Capturing moments and exploring different perspectives through my camera brings me joy.",
            "No answer",
            "My favorite subject in school is history because I find it fascinating to learn about past events, cultures, and how they have shaped the world.",
            "One person who has had a great influence on me is my grandfather. His wisdom, kindness, and work ethic inspire me to be a better person."])

        # creating final prompt with real data
        real_prompt = f"""     
Questions:
'''
{json.dumps(questions)}
'''

Answers:
'''
{answers}  

Your response should contain only a JSON object with no additional text or other information.
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


ielts_questions = [
    "What is your favorite type of weather and why?",
    "Tell me about a skill you would like to learn in the future.",
    "Do you prefer reading books or watching movies?",
    "What is your favorite way to relax and unwind?",
    "How do you usually celebrate your birthday?",
    "What is your favorite animal and why?",
    "Tell me about a time when you had to overcome a difficult challenge.",
    "Do you prefer working alone or in a team?",
    "What is your favorite type of art (painting, sculpture, etc.)?",
    "Describe a place you would like to visit in the future."
]


# ielts_answers = """My favorite type of weather is sunny with a gentle breeze. It makes me feel energized and uplifted. \
# One skill I would like to learn in the future is playing the guitar. I am always fascinated by the beautiful melodies created by this instrument. \
# I enjoy both reading books and watching movies, but if I had to choose, I would say I prefer reading books because they allow me to use my imagination. \
# My favorite way to relax and unwind is by taking long walks in nature. The fresh air and peaceful surroundings help clear my mind and reduce stress. \
# I usually celebrate my birthday by gathering with my close friends and family for a small party. We have a delicious meal together and enjoy each other's company. \
# My favorite animal is the dolphin because of its intelligence, gracefulness, and playful nature. \
# One time I had to overcome a difficult challenge was when I had to give a presentation in front of a large audience. With preparation and practice, I managed to deliver a successful presentation. \
# I enjoy working both alone and in a team, but I find that collaboration in a team often brings fresh perspectives and encourages creativity. \
# My favorite type of art is painting. I am fascinated by the use of colors, textures, and brushstrokes to create meaningful and visually appealing artworks. \
# A place I would like to visit in the future is the Maldives. The pristine beaches, crystal-clear waters, and stunning coral reefs make it a dream destination for relaxation and diving.
# """

ielts_answers = """
My favorite type of weather is sunny with a gentle breeze. It makes me feel energized and uplifted. \
One skill I would like to learn in the future is playing the guitar. I am always fascinated by the beautiful melodies created by this instrument. \
My favorite way to relax and unwind is by taking long walks in nature. The fresh air and peaceful surroundings help clear my mind and reduce stress. \
I usually celebrate my birthday by gathering with my close friends and family for a small party. We have a delicious meal together and enjoy each other's company. \
My favorite animal is the dolphin because of its intelligence, gracefulness, and playful nature. \
One time I had to overcome a difficult challenge was when I had to give a presentation in front of a large audience. With preparation and practice, I managed to deliver a successful presentation. \
A place I would like to visit in the future is the Maldives. The pristine beaches, crystal-clear waters, and stunning coral reefs make it a dream destination for relaxation and diving.
"""


chat_gpt = ChatGPT()
answers_list = chat_gpt.match_questions_answers(ielts_questions, ielts_answers)

print(answers_list)
print()
for n, answer in enumerate(answers_list, start=1):
    print(f"{n}. {answer}")
