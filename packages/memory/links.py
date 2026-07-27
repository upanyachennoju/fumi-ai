import re
from pathlib import Path
import frontmatter

from packages.knowledge.vault import Vault


def add_relationship_link(content: str, target_stem: str, target_category_plural: str) -> str:
    """
    Appends or inserts an Obsidian wiki link under the appropriate related category heading.
    """
    content = content.rstrip()
    if f"[[{target_stem}]]" in content:
        return content

    heading = f"## related {target_category_plural}"
    link_str = f"- [[{target_stem}]]"

    lines = content.splitlines()
    heading_idx = -1
    for idx, line in enumerate(lines):
        if line.strip().lower() == heading.lower():
            heading_idx = idx
            break

    if heading_idx != -1:
        insert_idx = heading_idx + 1
        while insert_idx < len(lines) and not lines[insert_idx].strip():
            insert_idx += 1
        while insert_idx < len(lines) and (lines[insert_idx].strip().startswith("-") or lines[insert_idx].strip().startswith("*")):
            insert_idx += 1
        lines.insert(insert_idx, link_str)
        content = "\n".join(lines)
    else:
        if content:
            content += f"\n\n{heading}\n\n{link_str}"
        else:
            content = f"{heading}\n\n{link_str}"

    return content


class LinkBuilder:
    """
    Component responsible for creating/maintaining Obsidian wiki links between
    related memory files co-occurring in the same pipeline run.
    """

    def __init__(self, vault: Vault):
        self.vault = vault

    async def build_links(self, updated_paths: list[Path]):
        """
        Cross-links all files modified in the transaction to show mutual relationships.
        """
        if len(updated_paths) < 2:
            return

        # Load all updated posts
        items = []
        for path in updated_paths:
            if not path.exists():
                continue
            try:
                post = frontmatter.load(path)
                category = path.parent.name  # e.g., 'goals', 'projects'
                items.append({
                    "path": path,
                    "post": post,
                    "stem": path.stem,
                    "category": category
                })
            except Exception:
                continue

        # Cross-link all loaded items to each other
        for i, item_a in enumerate(items):
            modified = False
            for j, item_b in enumerate(items):
                if i == j:
                    continue

                # Add link from A to B using B's filename stem
                new_content = add_relationship_link(
                    item_a["post"].content,
                    item_b["stem"],
                    item_b["category"]
                )

                if new_content != item_a["post"].content:
                    item_a["post"].content = new_content
                    modified = True

            if modified:
                with open(item_a["path"], "w", encoding="utf-8") as f:
                    frontmatter.dump(item_a["post"], f)
