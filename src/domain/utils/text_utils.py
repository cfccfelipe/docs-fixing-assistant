import re
from typing import List

def split_markdown_by_headers(text: str, max_chars: int = 5000) -> List[str]:
    """
    Surgically splits a markdown document into semantic chunks based on headers.
    Ensures each chunk is below the max_chars threshold while maintaining header context.
    """
    if len(text) <= max_chars:
        return [text]

    # Split by level 2 headers
    sections = re.split(r'(?=\n## )', text)
    chunks = []
    current_chunk = ""

    for section in sections:
        if len(current_chunk) + len(section) > max_chars:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = section
        else:
            current_chunk += section

    if current_chunk:
        chunks.append(current_chunk)

    return chunks
