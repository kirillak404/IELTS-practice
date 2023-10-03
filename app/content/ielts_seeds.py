SECTIONS = [
    {"name": "Listening",
     "description": "IELTS Listening is a section of the IELTS exam that assesses your ability to comprehend spoken English through various recordings."},

    {"name": "Reading",
     "description": "IELTS Reading is a section of the IELTS exam that evaluates your reading comprehension skills by presenting different passages and accompanying questions."},

    {"name": "Writing",
     "description": "IELTS Writing is a section of the IELTS exam that assesses your English writing skills through specific tasks such as report writing or graph description."},

    {"name": "Speaking",
     "description": "The IELTS Speaking test evaluates your English oral skills"}
]

SUBSECTIONS = [
    {"name": "Introduction and Interview",
     "part_number": 1,
     "description": "Answer general questions about yourself and various familiar topics",
     "time_limit_minutes": 5,
     "section": "Speaking"},

    {"name": "Individual Long Turn",
     "part_number": 2,
     "description": "Discuss a specific topic presented on a cue card",
     "time_limit_minutes": 4,
     "section": "Speaking"},

    {"name": "Two-way Discussion",
     "part_number": 3,
     "description": "Engage in a deeper, more abstract discussion on the topic from Part 2",
     "time_limit_minutes": 5,
     "section": "Speaking"}
]

QUESTIONS = [
    {"subsection": "Introduction and Interview",
     "questions": [
         "Can you tell me a bit about your hometown?",
         "What do you enjoy doing in your free time?",
         "Do you work or are you a student?",
         "Describe the kind of place where you live. What do you like about it?",
         "What is your favorite season, and why?",
         "How often do you use public transportation?",
         "Do you prefer spending time with friends or spending time alone?"
     ]},

    {"subsection": "Introduction and Interview",
     "questions": [
         "Can you describe the area where you grew up?",
         "Do you often cook at home or prefer eating out?",
         "Tell me about your studies or your current job.",
         "What aspects of your subject or job are most interesting to you?",
         "How important is exercise to you?",
         "What was the last book you read? Did you enjoy it?",
         "Do you believe technological advancements always have positive impacts on society?"
     ]},

    {"subsection": "Introduction and Interview",
     "questions": [
         "Could you tell me about your family?",
         "How often do you see your relatives?",
         "Can you describe your daily routine?",
         "How has your routine changed over the past few years?",
         "What traditional dish from your country do you like the most?",
         "How do people in your country celebrate major festivals or events?",
         "What is your opinion on learning foreign languages?"
     ]},

    {"subsection": "Introduction and Interview",
     "questions": [
         "Could you describe your best friend to me?",
         "How do you usually spend weekends?",
         "How would you describe your ideal vacation?",
         "Do you think tourism impacts the environment of a place?",
         "How significant do you think the role of the internet is in our lives?",
         "Have you ever tried learning something through online platforms?",
         "How does social media influence relationships among people in your opinion?"
     ]},

    {"subsection": "Introduction and Interview",
     "questions": [
         "What type of movies or series do you enjoy watching?",
         "Is there a type of movie that you prefer to watch at the cinema rather than at home?",
         "Can you describe a memorable event from your childhood?",
         "Do you think children’s activities today are different from those in the past?",
         "How often do you participate in outdoor activities?",
         "In your opinion, how has technology influenced entertainment?",
         "Should governments invest more in public or private transportation, in your opinion?"
     ]},

    {"subsection": "Introduction and Interview",
     "questions": [
         "How do you usually celebrate your birthday?",
         "Do you have a hobby or activity you like to do in your spare time?",
         "What type of shops do you usually visit?",
         "How do you feel about online shopping vs. in-store shopping?",
         "Can you tell me about a traditional game or sport in your country?",
         "Do you think it’s essential for children to play outdoor games?",
         "What are your thoughts on the importance of historical landmarks and museums in education?"
     ]},

    {"subsection": "Introduction and Interview",
     "questions": [
         "Can you describe your favourite place in your city?",
         "What is a popular festival or event in your country?",
         "How do you usually keep in touch with your friends?",
         "Can you tell me about a time when you helped someone?",
         "How does the weather affect your daily activities?",
         "What is your opinion on keeping pets?",
         "How do you think climate change is impacting your country?"
     ]},

    {"subsection": "Introduction and Interview",
     "questions": [
         "What is a common means of transportation in your city?",
         "Do you like travelling to different places?",
         "What kind of art or exhibitions have you seen recently?",
         "How often do you visit museums or galleries?",
         "Do you think it’s beneficial for students to travel abroad for their studies?",
         "In what ways do you think travel broadens the mind?",
         "How does the education system in your country address global issues?"
     ]},

    {"subsection": "Introduction and Interview",
     "questions": [
         "Do you enjoy listening to music while working or studying?",
         "How do you usually keep yourself fit and healthy?",
         "Can you tell me about a recent trip you went on?",
         "How have your travelling habits changed over time?",
         "In what ways do you think cities can become more eco-friendly?",
         "How often do you interact with nature and green spaces?",
         "What role do you think individuals should play in protecting the environment?"
     ]},

    {"subsection": "Introduction and Interview",
     "questions": [
         "How do you feel about spending time in nature?",
         "What is your favourite way to stay informed about current events?",
         "Are there any traditional dances in your country?",
         "What kind of role does traditional music play in your culture?",
         "How do you think technology will impact our lives in the future?",
         "What are the advantages and disadvantages of working from home?",
         "How do you think advancements in AI might affect job opportunities?"
     ]}
]

TOPICS = [
    {"subsection": "Individual Long Turn",
     "name": "Remote Work",
     "description": "Describe your experience (or someone you know) with working or studying remotely.",
     "general_questions": [
         "When this was",
         "Where you were working or studying from",
         "What challenges you faced, and",
         "Describe how you adapted to this situation."
     ],
     "discussion_questions": [
         "What do you think are the main challenges people face when working or studying remotely?",
         "How has remote work changed the professional environment?",
         "In your opinion, how does remote learning affect students' academic and social development?",
         "Do you think remote work and learning will continue to be popular in the future?"
     ]},

    {"subsection": "Individual Long Turn",
     "name": "Environment Protection",
     "description": "Describe an experience or an event that made you more aware of environmental issues.",
     "general_questions": [
         "When and where it happened",
         "What issue it related to",
         "How it changed your perspective, and",
         "Explain what actions you took (if any) after becoming more aware."
     ],
     "discussion_questions": [
         "How can awareness about environmental issues be increased among people?",
         "What role do individuals and governments play in protecting the environment?",
         "Do you think global cooperation is important to solve environmental problems?",
         "How can companies be encouraged to adopt more sustainable practices?"
     ]},

    {"subsection": "Individual Long Turn",
     "name": "Learning a New Skill",
     "description": "Describe a time when you tried to learn a new skill.",
     "general_questions": [
         "What the skill was",
         "Why you decided to learn it",
         "What the learning process was like, and",
         "Explain any challenges you faced and how you overcame them."
     ],
     "discussion_questions": [
         "Why do you think people decide to learn new skills?",
         "How have opportunities for learning new skills changed over the last few decades?",
         "Do you believe technological advancements make it easier or harder for people to pick up new skills?",
         "What role does lifelong learning play in a person’s career and personal development?"
     ]},

    {"subsection": "Individual Long Turn",
     "name": "Digital Privacy",
     "description": "Describe a situation where you were concerned about your digital privacy.",
     "general_questions": [
         "When this was",
         "What caused your concern",
         "What actions you took, and",
         "Explain why digital privacy is important to you."
     ],
     "discussion_questions": [
         "How can people protect their digital privacy?",
         "What role should governments play in protecting citizens’ digital privacy?",
         "Do you think people are generally aware of their digital rights?",
         "How do digital privacy concerns impact online behavior?"
     ]},

    {"subsection": "Individual Long Turn",
     "name": "Healthy Lifestyle",
     "description": "Describe a change you have made to lead a healthier lifestyle.",
     "general_questions": [
         "What the change was",
         "Why you decided to make this change",
         "How you implemented it, and",
         "Explain the impact it has had on your life."
     ],
     "discussion_questions": [
         "Why is maintaining a healthy lifestyle important?",
         "How can governments promote healthy living among their citizens?",
         "What are the obstacles people face when trying to live healthily?",
         "How has the perception of a healthy lifestyle changed over the years?"
     ]},

    {"subsection": "Individual Long Turn",
     "name": "Urbanization",
     "description": "Describe a city you have visited that has been significantly affected by urbanization.",
     "general_questions": [
         "When you visited",
         "What changes you noticed",
         "How it differed from smaller towns or rural areas, and",
         "Explain your feelings about the urbanization of the city."
     ],
     "discussion_questions": [
         "What are the main challenges and benefits of urbanization?",
         "How does urbanization impact the environment?",
         "What can governments do to manage urbanization effectively?",
         "Do you think the urbanization of cities will continue at the current rate?"
     ]},

    {"subsection": "Individual Long Turn",
     "name": "Cultural Diversity",
     "description": "Describe an experience where you learned something important about a culture different from your own.",
     "general_questions": [
         "When and where this was",
         "What you learned",
         "How you learned it, and",
         "Explain why it was significant to you."
     ],
     "discussion_questions": [
         "Why is it important to understand different cultures?",
         "How does cultural diversity benefit a society?",
         "Do you think globalisation affects cultural diversity positively or negatively?",
         "How can people be encouraged to appreciate and participate in other cultural traditions?"
     ]},

    {"subsection": "Individual Long Turn",
     "name": "Artificial Intelligence",
     "description": "Describe an instance where you interacted with, or were affected by, artificial intelligence.",
     "general_questions": [
         "When this was",
         "What the situation was",
         "How you interacted with the artificial intelligence, and",
         "Explain how it influenced your actions or decisions."
     ],
     "discussion_questions": [
         "How do you feel about the increasing use of artificial intelligence in daily life?",
         "What are some potential drawbacks of relying heavily on artificial intelligence?",
         "Do you think artificial intelligence will ever replace certain human roles completely?",
         "How can we ensure that the use of artificial intelligence is ethical and fair?"
     ]},

    {"subsection": "Individual Long Turn",
     "name": "Online Shopping",
     "description": "Describe an experience you had with online shopping.",
     "general_questions": [
         "When this was",
         "What you bought",
         "Why you chose to shop online, and",
         "Explain how satisfied you were with the experience."
     ],
     "discussion_questions": [
         "What do you think are the advantages and disadvantages of online shopping?",
         "How has online shopping changed retail business?",
         "Do you think online shopping will completely replace traditional shopping in the future?",
         "How can online shopping platforms improve the customer experience?"
     ]},

    {"subsection": "Individual Long Turn",
     "name": "Attitude towards Online Gaming",
     "description": "Describe your attitude towards online gaming.",
     "general_questions": [
         "Whether you play online games",
         "What kind of online games you play or avoid",
         "How much time you spend on them, and",
         "Explain why you have this attitude towards online gaming."
     ],
     "discussion_questions": [
         "What do you think are the social implications of online gaming?",
         "How can online gaming impact an individual’s physical and mental health?",
         "Do you believe that online gaming can be used for educational purposes?",
         "How do you see the future development of the online gaming industry?",
         "Do you think online gaming should be regulated more strictly?"
     ]}
]
