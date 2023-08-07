from datetime import datetime

from humanize import naturaltime


def convert_answer_object_to_html(answer):
    pronunciation_assessment_json = answer.pronunciation_assessment_json
    if not pronunciation_assessment_json:
        return "You didn't give an answer ❌"

    words = pronunciation_assessment_json["NBest"][0]["Words"]

    word_list = []
    for word in words:
        word_text = word["Word"]
        score = word.get("AccuracyScore")
        if score:
            score = int(score)

        if word["ErrorType"] == "Mispronunciation":
            word = f"""<span data-toggle="tooltip" title="Accuracy: {score}%" class="word_mispronunciation">{word_text}</span>"""
        elif word["ErrorType"] == "Omission":
            word = f"""<span data-toggle="tooltip" title="This word was omitted" class="word_omitted">{word_text}</span>"""
        elif word["ErrorType"] == "Insertion":
            word = f"""<span data-toggle="tooltip" title="This word is probably redundant" class="word_insertion">{word_text}</span>"""
        elif score < 90:
            word = f"""<span data-toggle="tooltip" title="Accuracy: {score}%" class="score-low">{word_text}</span>"""
        else:
            word = f"""<span data-toggle="tooltip" title="Accuracy: {score}%">{word_text}</span>"""

        word_list.append(word)

    return " ".join(word_list)


def show_score_with_emoji(score: float) -> str:
    emoji = ('💔', '😢', '🌧️', '😕', '🤨', '😐', '😊', '🌤️', '🎉', '💎')
    return f"{score} {emoji[int(score)]}"


def time_ago_in_words(dtime: datetime) -> str:
    past_time = datetime.utcnow() - dtime
    return naturaltime(past_time)


def init_jinja_filters(app):
    app.jinja_env.filters['time_ago_in_words'] = time_ago_in_words
    app.jinja_env.filters['show_score_with_emoji'] = show_score_with_emoji
    app.jinja_env.globals['convert_answer_object_to_html'] = convert_answer_object_to_html
