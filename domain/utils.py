from __future__ import annotations

import re
import unicodedata


LEET_TRANSLATION = str.maketrans(
    {
        "0": "o",
        "1": "i",
        "3": "e",
        "4": "a",
        "5": "s",
        "7": "t",
        "@": "a",
        "$": "s",
        "!": "i",
    }
)


def ascii_fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return normalized.encode("ascii", "ignore").decode("ascii")


def normalize_token(value: str) -> str:
    lowered = ascii_fold(value).lower()
    return lowered.translate(LEET_TRANSLATION)


def tokenize_text(value: str) -> list[str]:
    normalized = normalize_token(value)
    tokens = re.split(r"[^a-z0-9]+", normalized)
    return [token for token in tokens if token]


def collapse_text(value: str) -> str:
    return "".join(tokenize_text(value))


def extract_registrable_domain(domain: str, compound_tlds: set[str]) -> tuple[str, str]:
    clean_domain = domain.strip(".").lower()
    labels = [label for label in clean_domain.split(".") if label]
    if len(labels) < 2:
        return clean_domain, ""

    suffix_two = ".".join(labels[-2:])
    suffix_three = ".".join(labels[-3:]) if len(labels) >= 3 else ""
    if suffix_two in compound_tlds and len(labels) >= 3:
        registrable = ".".join(labels[-3:])
        tld = suffix_two
        return registrable, tld
    if suffix_three in compound_tlds and len(labels) >= 4:
        registrable = ".".join(labels[-4:])
        tld = suffix_three
        return registrable, tld

    registrable = ".".join(labels[-2:])
    tld = labels[-1]
    return registrable, tld


def split_subdomains(domain: str, registrable_domain: str) -> list[str]:
    if domain == registrable_domain:
        return []
    suffix = f".{registrable_domain}"
    if not domain.endswith(suffix):
        return []
    prefix = domain[: -len(suffix)]
    return [label for label in prefix.split(".") if label]


def extract_domain_label(registrable_domain: str, tld: str) -> str:
    if not tld:
        return registrable_domain
    suffix = f".{tld}"
    if registrable_domain.endswith(suffix):
        return registrable_domain[: -len(suffix)].strip(".")
    return registrable_domain.split(".")[0]


def damerau_levenshtein_distance(source: str, target: str) -> int:
    if source == target:
        return 0
    if not source:
        return len(target)
    if not target:
        return len(source)

    previous_previous_row: list[int] | None = None
    previous_row = list(range(len(target) + 1))

    for row_index, source_char in enumerate(source, start=1):
        current_row = [row_index]
        for column_index, target_char in enumerate(target, start=1):
            insertions = current_row[column_index - 1] + 1
            deletions = previous_row[column_index] + 1
            substitutions = previous_row[column_index - 1] + (
                0 if source_char == target_char else 1
            )
            distance = min(insertions, deletions, substitutions)

            if (
                previous_previous_row is not None
                and row_index > 1
                and column_index > 1
                and source_char == target[column_index - 2]
                and source[row_index - 2] == target_char
            ):
                distance = min(distance, previous_previous_row[column_index - 2] + 1)

            current_row.append(distance)

        previous_previous_row = previous_row
        previous_row = current_row

    return previous_row[-1]


def looks_like_typosquatting(candidate: str, official: str, max_distance: int = 2) -> bool:
    normalized_candidate = normalize_token(candidate)
    normalized_official = normalize_token(official)
    if normalized_candidate == normalized_official:
        return False
    if abs(len(normalized_candidate) - len(normalized_official)) > max_distance:
        return False
    return damerau_levenshtein_distance(normalized_candidate, normalized_official) <= max_distance
