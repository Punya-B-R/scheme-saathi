"""
Documents extraction for Public Safety, Law & Justice schemes.

Extracts structured document requirements from relevant sections.
"""

from __future__ import annotations

from typing import Any, Dict, List

from bs4 import BeautifulSoup


def _split_lines(text: str) -> List[str]:
    lines = []
    for raw in text.split("\n"):
        line = " ".join(raw.split())
        if line:
            lines.append(line)
    return lines


def extract_documents(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    Extract list of required documents with basic structure.
    Looks for sections/headings containing 'Document' or 'Certificate'.
    """
    docs: List[Dict[str, Any]] = []

    candidates: List[str] = []

    # Look for headings and following lists
    for heading_tag in ["h2", "h3", "h4", "strong", "b"]:
        for h in soup.find_all(heading_tag):
            txt = h.get_text(strip=True)
            if not txt:
                continue
            if "document" in txt.lower() or "certificate" in txt.lower():
                # Collect text from following sibling lists/paragraphs
                sib = h.find_next_sibling()
                collected = []
                while sib and sib.name in ("p", "ul", "ol", "li", "div"):
                    collected.append(sib.get_text(separator="\n", strip=True))
                    sib = sib.find_next_sibling()
                if collected:
                    candidates.append("\n".join(collected))

    if not candidates:
        # Fallback: look for generic 'documents required' text anywhere
        for div in soup.find_all(["div", "section", "article"]):
            text = div.get_text(separator="\n", strip=True)
            if "documents required" in text.lower():
                candidates.append(text)
                break

    if not candidates:
        return docs

    # Use first candidate block for now
    block = candidates[0]
    for line in _split_lines(block):
        # Skip very short lines
        if len(line) < 5:
            continue
        doc = {
            "document_name": line,
            "mandatory": True,
            "specifications": "",
            "notes": "",
            "validity": "",
        }
        docs.append(doc)

    return docs

