import re
import string
from typing import List, Literal

from model.relevance.bleu import compute_bleu
from model.relevance.tokenizer import Tokenizer13a
from utils.text import clean_text_snippet

STOPWORD_SET = {
    "wouldn't",
    "both",
    "about",
    "me",
    "its",
    "out",
    "hasn",
    "itself",
    "been",
    "ain",
    "myself",
    "below",
    "down",
    "any",
    "d",
    "herself",
    "up",
    "whom",
    "these",
    "by",
    "isn't",
    "very",
    "am",
    "ours",
    "has",
    "a",
    "than",
    "yourself",
    "not",
    "i",
    "his",
    "if",
    "couldn't",
    "too",
    "should",
    "doing",
    "mightn't",
    "you'll",
    "my",
    "those",
    "hers",
    "then",
    "other",
    "being",
    "you've",
    "he",
    "above",
    "had",
    "how",
    "once",
    "only",
    "she",
    "wouldn",
    "doesn't",
    "haven't",
    "mustn",
    "same",
    "hadn't",
    "our",
    "more",
    "shouldn",
    "there",
    "when",
    "hasn't",
    "just",
    "wasn",
    "at",
    "each",
    "do",
    "over",
    "most",
    "while",
    "she's",
    "and",
    "ma",
    "they",
    "himself",
    "nor",
    "the",
    "further",
    "having",
    "off",
    "you'd",
    "as",
    "them",
    "aren",
    "it",
    "such",
    "all",
    "who",
    "this",
    "their",
    "her",
    "with",
    "will",
    "couldn",
    "where",
    "of",
    "didn't",
    "or",
    "here",
    "won't",
    "before",
    "isn",
    "that'll",
    "needn",
    "have",
    "did",
    "into",
    "we",
    "yourselves",
    "in",
    "few",
    "after",
    "so",
    "s",
    "t",
    "ve",
    "haven",
    "needn't",
    "yours",
    "don",
    "theirs",
    "again",
    "during",
    "are",
    "weren",
    "o",
    "is",
    "but",
    "can",
    "should've",
    "were",
    "from",
    "didn",
    "m",
    "don't",
    "it's",
    "re",
    "until",
    "because",
    "under",
    "between",
    "through",
    "ll",
    "some",
    "aren't",
    "y",
    "won",
    "was",
    "you're",
    "wasn't",
    "own",
    "him",
    "what",
    "which",
    "on",
    "shan't",
    "that",
    "be",
    "against",
    "mightn",
    "shan",
    "you",
    "no",
    "doesn",
    "does",
    "ourselves",
    "weren't",
    "mustn't",
    "shouldn't",
    "to",
    "themselves",
    "why",
    "for",
    "now",
    "hadn",
    "an",
    "your",
}


def _get_last_word_combination(input_text: str, length: int) -> str:
    """
    Get last combination of words from the input string

    Parameters
    ----------
    input_text : str
        Input text
    length : int
        Word combination length

    Returns
    -------
    str
        Last word combination
    """
    splitted_text = re.findall(r"\S+|\n", input_text)
    if len(splitted_text) == 0:
        return input_text
    return splitted_text[length - 1]


def _combine_words(splitted_text: List[str], length: int):
    """
    Combine words

    Parameters
    ----------
    splitted_text : List[str]
        Text splitted into words
    length : int
        Length of the combinations
    """
    combined_inputs = []
    if len(splitted_text) > 1:
        for i in range(len(splitted_text) - 1):
            combined_inputs.append(
                f"{splitted_text[i]} {_get_last_word_combination(input_text = splitted_text[i + 1], length = length)}"
            )
            # add the last word of the right-neighbor (overlapping) sequence (before it has expanded),
            # which is the next word in the original sentence
    return combined_inputs, length + 1


def _remove_duplicates(splitted_text: List[str], length: int):
    """
    Recursively remove duplicate word combinations

    Parameters
    ----------
    splitted_text : str
        Text splitted into words
    length : int
        Length of the combinations
    """
    bool_broke = False  # this means we didn't find any duplicates here
    for i in range(len(splitted_text) - length):
        if splitted_text[i] == splitted_text[i + length]:  # found a duplicate piece of sentence!
            for j in range(0, length):  # remove the overlapping sequences in reverse order
                del splitted_text[i + length - j]
            bool_broke = True
            break  # break the for loop as the loop length does not matches the length of
            # splitted_input anymore as we removed elements
    if bool_broke:
        return _remove_duplicates(
            splitted_text, length
        )  # if we found a duplicate, look for another duplicate of the same length
    return splitted_text


# make a list of strings which represent every sequence of word_length adjacent words
def remove_repetitions(input_text: str):
    """
    Remove repeated word combinations

    Parameters
    ----------
    input_text : str
        Input text with repetitions
    """
    splitted_input = re.findall(r"\S+|\n", input_text)
    word_length = 1

    splitted_input, word_length = _combine_words(splitted_text=splitted_input, length=word_length)

    num_iter = 0
    while len(splitted_input) > 1:
        splitted_input = _remove_duplicates(splitted_text=splitted_input, length=word_length)
        # Look whether two sequences of length n (with distance n apart) are equal.
        # If so, remove the n overlapping sequences
        splitted_input, word_length = _combine_words(
            splitted_text=splitted_input, length=word_length
        )  # make even bigger sequences
        num_iter += 1

    if len(splitted_input) > 0:
        return splitted_input[0].replace("\n ", "\n")
    return input_text


def clean_question(question: str) -> str:
    """
    Clean question sent to LLM

    Parameters
    ----------
    question : str
        Raw user question

    Returns
    -------
    str
        Cleaned user question
    """
    if question != "":
        while question[0] in string.punctuation + " ":
            question = question[1:]
        while question[-1] == " ":
            question = question[:-1]
        question = question[0].capitalize() + question[1:]

    return question


def clean_answer(  # noqa: C901
    answer: str,
    remove_first_bulletpoint: bool = True,
    remove_last_keywords: bool = False,
) -> str:
    """
    Clean LLM answer

    Parameters
    ----------
    answer : str
        Raw answer from LLM
    remove_first_bulletpoint : bool, by default True
        Whether to add two dots in the start of the snippet
    remove_last_keywords : bool, by default False
        Whether to remove "Keywords:" at the end of the answer

    Returns
    -------
    str
        Cleaned LLM answer
    """

    # check bulletpoint
    if not remove_first_bulletpoint and answer[0] == "-":
        has_bulletpoint = True
    else:
        has_bulletpoint = False

    # replace incomplete line breaks
    answer = answer.replace("<n>", "")

    # check if answer is empty
    if len(answer) <= 1:
        return "[NO ANSWER]"

    # add bulletpoint if needed
    if has_bulletpoint:
        answer = "- " + answer

    # remove last breaks and whitespaces
    while answer[-1] == " ":
        answer = answer[:-1]
    while answer[-1] == "\n":
        answer = answer[:-1]

    # remove answer & context
    if answer[:7] == "Answer:":
        answer = answer[8:]
    if answer[-8:] == "Context:":
        answer = answer[:-8]

    # remove everything after "Human:"
    answer = answer.split("Human:")[0]

    # remove keywords
    if remove_last_keywords:
        if answer.split()[-1] == "Keywords:":
            answer = answer[:-10]

    # capitalize and add dot
    answer = answer[0].capitalize() + answer[1:]
    if answer[-1] not in ["!", "?", "."]:
        answer += "."

    return remove_repetitions(answer)


def check_relevance(
    context: str,
    question: str,
    answer: str,
    length_cutoff: int = 3,
    verbose: bool = False,
) -> List[float]:
    """
    Check relevance of the context for answer and question

    Parameters
    ----------
    context : str
        Context provided for RAG
    question : str
        User question
    answer : str
        Answer from LLM
    length_cutoff : int
        If number of terms in the question or answer is smaller than length_cutoff, return score of 1.0
    verbose : bool
        Whether to print intermediate steps details

    Returns
    -------
    List[float]
        Coverage scores for question and answer between 0 and 1
    """

    # remove punctuation and lowercase
    question = re.sub(r"[^\w\s]", "", question).lower()
    context = re.sub(r"[^\w\s]", "", context).lower()
    answer = re.sub(r"[^\w\s]", "", answer).lower()

    # split question
    question = re.compile("\\w+").findall(question)
    question = {term for term in question if term not in STOPWORD_SET}

    # split answer
    answer = re.compile("\\w+").findall(answer)
    answer = {term for term in answer if term not in STOPWORD_SET}

    # calculate question coverage
    if len(question) >= length_cutoff:
        coverage_q = sum([term in context for term in question]) / len(question)
    else:
        coverage_q = 1.0

    # calculate answer coverage
    if len(answer) >= length_cutoff:
        coverage_a = sum([term in context for term in answer]) / len(answer)
    else:
        coverage_a = 1.0

    # display feedback
    if verbose:
        print(f"Question: {question}")
        print(f"Answer: {answer}")
        # print(f"Context: {context}")
        print(f"Coverage: Q = {coverage_q}, A = {coverage_a}")

    # output
    return [coverage_q, coverage_a]


def check_token_intersection(
    context: str,
    answer: str,
    length_cutoff: int = 3,
) -> float:
    """
    Calculates relevance score using token intersection metrics

    Parameters
    ----------
    context : str
        Context provided by the retriever
    answer : str
        Answer from the LLM to be checked
    length_cutoff : int, optional, by default 3
        Returns 1.0 if the number of tokens in the answer is below length_cutoff
        Returns 0.0 if the number of tokens in the context is below length_cutoff

    Returns
    -------
    float
        Relevance score between 0 (likely hallucinated) and 1 (likely based on the context)
    """

    context = re.sub(r"[^\w\s]", "", context).lower()
    answer = re.sub(r"[^\w\s]", "", answer).lower()

    if len(context.split()) < length_cutoff:
        return 0.0

    if len(answer.split()) < length_cutoff:
        return 1.0

    context = [[c] for c in [context]]
    answer = [answer]

    tokenizer = Tokenizer13a()
    context = [[tokenizer(c) for c in con if c not in STOPWORD_SET] for con in context]
    answer = [tokenizer(a) for a in answer if a not in STOPWORD_SET]

    scores = compute_bleu(context, answer)  # returns tuple: BLEU, n-gram precisions, geometric mean of n-gram
    return sum(scores[1]) / len(scores[1])  # average of n-gram precisions as relevance score


def calculate_relevance_score(
    answer: str,
    context: str,
    question: str = None,
    method: Literal[None, "WORLD_RELEVANCE", "TOKEN_INTERSECTION"] = None,
) -> float:
    """
    Calculates relevance score

    Parameters
    ----------
    answer : str
        LLM answer
    context : str
        Retrieved context
    question : str, optional
        User question, by default None
    method : str, optional
        Hallucination detection method, one of [None, "WORLD_RELEVANCE", "TOKEN_INTERSECTION"], by default None

    Returns
    -------
    float
        Hallucination score between 0.0 (likely hallucinated) and 1.0 (likely correct)
    """
    if method == "WORD_RELEVANCE":
        return min(check_relevance(answer=answer, context=context, question=question, length_cutoff=3))
    if method == "TOKEN_INTERSECTION":
        return check_token_intersection(answer=answer, context=context, length_cutoff=3)
    return 1.0


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into a list of non-empty sentences

    Parameters
    ----------
    text : str
        Input text to be splitted

    Returns
    -------
    List[str]
        List of individual sentences
    """

    try:
        sentences = re.split(r"[.!?]\s*", text)
        sentences = [
            clean_text_snippet(
                sentence,
                add_dots_on_start=False,
                add_dots_on_end=False,
                remove_consecutive_spaces=False,
                remove_only_excluded_leading_chars=False,
            ).strip()
            for sentence in sentences
        ]
        return [sentence for sentence in sentences if len(sentence) > 1]

    except Exception:
        return [text]
