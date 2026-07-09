import re
from typing import Any, Dict, Tuple


class MarkdownParser:
    """Helper utilities to parse and clean markdown files for chunking."""

    @staticmethod
    def parse(content: str) -> Tuple[str, Dict[str, Any]]:
        """Parses markdown content, extracting frontmatter (if any) and raw text.

        Returns:
            Tuple of (clean_text, metadata_dict)
        """
        metadata: Dict[str, Any] = {}
        # Simple frontmatter extractor (yaml-like block at start of file between --- and ---)
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if match:
            frontmatter_text = match.group(1)
            # Basic parsing of key: value pairs
            for line in frontmatter_text.splitlines():
                if ":" in line:
                    key, val = line.split(":", 1)
                    metadata[key.strip()] = val.strip()
            # Strip the frontmatter from content
            content = content[match.end():]

        return content, metadata

    @staticmethod
    def strip_formatting(markdown_text: str) -> str:
        """Removes markdown formatting characters to get clean plain text."""
        # Remove headers
        text = re.sub(r"#+\s+", "", markdown_text)
        # Remove bold/italic markup
        text = re.sub(r"[\*_]{1,3}(.*?)[\*_]{1,3}", r"\1", text)
        # Remove links [text](url) -> text
        text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)
        # Remove code blocks
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        return text.strip()
