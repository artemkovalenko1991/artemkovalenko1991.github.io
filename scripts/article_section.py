"""Select public article content, ignoring headings inside fenced code blocks."""
import re

def extract_article(text):
    lines = text.splitlines(keepends=True)
    start = end = None
    fence = None
    for i, line in enumerate(lines):
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if marker:
            token = marker[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence) and not line[marker.end():].strip():
                fence = None
            continue
        if fence:
            continue
        heading = re.match(r'^ {0,3}(#{1,6})[ \t]+(.+?)\s*$', line)
        if not heading:
            continue
        level = len(heading[1])
        title = re.sub(r'[ \t]+#+[ \t]*$', '', heading[2]).strip()
        if level == 2 and title == 'Текст статьи':
            if start is not None:
                raise ValueError('Найдено несколько разделов «Текст статьи»')
            start = i + 1
        elif start is not None and end is None and level <= 2:
            end = i
    if start is None:
        raise ValueError('Не найден раздел «## Текст статьи»')
    result = ''.join(lines[start:end]).strip()
    if not result:
        raise ValueError('Раздел «Текст статьи» пуст')
    return result + '\n'
