import os
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
    "Can you tell me your full name, please?",
    "Where are you from?",
    "What do you do? Are you a student or do you work?",
    "Do you enjoy your job/studies? Why or why not?",
    "How often do you hang out with your friends?",
    "What do you usually do when you go out with friends?",
    "Are you more of an indoor person or an outdoor person?",
    "Do you prefer living in a city or in the countryside? Why?",
    "What kind of music do you enjoy listening to?",
    "Have you ever traveled abroad? Where did you go and what did you do there?"
]
answers = [
    "Me name is Alex Jhonson.",
    "I'm original from Moskow, Russia.",
    "I'm currently a student at the Univercity of Moskow.",
    "Yes, I do enjoy my study. I find my courses interesting and challenge.",
    "I try to hangout with my friends atleast once or twice a weak.",
    "When we go out, we usually go to a cafe or a restarant to have a meal together and chat.",
    "I'm more of a indoor person. I enjoy spend time in door, watching movies and reading books.",
    "I prefer live in a city because there is more opportunities for entertainment and carrer growth.",
    "I enjoy listen to a wide range of music genres, but my favorite is pop music.",
    "Yes, I have traveled abrod. Last year, I went to France and visited Pariz. I explore the famous landmarks and experienced the vibrant culture of the city."
]


class IELTSExaminer:
    def __init__(self, model="gpt-3.5-turbo"):  # alt "gpt-4"
        self.about = "You are a professional IELTS Examiner."
        self.model = model

    # TODO move to utils
    @staticmethod
    def convert_list_to_string(string_list: list) -> str:
        return "\n".join(f"{s[0]}. {s[1]}" for s in enumerate(string_list,
                                                              start=1))

    def evaluate_speaking(self, questions, answers):
        questions = IELTSExaminer.convert_list_to_string(questions)
        answers = IELTSExaminer.convert_list_to_string(answers)

        prompt = f'''
Your task is to evaluate the student's answers to IELTS Speaking Part 1: Introduction and Interview. 

You must give a grade of 0 to 9 for each of the criteria:
1. Fluency and Coherence
2. Lexical Resource
3. Grammatical Range and Accuracy
4. Pronunciation

These are the questions the student was asked:
###
{questions}
###

Here are the student's answers to these questions:
###
{answers}
###

Give a short answer with only a JSON string: 
{{"Fluency and Coherence": SCORE, "Lexical Resource": SCORE, "Grammatical 
Range and Accuracy": SCORE, "Pronunciation": SCORE}}
'''

        for _ in range(10):
            try:
                completion = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.about},
                        {"role": "user", "content": prompt}
                    ]
                )
            except openai.error.APIError as e:
                print(e.error['message'])
                time.sleep(1)
            else:
                break

        # TODO add exception handling (move to try block)
        result = json.loads(completion.choices[0].message["content"])
        print()
        print(result)
        print(type(result))


# examiner = IELTSExaminer()
# examiner.evaluate_speaking(questions, answers)


# value = '''{"Fluency and Coherence": 5, "Lexical Resource": 5,
# "Grammatical Range and Accuracy": 5, "Pronunciation": 5}
# '''
