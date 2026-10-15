"""Document extraction service supporting PDF, PPTX, DOCX, TXT, and Markdown.
Preserves page numbers, slide numbers, and location metadata.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Check optional parser libraries
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    import docx  # python-docx
    HAS_PYTHON_DOCX = True
except ImportError:
    HAS_PYTHON_DOCX = False

try:
    import pptx  # python-pptx
    HAS_PYTHON_PPTX = True
except ImportError:
    HAS_PYTHON_PPTX = False


@dataclass
class ExtractedSection:
    text: str
    page_number: Optional[int] = None
    slide_number: Optional[int] = None
    start_timestamp: Optional[float] = None
    end_timestamp: Optional[float] = None
    section_title: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class ParseResult:
    sections: List[ExtractedSection]
    total_pages: int = 0
    total_slides: int = 0
    file_type: str = "txt"
    title: Optional[str] = None
    char_count: int = 0


class DocumentParser:
    """Parses various file types while strictly tracking source location metadata."""

    @staticmethod
    def parse(file_path: Path, file_type: str) -> ParseResult:
        """Parse file and return structured extracted sections."""
        ext = file_type.lower().strip(".")
        if ext == "pdf":
            return DocumentParser._parse_pdf(file_path)
        elif ext in ("pptx", "ppt"):
            return DocumentParser._parse_pptx(file_path)
        elif ext in ("docx", "doc"):
            return DocumentParser._parse_docx(file_path)
        elif ext in ("txt", "md", "markdown"):
            return DocumentParser._parse_text(file_path, ext)
        elif ext in ("vtt", "srt", "json"):
            return DocumentParser._parse_video_transcript(file_path, ext)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    @staticmethod
    def _parse_pdf(file_path: Path) -> ParseResult:
        sections: List[ExtractedSection] = []
        total_pages = 0
        char_count = 0

        if HAS_PYMUPDF:
            try:
                doc = fitz.open(str(file_path))
                total_pages = len(doc)
                for page_idx in range(total_pages):
                    page = doc[page_idx]
                    page_num = page_idx + 1
                    text = page.get_text("text").strip()
                    if text:
                        char_count += len(text)
                        sections.append(
                            ExtractedSection(
                                text=text,
                                page_number=page_num,
                                metadata={"page_num": page_num, "total_pages": total_pages},
                            )
                        )
                doc.close()
                return ParseResult(
                    sections=sections,
                    total_pages=total_pages,
                    file_type="pdf",
                    char_count=char_count,
                )
            except Exception as e:
                logger.error(f"PyMuPDF error parsing {file_path}: {e}")

        # Fallback text-based extraction for PDFs if PyMuPDF is not installed or errors
        try:
            raw_bytes = file_path.read_bytes()
            # Basic text stream extraction fallback
            text_matches = re.findall(rb"\((.*?)\)Tj", raw_bytes)
            fallback_text = "\n".join([m.decode("latin-1", errors="ignore") for m in text_matches if m.strip()])
            if not fallback_text.strip():
                # Try generic UTF-8 decode
                fallback_text = raw_bytes.decode("utf-8", errors="ignore")
                fallback_text = re.sub(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]", " ", fallback_text)

            clean_text = " ".join(fallback_text.split())
            if clean_text:
                sections.append(
                    ExtractedSection(
                        text=clean_text[:50000],
                        page_number=1,
                        metadata={"note": "Extracted via fallback binary decoder"},
                    )
                )
                total_pages = 1
                char_count = len(clean_text)
        except Exception as e:
            logger.error(f"Fallback PDF extractor error: {e}")

        return ParseResult(
            sections=sections,
            total_pages=total_pages or 1,
            file_type="pdf",
            char_count=char_count,
        )

    @staticmethod
    def _parse_pptx(file_path: Path) -> ParseResult:
        sections: List[ExtractedSection] = []
        total_slides = 0
        char_count = 0

        if HAS_PYTHON_PPTX:
            try:
                prs = pptx.Presentation(str(file_path))
                total_slides = len(prs.slides)
                for slide_idx, slide in enumerate(prs.slides):
                    slide_num = slide_idx + 1
                    slide_texts: List[str] = []
                    for shape in slide.shapes:
                        if shape.has_text_frame:
                            for paragraph in shape.text_frame.paragraphs:
                                line = paragraph.text.strip()
                                if line:
                                    slide_texts.append(line)
                    text = "\n".join(slide_texts).strip()
                    if text:
                        char_count += len(text)
                        sections.append(
                            ExtractedSection(
                                text=text,
                                slide_number=slide_num,
                                metadata={"slide_num": slide_num, "total_slides": total_slides},
                            )
                        )
                return ParseResult(
                    sections=sections,
                    total_slides=total_slides,
                    file_type="pptx",
                    char_count=char_count,
                )
            except Exception as e:
                logger.error(f"python-pptx error parsing {file_path}: {e}")

        # Fallback for PPTX
        raw = file_path.read_text(errors="ignore")
        clean_text = " ".join(raw.split())
        sections.append(ExtractedSection(text=clean_text[:20000], slide_number=1))
        return ParseResult(sections=sections, total_slides=1, file_type="pptx", char_count=len(clean_text))

    @staticmethod
    def _parse_docx(file_path: Path) -> ParseResult:
        sections: List[ExtractedSection] = []
        char_count = 0

        if HAS_PYTHON_DOCX:
            try:
                doc = docx.Document(str(file_path))
                current_heading = "General"
                current_paragraphs: List[str] = []
                page_estimate = 1
                words_on_page = 0

                for p in doc.paragraphs:
                    line = p.text.strip()
                    if not line:
                        continue
                    if p.style and p.style.name.startswith("Heading"):
                        if current_paragraphs:
                            body = "\n".join(current_paragraphs)
                            char_count += len(body)
                            sections.append(
                                ExtractedSection(
                                    text=body,
                                    page_number=page_estimate,
                                    section_title=current_heading,
                                )
                            )
                            current_paragraphs = []
                        current_heading = line

                    current_paragraphs.append(line)
                    words_on_page += len(line.split())
                    if words_on_page >= 350:  # standard words per page estimate
                        page_estimate += 1
                        words_on_page = 0

                if current_paragraphs:
                    body = "\n".join(current_paragraphs)
                    char_count += len(body)
                    sections.append(
                        ExtractedSection(
                            text=body,
                            page_number=page_estimate,
                            section_title=current_heading,
                        )
                    )

                return ParseResult(
                    sections=sections,
                    total_pages=page_estimate,
                    file_type="docx",
                    char_count=char_count,
                )
            except Exception as e:
                logger.error(f"python-docx error parsing {file_path}: {e}")

        # Fallback for DOCX
        raw = file_path.read_text(errors="ignore")
        clean_text = " ".join(raw.split())
        sections.append(ExtractedSection(text=clean_text[:20000], page_number=1))
        return ParseResult(sections=sections, total_pages=1, file_type="docx", char_count=len(clean_text))

    @staticmethod
    def _parse_text(file_path: Path, ext: str) -> ParseResult:
        content = file_path.read_text(encoding="utf-8", errors="replace")
        sections: List[ExtractedSection] = []

        # Split Markdown by headers (# or ##) or paragraphs
        chunks = re.split(r"(?m)^(?=#{1,3}\s+)", content)
        page_estimate = 1
        char_count = 0

        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue
            char_count += len(chunk)
            lines = chunk.splitlines()
            title = lines[0].lstrip("#").strip() if lines and lines[0].startswith("#") else None
            sections.append(
                ExtractedSection(
                    text=chunk,
                    page_number=page_estimate,
                    section_title=title,
                )
            )
            # Estimate 1800 characters per page
            if len(chunk) > 1800:
                page_estimate += len(chunk) // 1800

        if not sections and content.strip():
            sections.append(ExtractedSection(text=content.strip(), page_number=1))
            char_count = len(content.strip())

        return ParseResult(
            sections=sections,
            total_pages=page_estimate,
            file_type=ext,
            char_count=char_count,
        )

    @staticmethod
    def _parse_video_transcript(file_path: Path, ext: str) -> ParseResult:
        """Parse video and audio subtitle/transcript files (.vtt, .srt, .json) preserving exact timestamps."""
        sections: List[ExtractedSection] = []
        raw_text = file_path.read_text(encoding="utf-8", errors="replace")
        char_count = 0

        def _time_to_seconds(h_str: Optional[str], m_str: str, s_str: str, ms_str: str) -> float:
            hours = float(h_str.rstrip(":")) if h_str else 0.0
            minutes = float(m_str)
            seconds = float(s_str)
            ms = float(ms_str) / (1000.0 if len(ms_str) == 3 else 100.0)
            return hours * 3600.0 + minutes * 60.0 + seconds + ms

        if ext == "json":
            import json
            try:
                data = json.loads(raw_text)
                items = data if isinstance(data, list) else data.get("segments", data.get("transcript", []))
                for idx, item in enumerate(items, 1):
                    t_text = item.get("text", "").strip()
                    if not t_text:
                        continue
                    start_s = float(item.get("start", item.get("timestamp_start", 0.0)))
                    end_s = float(item.get("end", item.get("timestamp_end", start_s + 5.0)))
                    char_count += len(t_text)

                    s_min, s_sec = int(start_s // 60), int(start_s % 60)
                    e_min, e_sec = int(end_s // 60), int(end_s % 60)
                    title = f"Video Interval [{s_min:02d}:{s_sec:02d} - {e_min:02d}:{e_sec:02d}]"

                    sections.append(
                        ExtractedSection(
                            text=t_text,
                            page_number=idx,
                            start_timestamp=start_s,
                            end_timestamp=end_s,
                            section_title=title,
                            metadata={"interval": f"{s_min:02d}:{s_sec:02d} - {e_min:02d}:{e_sec:02d}"},
                        )
                    )
            except Exception as e:
                logger.warning(f"JSON video transcript parse warning: {e}")

        # VTT or SRT regex matching
        if not sections and ext in ("vtt", "srt"):
            # Match 00:01:20.000 --> 00:01:25.000 or 01:20,000 --> 01:25,000
            pattern = re.compile(
                r"(?:(\d{1,2}:)?(\d{2}):(\d{2})[.,](\d{2,3}))\s*-->\s*(?:(\d{1,2}:)?(\d{2}):(\d{2})[.,](\d{2,3}))"
            )
            lines = raw_text.splitlines()
            current_start: Optional[float] = None
            current_end: Optional[float] = None
            current_lines: List[str] = []

            for line in lines:
                line_str = line.strip()
                if not line_str or line_str.isdigit() or line_str.upper() == "WEBVTT":
                    continue

                m = pattern.search(line_str)
                if m:
                    # Flush previous if exceeded 40 seconds or 400 characters
                    if current_lines and current_start is not None and current_end is not None:
                        if (current_end - current_start >= 40.0) or len(" ".join(current_lines)) >= 400:
                            chunk_t = " ".join(current_lines)
                            char_count += len(chunk_t)
                            s_m, s_s = int(current_start // 60), int(current_start % 60)
                            e_m, e_s = int(current_end // 60), int(current_end % 60)
                            sections.append(
                                ExtractedSection(
                                    text=chunk_t,
                                    page_number=len(sections) + 1,
                                    start_timestamp=current_start,
                                    end_timestamp=current_end,
                                    section_title=f"Video Clip [{s_m:02d}:{s_s:02d} - {e_m:02d}:{e_s:02d}]",
                                    metadata={"video_timestamp": f"{s_m:02d}:{s_s:02d}"},
                                )
                            )
                            current_lines = []
                            current_start = None

                    h1, m1, s1, ms1, h2, m2, s2, ms2 = m.groups()
                    start_sec = _time_to_seconds(h1, m1, s1, ms1)
                    end_sec = _time_to_seconds(h2, m2, s2, ms2)
                    if current_start is None:
                        current_start = start_sec
                    current_end = end_sec
                else:
                    if current_start is not None:
                        current_lines.append(line_str)

            # Flush trailing
            if current_lines and current_start is not None:
                chunk_t = " ".join(current_lines)
                char_count += len(chunk_t)
                end_sec = current_end or (current_start + 10.0)
                s_m, s_s = int(current_start // 60), int(current_start % 60)
                e_m, e_s = int(end_sec // 60), int(end_sec % 60)
                sections.append(
                    ExtractedSection(
                        text=chunk_t,
                        page_number=len(sections) + 1,
                        start_timestamp=current_start,
                        end_timestamp=end_sec,
                        section_title=f"Video Clip [{s_m:02d}:{s_s:02d} - {e_m:02d}:{e_s:02d}]",
                        metadata={"video_timestamp": f"{s_m:02d}:{s_s:02d}"},
                    )
                )

        if not sections and raw_text.strip():
            sections.append(
                ExtractedSection(
                    text=raw_text.strip()[:10000],
                    page_number=1,
                    start_timestamp=0.0,
                    end_timestamp=60.0,
                    section_title="Video Transcript Overview",
                )
            )
            char_count = len(raw_text.strip())

        return ParseResult(
            sections=sections,
            total_pages=max(1, len(sections)),
            file_type="video_transcript",
            char_count=char_count,
        )
