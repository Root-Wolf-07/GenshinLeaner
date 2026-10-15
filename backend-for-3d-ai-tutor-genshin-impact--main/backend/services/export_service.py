"""Study Material Export Service.
Formats study notes, revision sheets, and flashcards for Markdown, Plain Text, and HTML export.
"""

from __future__ import annotations

import html
import re
from typing import Dict
from backend.models.material import StudyMaterial


class ExportService:
    """Exports StudyMaterial into requested output formats."""

    @staticmethod
    def export(material: StudyMaterial, export_format: str) -> Dict[str, str]:
        """Convert material into requested format and generate filename."""
        fmt = export_format.lower()
        clean_topic = re.sub(r"[^\w\-]", "_", material.topic.lower())

        if fmt == "markdown":
            filename = f"{clean_topic}_{material.material_type}.md"
            content = material.raw_markdown

        elif fmt == "txt":
            filename = f"{clean_topic}_{material.material_type}.txt"
            # Strip markdown headers and fences for plain text
            plain = re.sub(r"^#+\s*", "", material.raw_markdown, flags=re.MULTILINE)
            plain = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", plain)
            plain = re.sub(r"\${1,2}([^$]+)\${1,2}", r"\1", plain)
            content = plain

        elif fmt == "html":
            filename = f"{clean_topic}_{material.material_type}.html"
            # Wrap rendered markdown into clean standalone HTML template
            escaped_md = html.escape(material.raw_markdown)
            content = (
                f"<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
                f"<meta charset=\"UTF-8\">\n<title>{html.escape(material.title)}</title>\n"
                f"<link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css\">\n"
                f"<style>\n"
                f"body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; max-width: 800px; margin: 40px auto; padding: 0 20px; color: #2e3440; background: #eceff4; }}\n"
                f"article {{ background: #ffffff; padding: 40px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}\n"
                f"h1, h2, h3 {{ color: #5e81ac; }}\n"
                f"pre {{ background: #f8f9fa; padding: 16px; border-radius: 8px; overflow-x: auto; white-space: pre-wrap; font-family: inherit; }}\n"
                f"</style>\n</head>\n<body>\n<article>\n<pre>{escaped_md}</pre>\n</article>\n</body>\n</html>"
            )
        else:
            raise ValueError(f"Unsupported export format: {export_format}")

        return {
            "material_id": material.id,
            "format": fmt,
            "filename": filename,
            "content": content,
        }


# Global instance
export_service = ExportService()
