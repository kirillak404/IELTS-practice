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