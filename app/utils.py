import time

def validation_class(field):
    if field.errors:
        return "is-invalid"
    elif field.data or field.raw_data:
        return "is-valid"
    return ""


def highlight_errors(content, mistakes):
    for error in mistakes:
        content = content.replace(error['IncorrectText'], f'<span class="highlight" data-bs-toggle="tooltip" title="{error["Explanation"]}">{error["IncorrectText"]}</span>')
    return content


def convert_list_to_string(string_list: list) -> str:
    return "\n".join(f"{s[0]}. {s[1]}" for s in enumerate(string_list, start=1))


def measure_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Function {func.__name__} executed in {int(execution_time)} seconds.")
        return result
    return wrapper