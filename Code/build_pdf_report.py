"""
PDF Report Generator for Automotive TARA Assistant.
Uses ReportLab Platypus to compile technical_report.md into technical_report.pdf
with a real two-pass page-numbered Table of Contents, running headers, and clean typography.
"""
import os
import re
import sys
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable, Flowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

PROJECT_ROOT = Path(__file__).parent.resolve()
MD_PATH = PROJECT_ROOT / "Documentation" / "technical_report.md"
PDF_PATH = PROJECT_ROOT / "Documentation" / "technical_report.pdf"

# Global dictionary to record exact page numbers for each H1 heading
section_page_map = {}

class BookmarkFlowable(Flowable):
    """Zero-height flowable that captures the canvas page number when drawn."""
    def __init__(self, key):
        super().__init__()
        self.key = key
        self.width = 0
        self.height = 0

    def draw(self):
        section_page_map[self.key] = self.canv._pageNumber

class NumberedCanvas(canvas.Canvas):
    """Canvas that computes total pages dynamically and adds running headers/footers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#718096"))

        # Skip header on Title Page (Page 1)
        if self._pageNumber > 1:
            self.drawString(36, 11 * 72 - 24, "AUTOMOTIVE CYBERSECURITY TARA ASSISTANT — TECHNICAL REPORT")
            self.drawRightString(8.5 * 72 - 36, 11 * 72 - 24, "TECHPULSE CAPSTONE")
            self.setStrokeColor(colors.HexColor("#CBD5E0"))
            self.setLineWidth(0.5)
            self.line(36, 11 * 72 - 28, 8.5 * 72 - 36, 11 * 72 - 28)

        # Running footer on all pages
        self.setStrokeColor(colors.HexColor("#CBD5E0"))
        self.setLineWidth(0.5)
        self.line(36, 36, 8.5 * 72 - 36, 36)
        
        self.setFont("Helvetica", 8)
        self.drawString(36, 24, "Academic Prototype | Informed by ISO/SAE 21434 & UNECE R155 Concepts")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * 72 - 36, 24, page_str)
        self.restoreState()

def clean_inline_md(text):
    """Convert markdown formatting to ReportLab XML tags and strip raw links."""
    # Strip markdown links [Title](url) -> Title
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    # Convert bold, italic, code
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    text = re.sub(r'`(.*?)`', r'<font name="Courier" color="#2B6CB0">\1</font>', text)
    # Sanitize naked ampersands that are not XML entities
    text = re.sub(r'&(?!amp;|lt;|gt;|quot;|nbsp;)', '&amp;', text)
    return text

def build_story(md_text, page_map):
    styles = getSampleStyleSheet()

    primary_color = colors.HexColor("#1A365D")
    secondary_color = colors.HexColor("#2B6CB0")
    dark_text = colors.HexColor("#2D3748")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=primary_color,
        alignment=0,
        spaceAfter=8
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=secondary_color,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    h3_style = ParagraphStyle(
        'Heading3_Custom',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=dark_text,
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=dark_text,
        spaceAfter=5
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=dark_text,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=2
    )

    callout_style = ParagraphStyle(
        'Callout_Custom',
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#742A2A"),
        backColor=colors.HexColor("#FFF5F5"),
        borderColor=colors.HexColor("#E53E3E"),
        borderWidth=1,
        borderPadding=7,
        spaceBefore=6,
        spaceAfter=8,
        borderRadius=4
    )

    code_style = ParagraphStyle(
        'Code_Custom',
        fontName='Courier',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#E2E8F0"),
        backColor=colors.HexColor("#1A202C"),
        borderPadding=5,
        spaceBefore=5,
        spaceAfter=6,
        borderRadius=3
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=dark_text
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white
    )

    toc_title_style = ParagraphStyle(
        'TOCTitle',
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=primary_color
    )

    toc_page_style = ParagraphStyle(
        'TOCPage',
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=secondary_color,
        alignment=2 # Right align
    )

    story = []
    lines = md_text.split('\n')

    in_code_block = False
    code_block_lines = []
    in_callout = False
    callout_lines = []
    skip_md_toc = False

    i = 0
    while i < len(lines):
        line = lines[i]
        raw_line = line.strip()

        # Handle Code blocks
        if raw_line.startswith('```'):
            if in_code_block:
                code_text = "<br/>".join([clean_inline_md(l).replace(" ", "&nbsp;") for l in code_block_lines])
                story.append(Paragraph(code_text, code_style))
                code_block_lines = []
                in_code_block = False
            else:
                in_code_block = True
                code_block_lines = []
            i += 1
            continue

        if in_code_block:
            code_block_lines.append(line)
            i += 1
            continue

        # Handle Callout blocks (> [!IMPORTANT] ...)
        if raw_line.startswith('> [!') or (in_callout and raw_line.startswith('>')):
            clean_callout_line = raw_line.lstrip('> ').replace('[!IMPORTANT]', '<b>IMPORTANT ADVISORY:</b>').replace('[!NOTE]', '<b>NOTE:</b>')
            callout_lines.append(clean_inline_md(clean_callout_line))
            in_callout = True
            i += 1
            continue

        if in_callout and not raw_line.startswith('>'):
            story.append(Paragraph(" ".join(callout_lines), callout_style))
            callout_lines = []
            in_callout = False

        if not raw_line:
            i += 1
            continue

        # Handle Table of Contents replacement
        if raw_line.startswith('## Table of Contents'):
            story.append(BookmarkFlowable("Table of Contents"))
            story.append(Paragraph("Table of Contents", h1_style))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E0"), spaceBefore=2, spaceAfter=6))
            
            # Build two-column structured TOC Table
            toc_entries = [
                "1. Introduction and Background",
                "2. Problem Statement",
                "3. Project Objectives and Scope",
                "4. Intended Users and Use Cases",
                "5. Existing Approach and Limitations",
                "6. Proposed Solution and Contributions",
                "7. Functional and Non-Functional Requirements",
                "8. System Architecture",
                "9. Technology Stack and Justification",
                "10. Input Knowledge Base & Synthetic Dataset Description",
                "11. Data Ingestion, Chunking, Embeddings, & Vector Store",
                "12. RAG Pipeline & Multi-Provider LLM Integration",
                "13. Automotive TARA Analysis Workflow",
                "14. Asset Identification & CIA/A Security Properties",
                "15. Trust-Boundary and Attack-Surface Analysis",
                "16. STRIDE Threat Scenario Generation",
                "17. Deterministic Risk Assessment & Qualitative AI Reasoning",
                "18. Mitigation Recommendations & Requirement Generation",
                "19. End-to-End Traceability Matrix",
                "20. Application Architecture & User Interface",
                "21. Implementation Details & Module Structure",
                "22. Prompt Engineering & Prompt Injection Safeguards",
                "23. Evaluation Methodology, Benchmark Dataset, & Empirical Results",
                "24. Unit Testing & Verification Results",
                "25. Responsible AI, Privacy, & Security Guardrails",
                "26. Innovations & Key Distinguishing Features",
                "27. Installation, Configuration, & Execution Guide",
                "28. Demonstration Procedure & Sample Interactions",
                "29. Conclusion & Future Enhancements",
                "30. References and Citations",
                "31. Appendices"
            ]

            toc_table_data = []
            # Split entries into 2 columns for compact, clean layout
            mid = (len(toc_entries) + 1) // 2
            col1_entries = toc_entries[:mid]
            col2_entries = toc_entries[mid:]

            for idx in range(len(col1_entries)):
                e1 = col1_entries[idx]
                p1 = f"Page {page_map.get(e1, 1)}"
                e2 = col2_entries[idx] if idx < len(col2_entries) else ""
                p2 = f"Page {page_map.get(e2, 1)}" if e2 else ""

                row = [
                    Paragraph(e1, toc_title_style),
                    Paragraph(p1, toc_page_style),
                    Paragraph(e2, toc_title_style) if e2 else "",
                    Paragraph(p2, toc_page_style) if p2 else ""
                ]
                toc_table_data.append(row)

            # 540 pt available width: [210, 50, 230, 50]
            toc_table = Table(toc_table_data, colWidths=[215, 45, 235, 45])
            toc_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('ALIGN', (2, 0), (2, -1), 'LEFT'),
                ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('LEFTPADDING', (0, 0), (-1, -1), 2),
                ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                ('LINEBELOW', (0, 0), (-1, -1), 0.3, colors.HexColor("#EDF2F7"))
            ]))
            story.append(toc_table)
            story.append(Spacer(1, 10))

            # Skip the raw markdown TOC list items
            skip_md_toc = True
            i += 1
            continue

        if skip_md_toc:
            if raw_line.startswith('## '):
                skip_md_toc = False
            else:
                i += 1
                continue

        # Handle Markdown Tables
        if raw_line.startswith('|') and '|' in raw_line[1:]:
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i].strip())
                i += 1

            rows = []
            for tline in table_lines:
                if re.match(r'^\|[\s:\-\|]+\|$', tline):
                    continue
                cells = [c.strip() for c in tline.split('|')[1:-1]]
                rows.append(cells)

            if rows:
                table_data = []
                header_row = [Paragraph(clean_inline_md(c), table_header_style) for c in rows[0]]
                table_data.append(header_row)

                for r in rows[1:]:
                    data_row = [Paragraph(clean_inline_md(c), table_cell_style) for c in r]
                    table_data.append(data_row)

                num_cols = len(rows[0])
                available_width = 540 # pt
                col_width = available_width / num_cols if num_cols > 0 else 100

                t = Table(table_data, colWidths=[col_width]*num_cols)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), secondary_color),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ('LEFTPADDING', (0, 0), (-1, -1), 3),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 3),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")])
                ]))
                story.append(Spacer(1, 3))
                story.append(t)
                story.append(Spacer(1, 5))
            continue

        # Headers
        if raw_line.startswith('# '):
            story.append(Paragraph(clean_inline_md(raw_line[2:]), title_style))
        elif raw_line.startswith('## '):
            h_text = raw_line[3:].strip()
            # Insert bookmark before heading
            story.append(BookmarkFlowable(h_text))
            story.append(Paragraph(clean_inline_md(h_text), h1_style))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E0"), spaceBefore=1, spaceAfter=5))
        elif raw_line.startswith('### '):
            story.append(Paragraph(clean_inline_md(raw_line[4:]), h2_style))
        elif raw_line.startswith('#### '):
            story.append(Paragraph(clean_inline_md(raw_line[5:]), h3_style))
        elif raw_line.startswith('- ') or raw_line.startswith('* '):
            story.append(Paragraph(f"• {clean_inline_md(raw_line[2:])}", bullet_style))
        elif re.match(r'^\d+\.\s', raw_line):
            story.append(Paragraph(clean_inline_md(raw_line), bullet_style))
        elif raw_line == '---':
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E0"), spaceBefore=6, spaceAfter=6))
        else:
            story.append(Paragraph(clean_inline_md(raw_line), body_style))

        i += 1

    if in_callout and callout_lines:
        story.append(Paragraph(" ".join(callout_lines), callout_style))

    return story

def build_pdf():
    print(f"Reading markdown source from: {MD_PATH}")
    if not MD_PATH.exists():
        print(f"ERROR: File not found {MD_PATH}")
        return

    with open(MD_PATH, "r", encoding="utf-8") as f:
        md_text = f.read()

    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=44
    )

    # --- PASS 1: Build draft to record exact page numbers for each section ---
    print("Executing Pass 1: Recording section page numbers...")
    pass1_story = build_story(md_text, section_page_map)
    doc.build(pass1_story, canvasmaker=NumberedCanvas)
    print(f"Pass 1 complete. Recorded {len(section_page_map)} heading page locations.")

    # --- PASS 2: Build final document with populated Table of Contents ---
    print("Executing Pass 2: Generating final PDF with page-numbered Table of Contents...")
    pass2_story = build_story(md_text, section_page_map)
    doc.build(pass2_story, canvasmaker=NumberedCanvas)
    
    print(f"PDF successfully compiled at: {PDF_PATH}")
    print(f"File size: {os.path.getsize(PDF_PATH)} bytes")

if __name__ == "__main__":
    build_pdf()
