"""
agent/exporter.py
================
Handles content transformation and filesystem persistence for research reports.
Supports TXT (cleaned for readability) and PDF (rich formatting) formats.
"""

import os
import re
from typing import Dict, List, Tuple
from fpdf import FPDF
import markdown2

# ---------------------------------------------------------------------------
# GLOBAL CONFIGURATIONS
# ---------------------------------------------------------------------------

EXPORT_DIRECTORY: str = "exports"
os.makedirs(EXPORT_DIRECTORY, exist_ok=True)

# Markers
SOURCES_MARKER: str = "SOURCES & REFERENCES"

# Plaintext Markdown Strip Expressions
MARKDOWN_CLEAN_PATTERNS: List[Tuple[str, str]] = [
    (r"\(https?://\S+\)", ""),        # Inline URLs
    (r"\[\d+\]:\s*https?://\S+", ""),  # Reference definitions
    (r"\[\d+\]", ""),                 # Citation markers [1]
    (r"[*_`]", ""),                   # Bold, italic, code ticks
]

# Character Mapping Table for Target Latin-1 PDF Engine Compatibility
LATIN1_CHAR_MAP: Dict[str, str] = {
    "—": "-",
    "–": "-",
    "“": '"',
    "”": '"',
    "’": "'",
    "‘": "'",
}
LATIN1_TRANSLATION_TABLE = str.maketrans(LATIN1_CHAR_MAP)


# ---------------------------------------------------------------------------
# UTILITY HELPER METHODS
# ---------------------------------------------------------------------------

def slugify_topic(topic: str) -> str:
    """
    Transforms a raw research topic string into a clean, filesystem-safe filename.
    Example: "Quantum Computing: Trends for 2026!" -> "quantum_computing_trends_for_2026"
    """
    cleaned: str = topic.lower().strip()
    cleaned = re.sub(r"[^\w\s-]", "", cleaned)
    cleaned = re.sub(r"[\s-]+", "_", cleaned)
    return cleaned if cleaned else "untitled_research_report"


def _extract_source_links(text: str) -> str:
    """
    Isolates and formats raw URLs from the sources section.
    Provides a clean, uniform list of references at the end of TXT files.
    """
    if SOURCES_MARKER.upper() not in text.upper():
        return ""

    parts: List[str] = re.split(f"(?i){SOURCES_MARKER}", text, maxsplit=1)
    if len(parts) < 2:
        return ""

    sources_section: str = parts[1]
    links: List[str] = re.findall(r"https?://\S+", sources_section)
    if not links:
        return ""

    formatted_block: str = f"\n\n{SOURCES_MARKER}\n{'-' * len(SOURCES_MARKER)}\n"
    formatted_block += "\n".join([f"• {link.strip(')]')}" for link in links])
    return formatted_block


def clean_markdown_for_txt(text: str) -> str:
    """
    Strips markdown syntax elements and inline references to output clean plaintext.
    """
    body: str = re.split(r"(?i)SOURCES & REFERENCES", text, maxsplit=1)[0]

    for pattern, replacement in MARKDOWN_CLEAN_PATTERNS:
        body = re.sub(pattern, replacement, body)

    # Format headers: structural transform from '# Header' to 'UPPERCASE HEADER \n ----'
    body = re.sub(
        r"^(#+)\s*(.*)$",
        lambda m: f"\n{m.group(2).upper()}\n{'-' * len(m.group(2))}",
        body,
        flags=re.MULTILINE,
    )

    # Standardize list formatting structures
    body = re.sub(r"^-\s+", "• ", body, flags=re.MULTILINE)

    final_output: str = body.strip() + _extract_source_links(text)
    
    # Compress excessive line breaks down to double spaces
    return re.sub(r"\n{3,}", "\n\n", final_output)


# ---------------------------------------------------------------------------
# CORE EXPORT CONVERTERS
# ---------------------------------------------------------------------------

def export_to_txt(content: str, topic_name: str) -> str:
    """
    Transforms structural markdown input payloads into a clean plaintext file.
    Saves output locally and returns the absolute generated file path.
    """
    cleaned_content: str = clean_markdown_for_txt(content)
    safe_filename: str = f"{slugify_topic(topic_name)}.txt"
    file_path: str = os.path.join(EXPORT_DIRECTORY, safe_filename)

    with open(file_path, "w", encoding="utf-8") as file_writer:
        file_writer.write(cleaned_content)
        
    return file_path


def export_to_pdf(content: str, topic_name: str) -> str:
    """
    Converts markdown documents into valid, formatted PDF publications.
    Safely maps non-standard character codes to standard Latin-1 strings.
    """
    safe_filename: str = f"{slugify_topic(topic_name)}.pdf"
    file_path: str = os.path.join(EXPORT_DIRECTORY, safe_filename)
    
    # Generate temporary standard HTML string payload segment structures
    html_content: str = markdown2.markdown(content)

    # Map dynamic complex Unicode punctuation markers to clean alternative characters
    safe_html: str = html_content.translate(LATIN1_TRANSLATION_TABLE)
    safe_html = safe_html.encode("latin-1", "replace").decode("latin-1")

    # Construct Document Layout Architecture Configuration Canvas
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margin(15)
    pdf.set_font("helvetica", size=12)
    
    # Render and stream file asset directly down to target directory path
    pdf.write_html(safe_html)
    pdf.output(file_path)
    
    return file_path
