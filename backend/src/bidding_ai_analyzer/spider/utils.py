"""Utility functions for the spider module."""


def normalize_url(url: str, base_url: str = "") -> str:
    """Normalize a potentially relative URL to absolute."""
    from urllib.parse import urljoin
    if url.startswith("http"):
        return url
    if base_url:
        return urljoin(base_url, url)
    return url


def clean_text(text: str) -> str:
    """Clean extracted text by removing extra whitespace."""
    import re
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
