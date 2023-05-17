SECTIONS = [
    {"name": "Listening",
     "description": "IELTS Listening is a section of the IELTS exam that assesses your ability to comprehend spoken English through various recordings."},

    {"name": "Reading",
     "description": "IELTS Reading is a section of the IELTS exam that evaluates your reading comprehension skills by presenting different passages and accompanying questions."},

    {"name": "Writing",
     "description": "IELTS Writing is a section of the IELTS exam that assesses your English writing skills through specific tasks such as report writing or graph description."},

    {"name": "Speaking",
     "description": "IELTS Speaking is a section of the IELTS exam that assesses your oral communication skills in English."}
]

SUBSECTIONS = [
    {"name": "Introduction and Interview",
     "part_number": 1,
     "description": "The examiner asks questions about yourself, family, work/study, hobbies, etc.",
     "approx_time": "4-5 minutes",
     "section": "Speaking"},

    {"name": "Individual Long Turn",
     "part_number": 2,
     "description": "You are given a topic, prepare for 1-2 minutes, and speak for 1-2 minutes on the topic",
     "approx_time": "3-4 minutes",
     "section": "Speaking"},

    {"name": "Two-way Discussion",
     "part_number": 3,
     "description": "The examiner asks broader questions related to the topic in Part 2, and you discuss and express your opinions",
     "approx_time": "4-5 minutes",
     "section": "Speaking"}
]

QUESTIONS = [
    {"subsection": "Introduction and Interview",
     "questions": [
         "Can you tell me your full name, please?",
         "Can you tell me where you're from?",
         "Can you describe your hometown a bit?",
         "What do you like most about your hometown?",
         "Do you work or are you a student?",
         "What subject are you studying?",
         "Why did you choose this subject?",
         "Do you enjoy your work/studies? Why or why not?",
         "What do you like to do in your free time?"
     ]},

    {"subsection": "Introduction and Interview",
     "questions": [
         "Can you tell me your full name, please?",
         "What should I call you?",
         "Can you tell me where you're from?",
         "Do you work or study?",
         "What do you do at your job?",
         "Let's talk about your hometown or city. What do you like most about it?",
         "How have the places you've lived influenced you?"
     ]}
]

TOPICS = [
    {"subsection": "Individual Long Turn",
     "text": "Describe a time you had to make a difficult decision.",
     "questions": [
         "When this was",
         "What the decision was",
         "What you had to consider, and",
         "Explain why it was a difficult decision."
     ],
     "discussion_questions": [
         "Do you think decision making becomes easier as people get older?",
         "In your culture, who usually makes the important decisions in the family?",
         "How can people improve their decision-making skills?",
         "Do you think it's always good to take your time when making decisions?"
     ]},

    {"subsection": "Individual Long Turn",
     "text": "I'd like you to describe a memorable event that happened in your life.",
     "questions": [
         "What the event was",
         "Where it happened",
         "Who was with you",
         "And explain why it was memorable"
     ],
     "discussion_questions": [
         "Why do you think some events are more memorable than others?",
         "How do people in your country celebrate special events?",
         "Do you think people have too many celebrations these days? Why?",
         "How might celebrations change in the future?",
         "How important is it to mark events and milestones?"
     ]}
]
