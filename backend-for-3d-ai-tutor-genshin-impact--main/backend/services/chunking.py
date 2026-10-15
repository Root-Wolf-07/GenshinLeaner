"""Text chunking service that maintains document hierarchy and location citations.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from backend.services.document_parser import ExtractedSection


@dataclass
class ProcessedChunk:
    chunk_id: str
    document_id: str
    owner_id: str
    chunk_index: int
    content: str
    page_number: Optional[int]
    slide_number: Optional[int]
    start_timestamp: Optional[float]
    end_timestamp: Optional[float]
    source_type: str
    token_count: int
    chunk_metadata: Dict[str, Any]


class TextChunker:
    """Chunks document sections with sentence-aware boundaries and overlap."""

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_sections(
        self,
        sections: List[ExtractedSection],
        document_id: str,
        owner_id: str,
        source_type: str,
    ) -> List[ProcessedChunk]:
        """Convert extracted sections into overlapping chunks with precise source coordinates."""
        all_chunks: List[ProcessedChunk] = []
        global_chunk_idx = 0

        for section in sections:
            section_text = section.text.strip()
            if not section_text:
                continue

            # If section fits within chunk_size, keep it whole
            if len(section_text) <= self.chunk_size:
                chunk_id = str(uuid.uuid4())
                words = section_text.split()
                all_chunks.append(
                    ProcessedChunk(
                        chunk_id=chunk_id,
                        document_id=document_id,
                        owner_id=owner_id,
                        chunk_index=global_chunk_idx,
                        content=section_text,
                        page_number=section.page_number,
                        slide_number=section.slide_number,
                        start_timestamp=section.start_timestamp,
                        end_timestamp=section.end_timestamp,
                        source_type=source_type,
                        token_count=max(1, len(words)),
                        chunk_metadata={
                            "section_title": section.section_title,
                            **section.metadata,
                        },
                    )
                )
                global_chunk_idx += 1
                continue

            # Split by sentences or paragraphs
            sentences = re.split(r"(?<=[.!?\n])\s+", section_text)
            current_buffer: List[str] = []
            current_len = 0

            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue

                if current_len + len(sentence) > self.chunk_size and current_buffer:
                    chunk_text = " ".join(current_buffer)
                    chunk_id = str(uuid.uuid4())
                    words = chunk_text.split()
                    all_chunks.append(
                        ProcessedChunk(
                            chunk_id=chunk_id,
                            document_id=document_id,
                            owner_id=owner_id,
                            chunk_index=global_chunk_idx,
                            content=chunk_text,
                            page_number=section.page_number,
                            slide_number=section.slide_number,
                            start_timestamp=section.start_timestamp,
                            end_timestamp=section.end_timestamp,
                            source_type=source_type,
                            token_count=max(1, len(words)),
                            chunk_metadata={
                                "section_title": section.section_title,
                                **section.metadata,
                            },
                        )
                    )
                    global_chunk_idx += 1

                    # Retain overlap from end of current_buffer
                    overlap_buffer: List[str] = []
                    overlap_len = 0
                    for s in reversed(current_buffer):
                        if overlap_len + len(s) <= self.chunk_overlap:
                            overlap_buffer.insert(0, s)
                            overlap_len += len(s)
                        else:
                            break
                    current_buffer = overlap_buffer
                    current_len = overlap_len

                current_buffer.append(sentence)
                current_len += len(sentence)

            # Flush remaining buffer
            if current_buffer:
                chunk_text = " ".join(current_buffer)
                chunk_id = str(uuid.uuid4())
                words = chunk_text.split()
                all_chunks.append(
                    ProcessedChunk(
                        chunk_id=chunk_id,
                        document_id=document_id,
                        owner_id=owner_id,
                        chunk_index=global_chunk_idx,
                        content=chunk_text,
                        page_number=section.page_number,
                        slide_number=section.slide_number,
                        start_timestamp=section.start_timestamp,
                        end_timestamp=section.end_timestamp,
                        source_type=source_type,
                        token_count=max(1, len(words)),
                        chunk_metadata={
                            "section_title": section.section_title,
                            **section.metadata,
                        },
                    )
                )
                global_chunk_idx += 1

        return all_chunks
