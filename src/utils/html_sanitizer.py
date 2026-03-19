import re
import html


def sanitize_html(raw_html: str) -> str:
    """Extract only visible text from HTML email bodies.

    Strips scripts, styles, hidden elements, invisible Unicode,
    and HTML comments to prevent prompt injection.

    Args:
        raw_html: Raw HTML string from email body.

    Returns:
        Clean plain text with boundary markers.
    """
    if not raw_html:
        return ""

    text = raw_html

    # Remove HTML comments (can hide prompt injections)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    # Remove dangerous tags entirely (content included)
    for tag in ["script", "style", "head", "iframe", "object", "embed", "applet", "noscript"]:
        text = re.sub(rf"<{tag}[^>]*>.*?</{tag}>", "", text, flags=re.DOTALL | re.IGNORECASE)

    # Remove elements with hidden attribute
    text = re.sub(r'<[^>]+\bhidden\b[^>]*>.*?</[^>]+>', "", text, flags=re.DOTALL | re.IGNORECASE)

    # Remove elements with aria-hidden="true"
    text = re.sub(r'<[^>]+aria-hidden\s*=\s*["\']true["\'][^>]*>.*?</[^>]+>', "", text, flags=re.DOTALL | re.IGNORECASE)

    # Remove elements with hiding CSS inline styles
    hiding_patterns = [
        r'display\s*:\s*none',
        r'visibility\s*:\s*hidden',
        r'opacity\s*:\s*0\b',
        r'font-size\s*:\s*0\b',
        r'height\s*:\s*0\b',
        r'width\s*:\s*0\b',
        r'max-height\s*:\s*0\b',
        r'max-width\s*:\s*0\b',
        r'overflow\s*:\s*hidden',
    ]
    for pattern in hiding_patterns:
        text = re.sub(
            rf'<[^>]+style\s*=\s*["\'][^"\']*{pattern}[^"\']*["\'][^>]*>.*?</[^>]+>',
            "", text, flags=re.DOTALL | re.IGNORECASE
        )

    # Convert block elements to newlines
    block_tags = ["div", "p", "br", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "hr"]
    for tag in block_tags:
        text = re.sub(rf"</?{tag}[^>]*>", "\n", text, flags=re.IGNORECASE)

    # Strip all remaining HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Decode HTML entities
    text = html.unescape(text)

    # Remove invisible Unicode characters (zero-width spaces, joiners, etc.)
    invisible_chars = [
        "\u200b",  # Zero-width space
        "\u200c",  # Zero-width non-joiner
        "\u200d",  # Zero-width joiner
        "\u2060",  # Word joiner
        "\ufeff",  # BOM / zero-width no-break space
        "\u00ad",  # Soft hyphen
        "\u200e",  # Left-to-right mark
        "\u200f",  # Right-to-left mark
        "\u202a",  # Left-to-right embedding
        "\u202b",  # Right-to-left embedding
        "\u202c",  # Pop directional formatting
        "\u202d",  # Left-to-right override
        "\u202e",  # Right-to-left override
        "\u2061",  # Function application
        "\u2062",  # Invisible times
        "\u2063",  # Invisible separator
        "\u2064",  # Invisible plus
    ]
    for char in invisible_chars:
        text = text.replace(char, "")

    # Collapse whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    if not text:
        return ""

    # Wrap in boundary markers for LLM safety
    return f"--- BEGIN EMAIL BODY ---\n{text}\n--- END EMAIL BODY ---"
