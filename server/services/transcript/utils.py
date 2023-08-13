def preporcess_transcript(raw_text):
    """
    Подготавливает текст.
    Очищает от постфиксов ([музыка], [смех]), знака '\n'
    """
    clear_text = del_postscript(raw_text.replace('\n', ' ').replace('♪', '').strip(
        ' - ').strip(' '))

    return clear_text


def del_postscript(text):
    """
    Удаляет постфиксы: [музыка], [смех]
    """
    startPostcript = text.find('[')
    endPostcript = text.find(']')
    if startPostcript != -1 and endPostcript != -1:
        postcript = text[startPostcript:][:endPostcript + 1]
        text = text.replace(postcript, '')
    return text
