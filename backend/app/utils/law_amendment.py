import re


_AMENDMENT_TYPE_RE = re.compile(r"전부개정|일부개정|타법개정|제정|폐지|개정")


def extract_amendment_type(raw_text: str | None) -> str | None:
    """Extract the document-level enactment/amendment marker from stored source text.

    Only the document header is inspected. This avoids treating every article-level
    ``<개정 ...>`` annotation as a separate amendment event.
    """
    if not raw_text:
        return None

    header = raw_text[:4_000]
    match = _AMENDMENT_TYPE_RE.search(header)
    return match.group(0) if match else None


def prepend_amendment_marker(raw_text: str, amendment_type: str | None) -> str:
    """Keep the API's enactment/amendment classification in the stored raw source."""
    if not amendment_type or amendment_type in raw_text[:500]:
        return raw_text
    return f"[제개정구분: {amendment_type}]\n{raw_text}"
