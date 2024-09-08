import re
from functools import partial, reduce
from typing import List, Optional

EXCLUDED_CHARACTERS = ["™", "®", "©"]
EXCLUDED_LEADING_CHARS = ["#", "*"]
LEADING_SEQUENCE = ".."
TRAILING_SEQUENCE = "..."


def remove_excluded_characters(text: str, excluded_chars: List[str]) -> str:
    pattern = f"[{''.join(excluded_chars)}]"
    return re.sub(pattern, "", text)


def remove_leading_non_alphanumeric_chars(text: str, remove_only_excluded_chars: bool = True) -> str:
    if remove_only_excluded_chars:
        pattern = f"^[{''.join(EXCLUDED_LEADING_CHARS)}]+"
    else:
        pattern = r"^\W+"
    return re.sub(pattern, "", text)


def remove_multi_consecutive_whitespaces(text: str) -> str:
    """
    For each sub-sequence of consecutive whitespace characters in the input `text` string, this function
    removes all whitespace characters but the first one.
    """
    return re.sub(r"(?<=\s)\s+", "", text)


def add_leading_sequence(text: str, seq: str, append: bool) -> str:
    if append:
        return seq + text
    return seq + text[len(seq) :]


def add_trailing_sequence(text: str, seq: str, append: bool) -> str:
    if append:
        return text + seq
    return text[: -len(seq)] + seq


def clean_text_snippet(
    text: str,
    add_dots_on_start: Optional[bool] = False,
    add_dots_on_end: Optional[bool] = True,
    remove_consecutive_spaces: Optional[bool] = True,
    remove_only_excluded_leading_chars: Optional[bool] = True,
    max_length: Optional[int] = None,
) -> str:
    """
    Clean a text snippet.

    Parameters
    ----------
    text : str
        Text snippet to be cleaned
    add_dots_on_start : bool, by default False
        Whether to add two dots in the start of the snippet
    add_dots_on_end : bool, by default True
        Whether to add three dots in the end of the snippet
    remove_consecutive_spaces : bool, by default True
        Whether to remove consecutive whitespaces and line breaks
    remove_only_excluded_leading_chars : bool, by default True
        Whether to remove only specific leading non-alphanumeric characters
    max_length : None
        Maximum no. characters in the text snippet, by default None
    Returns
    -------
    str
        Cleaned text snippet
    """
    leading_sequence = LEADING_SEQUENCE if add_dots_on_start else ""
    trailing_sequence = TRAILING_SEQUENCE if add_dots_on_end else ""
    return reduce(
        lambda x, f: f(x),
        [
            text,
            partial(remove_excluded_characters, excluded_chars=EXCLUDED_CHARACTERS),
            partial(
                remove_leading_non_alphanumeric_chars,
                remove_only_excluded_chars=remove_only_excluded_leading_chars,
            ),
            lambda x: x.rstrip(),
            remove_multi_consecutive_whitespaces if remove_consecutive_spaces else lambda x: x,
            lambda x: x[slice(None, max_length, None)],
            partial(add_leading_sequence, seq=leading_sequence, append=False),
            partial(add_trailing_sequence, seq=trailing_sequence, append=True),
        ],
    )


def remove_page_numbers(text: str) -> str:
    """Remove page numbers from document text"""
    return re.sub(r"\[page \d+\]", "", text)
