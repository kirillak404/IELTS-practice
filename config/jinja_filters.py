from app.utils import convert_answer_object_to_html, time_ago_in_words, show_score_with_emoji


def init_jinja_filters(app):
    app.jinja_env.filters['time_ago_in_words'] = time_ago_in_words
    app.jinja_env.filters['show_score_with_emoji'] = show_score_with_emoji
    app.jinja_env.globals['convert_answer_object_to_html'] = convert_answer_object_to_html
