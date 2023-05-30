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

json_format = """{"Fluency_and_Coherence":"<Fluency and Coherence Score (int)>","Lexical_Resource":"<Lexical Resource Score (int)>","Grammatical_Range_and_Accuracy":"<Grammatical Range and Accuracy Score (int)>","Pronunciation":"<Pronunciation Score (int)>","QuestionAnswerPairs":[{"Question":"<Text of the examiner's question>","Answer":{"Content":"<Original response provided by the student>","Mistakes":[{"Type":"<Category or type of the mistake: 'Spelling', 'Grammar', 'Punctuation', 'Verb form', 'Subject-verb agreement', 'Preposition', etc.>","IncorrectText":"<Exact segment from the original response that is incorrect>","CorrectText":"<Corrected version of the 'IncorrectText'>","Explanation":"<Brief explanation of the mistake and the correction>"}]}}]}"""
json_example = '''{"Fluency_and_Coherence":6,"Lexical_Resource":6,"Grammatical_Range_and_Accuracy":5,"Pronunciation":7,"QuestionAnswerPairs":[{"Question":"What is your favorite hobby?","Answer":{"Content":"My favorite hobby is play football. I like to play it with my friends every weekend.","Mistakes":[{"Type":"Verb form","IncorrectText":"play","CorrectText":"playing","Explanation":"After the verb 'is', we need to use the gerund form of the verb, which is 'playing' in this case."}]}},{"Question":"Do you prefer living in a city or in the countryside?","Answer":{"Content":"I prefer living in a city because there are more opportunities for work and have many entertainments.","Mistakes":[{"Type":"Subject-verb agreement","IncorrectText":"have","CorrectText":"it has","Explanation":"The city is referred to as 'it'. So, we need to use 'it has' instead of 'have'."},{"Type":"Noun form","IncorrectText":"entertainments","CorrectText":"entertainment","Explanation":"'Entertainment' is uncountable in English and it's incorrect to use it in the plural form."}]}},{"Question":"How often do you exercise?","Answer":{"Content":"I don't exercise often. Sometimes I go to the gym, but most of the time I'm too busy with my work.","Mistakes":[]}},{"Question":"What kind of music do you like?","Answer":{"Content":"I like listen to rock music. It makes me feel relax and it have a lot of energy.","Mistakes":[{"Type":"Verb form","IncorrectText":"like listen","CorrectText":"like listening","Explanation":"After 'like', the verb should be in gerund form, so 'listen' should be 'listening'."},{"Type":"Verb form","IncorrectText":"relax","CorrectText":"relaxed","Explanation":"In this context, the verb 'feel' should be followed by an adjective. The correct adjective form is 'relaxed'."},{"Type":"Subject-verb agreement","IncorrectText":"it have","CorrectText":"it has","Explanation":"The subject 'it' (referring to rock music) is singular, so the verb should be 'has' instead of 'have'."}]}},{"Question":"How often do you eat fast food?","Answer":{"Content":"I eat fast food very often. It's cheap and easy for me, and I don't have much time to cook.","Mistakes":[]}},{"Question":"What is your favorite season?","Answer":{"Content":"My favorite season is spring because the weather is not too hot or cold, and the flowers blossoms.","Mistakes":[{"Type":"Verb form","IncorrectText":"blossoms","CorrectText":"blossom","Explanation":"In this context, 'blossoms' should be used as a verb in the present tense, not as a noun or a third-person singular verb. Therefore, it should be 'blossom'."}]}},{"Question":"How often do you go to the cinema?","Answer":{"Content":"I don't go to the cinema often. Tickets are very expensive and I can watch movies at home.","Mistakes":[]}},{"Question":"What is your favorite book?","Answer":{"Content":"My favorite book is \"Pride and Prejudice\" by Jane Austin. It's a very interesting story about love and romance.","Mistakes":[{"Type":"Spelling","IncorrectText":"Jane Austin","CorrectText":"Jane Austen","Explanation":"The correct spelling of the author's name is 'Jane Austen'."}]}},{"Question":"How do you usually spend your weekends?","Answer":{"Content":"I usually spend my weekends sleep late and hang out with my friends. We go to shopping or watch a movie.","Mistakes":[{"Type":"Verb form","IncorrectText":"sleep","CorrectText":"sleeping","Explanation":"The verb after 'spend' should be in the gerund form, so 'sleep' should be 'sleeping'."},{"Type":"Preposition","IncorrectText":"go to shopping","CorrectText":"go shopping","Explanation":"The correct expression is 'go shopping', not 'go to shopping'."}]}},{"Question":"What is your favorite food?","Answer":{"Content":"My favorite food is pizza. It's delicious and I like the taste of cheese and toppings.","Mistakes":[]}}]}'''


class IELTSExaminer:
    def __init__(self, model="gpt-3.5-turbo"):  # gpt-4 | gpt-3.5-turbo
        self.about = "You are a professional IELTS Examiner."
        self.model = model

    # TODO move to utils
    @staticmethod
    def convert_list_to_string(string_list: list) -> str:
        return "\n".join(f"{s[0]}. {s[1]}" for s in enumerate(string_list,
                                                              start=1))

    def evaluate_speaking(self, questions, answers):
        questions = IELTSExaminer.convert_list_to_string(questions)
        prompt = f"""
Your task encompasses the following instructions:

1. Match the examiner's questions with the corresponding student's answers.
2. Carefully analyze the student's answers and identify ALL grammatical \
errors in them. For each error, suggest the correct option \
and provide a brief description of the mistake.
3. Assign scores ranging from 0 to 9 based on the standard \
IELTS Speaking Part 1 criteria: Fluency and Coherence, \
Lexical Resource, Grammatical Range and Accuracy, Pronunciation.
4. Output a JSON object that includes the scores, examiner's questions, \
student's responses, and the student's mistakes, following this format:

Json output example:
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
        for _ in range(10):
            try:
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
                print(e.error['message'])
                time.sleep(1)
            except json.decoder.JSONDecodeError as e:
                print(result)
                print("JSON decoding error, message::", str(e))
            else:
                print(result_json)
                break


# examiner = IELTSExaminer()
# examiner.evaluate_speaking(questions, answers)
