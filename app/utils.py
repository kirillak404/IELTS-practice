import openai


def transcript_file(file_path: str) -> str:
    audio_file = open(file_path, "rb")
    transcript = openai.Audio.transcribe("whisper-1", audio_file,
                                         language="en")
    return transcript["text"]


def validation_class(field):
    if field.errors:
        return "is-invalid"
    elif field.data or field.raw_data:
        return "is-valid"
    return ""
