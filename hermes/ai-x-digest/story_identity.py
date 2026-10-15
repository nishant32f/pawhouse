"""Parse editorial-v2 identity and compare accepted Markdown revisions.

This module does not render Markdown or replace the editorial/source checker.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Optional


MARKER = re.compile(r"<!-- story-id: ([a-z0-9]+(?:-[a-z0-9]+)*) -->")
RESERVED = ("In brief", "Archived stories", "Navigation", "Backlinks")


class IdentityError(ValueError):
    pass


@dataclass(frozen=True)
class Story:
    story_id: str
    headline: str
    kind: str
    body: str
    correction: Optional[str] = None


@dataclass(frozen=True)
class Edition:
    format: Optional[str]
    original_text: str
    stories: tuple[Story, ...]

    @property
    def active_stories(self) -> tuple[Story, ...]:
        return tuple(story for story in self.stories if story.kind != "archived")

    @property
    def archived_stories(self) -> tuple[Story, ...]:
        return tuple(story for story in self.stories if story.kind == "archived")

    @property
    def lead(self) -> Optional[Story]:
        return next((story for story in self.stories if story.kind == "story"), None)


def _structure(lines: list[str]) -> list[str]:
    visible = []
    fence = None
    in_comment = False
    for line in lines:
        fence_match = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            if fence_match and fence_match[1][0] == fence[0] and len(fence_match[1]) >= len(fence) and not fence_match[2].strip():
                fence = None
            visible.append("")
            continue
        if fence_match and not in_comment:
            fence = fence_match[1]
            visible.append("")
            continue
        if not in_comment and line.startswith("<!-- story-id:"):
            visible.append(line)
            continue
        remaining = line
        result = ""
        while remaining:
            if in_comment:
                end = remaining.find("-->")
                if end < 0:
                    break
                remaining = remaining[end + 3:]
                in_comment = False
            else:
                start = remaining.find("<!--")
                if start < 0:
                    result += remaining
                    break
                result += remaining[:start]
                remaining = remaining[start + 4:]
                in_comment = True
        visible.append(result)
    return visible


def parse_edition(text: str) -> Edition:
    """Return unchanged legacy text, or ordered identified v2 story records.

    Raise IdentityError for invalid identity, archive, or section structure.
    Dates, prose targets, citations, and rendered link safety belong to callers.
    """
    frontmatter = re.match(r"\A---\n(.*?)\n---(?:\n|$)", text, re.S)
    if not frontmatter:
        raise IdentityError("missing edition frontmatter")
    formats = re.findall(r"^digest_format:\s*(.*?)\s*$", frontmatter[1], re.M)
    if len(formats) > 1:
        raise IdentityError("duplicate digest_format")
    version = formats[0].strip("\"'") if formats else None
    if version not in (None, "editorial-v1", "editorial-v2"):
        raise IdentityError(f"unsupported digest_format: {version}")
    if version != "editorial-v2":
        return Edition(version, text, ())

    lines = text[frontmatter.end():].splitlines()
    visible = _structure(lines)
    headings = []
    for index, line in enumerate(visible):
        heading = re.fullmatch(r"(#{2,3}) (\S.*?)\s*", line)
        if heading:
            headings.append((index, len(heading[1]), heading[2]))
    top = [(index, title) for index, level, title in headings if level == 2]
    if len(top) < 3 or [title for _, title in top[-2:]] != ["Navigation", "Backlinks"]:
        raise IdentityError("final sections must be Navigation then Backlinks")
    if top[0][1].casefold() in {title.casefold() for title in RESERVED}:
        raise IdentityError("edition must start with its lead story")
    if any(title == "Archived stories" for _, title in top) and top[-3][1] != "Archived stories":
        raise IdentityError("Archived stories must be the final content section")
    if any(line.strip() for line in visible[:top[0][0]]):
        raise IdentityError("edition must start with its lead story")
    for reserved in RESERVED:
        matches = [title for _, title in top if title.casefold() == reserved.casefold()]
        if any(title != reserved for title in matches) or len(matches) > 1:
            raise IdentityError(f"use one exact reserved heading: {reserved}")

    stories = []
    consumed_markers = set()

    def read_story(index: int, end: int, title: str, kind: str) -> None:
        if index + 1 >= end or not MARKER.fullmatch(lines[index + 1]):
            raise IdentityError(f"{title}: missing or unsafe story-id immediately after heading")
        story_id = MARKER.fullmatch(lines[index + 1])[1]
        if any(story.story_id == story_id for story in stories):
            raise IdentityError(f"duplicate story-id: {story_id}")
        consumed_markers.add(index + 1)
        body = "\n".join(lines[index + 2:end]).strip()
        correction = None
        if kind == "archived":
            paragraphs = re.split(r"\n\s*\n", body, maxsplit=1)
            if not paragraphs[0].startswith("Correction: ") or not paragraphs[0][12:].strip() or len(paragraphs) != 2:
                raise IdentityError(f"{story_id}: archived story requires a Correction paragraph and original prose")
            correction = paragraphs[0][12:].strip()
            body = paragraphs[1].strip()
        if not body:
            raise IdentityError(f"{story_id}: missing story prose")
        stories.append(Story(story_id, title, kind, body, correction))

    for position, (index, title) in enumerate(top):
        end = top[position + 1][0] if position + 1 < len(top) else len(lines)
        children = [(child, name) for child, level, name in headings if index < child < end and level == 3]
        if title in ("Navigation", "Backlinks"):
            continue
        if title in ("In brief", "Archived stories"):
            if not children or any(line.strip() for line in visible[index + 1:children[0][0]]):
                raise IdentityError(f"{title}: requires H3 records without introductory prose")
            kind = "brief" if title == "In brief" else "archived"
            for child_position, (child, name) in enumerate(children):
                child_end = children[child_position + 1][0] if child_position + 1 < len(children) else end
                read_story(child, child_end, name, kind)
        else:
            if children:
                raise IdentityError(f"{title}: H3 records belong under In brief or Archived stories")
            read_story(index, end, title, "story")
    for index, line in enumerate(visible):
        if line.startswith("<!-- story-id:") and index not in consumed_markers:
            raise IdentityError("story-id is not attached to a story heading")
    parsed = Edition(version, text, tuple(stories))
    if parsed.lead is None:
        raise IdentityError("editorial-v2 requires at least one full story")
    return parsed


def validate_revision(previous_text: str, current_text: str) -> Edition:
    """Keep every published v2 ID and preserve prose when archiving a story."""
    previous = parse_edition(previous_text)
    current = parse_edition(current_text)
    if previous.format != "editorial-v2":
        return current
    if current.format != "editorial-v2":
        raise IdentityError("cannot downgrade an identified editorial-v2 edition")
    current_by_id = {story.story_id: story for story in current.stories}
    for old_story in previous.stories:
        revised = current_by_id.get(old_story.story_id)
        if revised is None:
            raise IdentityError(f"removed story-id {old_story.story_id}; retain it in Archived stories with a correction")
        if revised.kind == "archived" and revised.body != old_story.body:
            raise IdentityError(f"{old_story.story_id}: archived prose and sources must match the previous revision")
    return current
