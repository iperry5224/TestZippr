"""Inspect the draft AOR document structure."""
from docx import Document
from pathlib import Path

doc = Document(Path(__file__).parent / "DRAFT_AOR_SAE_CSTA-SANDBOX.docx")
for i, para in enumerate(doc.paragraphs):
    style = para.style.name if para.style else ""
    text = para.text[:80] + "..." if len(para.text) > 80 else para.text
    print(f"{i:3} [{style:20}] {repr(text)}")
