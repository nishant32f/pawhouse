#!/usr/bin/env python3
"""Verify Nishant's X-AI daily digest formatting conventions.

Usage:
  python verify-x-ai-digest-format.py /Users/skypawalker/Dropbox/Obsidian
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def display_stem(path: Path) -> str:
    # Public filenames are lowercase kebab-case; note titles/H1s keep the readable X-AI casing.
    return path.stem.upper().replace('X-AI-', 'X-AI-', 1)


def without_hidden_blocks(content: str) -> str:
    visible = re.sub(r'<!--.*?(?:-->|\Z)', '', content, flags=re.S)
    visible = re.sub(r'^ {0,3}(`{3,}|~{3,})[^\n]*\n.*?^ {0,3}\1[ \t]*$', '', visible, flags=re.M | re.S)
    return visible


def has_source_link(content: str) -> bool:
    visible = without_hidden_blocks(content)
    # Match links before code spans so a code-formatted link label remains valid.
    tokens = re.finditer(r'!?(\[[^\]\n]+\]\(https://[^\s)]+\))|(`+).*?\2', visible, re.S)
    return any(token.group(1) and not token.group().startswith('!') for token in tokens)


def check_editorial(text: str, expected_date: str) -> tuple[list[str], list[str]]:
    issues: list[str] = []
    warnings: list[str] = []
    body = re.sub(r'\A---\n.*?\n---\n', '', text, count=1, flags=re.S)
    body = without_hidden_blocks(body)
    if re.search(r'^#\s+', body, re.M):
        issues.append('duplicate H1; the website already displays the frontmatter title')
    if not re.search(rf'^date:\s*["\']?{re.escape(expected_date)}["\']?\s*$', text, re.M):
        issues.append('date does not match the daily filename')
    for token in ['Practical takeaway:', 'Signal quality:', '**Signal-quality note:',
                  '## Digest\n', '## Source provenance']:
        if token in body:
            issues.append(f'legacy boilerplate is not allowed in editorial-v1: {token.strip()}')

    matches = list(re.finditer(r'^##\s+(.+?)\s*$', body, re.M))
    if matches and body[:matches[0].start()].strip():
        issues.append('start with the lead story, without an introductory note')
    sections = [(m.group(1), body[m.end():matches[i + 1].start() if i + 1 < len(matches) else len(body)])
                for i, m in enumerate(matches)]
    reserved = {title.casefold(): title for title in ['In brief', 'Navigation', 'Backlinks', 'Source provenance', 'Digest']}
    for title, _ in sections:
        if title.casefold() in reserved and title != reserved[title.casefold()]:
            issues.append(f'use the reserved heading exactly: {reserved[title.casefold()]}')
    stories = [(title, content) for title, content in sections
               if title.casefold() not in reserved]
    if not 1 <= len(stories) <= 5:
        issues.append(f'story count must be 1 to 5, found {len(stories)}; do not pad quiet days')
    if len({title.lower() for title, _ in stories}) != len(stories):
        issues.append('duplicate story headlines')

    def check_story(title: str, content: str, brief: bool = False) -> None:
        if not has_source_link(content):
            issues.append(f'{title}: missing adjacent HTTPS source link')
        prose = re.sub(r'^Sources?:.*$', '', content, flags=re.M).strip()
        prose = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', prose)
        words = re.findall(r"\b[\w]+(?:[-'][\w]+)*\b", prose)
        maximum = 85 if brief else 220
        target_min, target_max = (30, 60) if brief else (100, 180)
        if not words:
            issues.append(f'{title}: empty story')
        elif len(words) > maximum:
            issues.append(f'{title}: {len(words)} words exceeds the {maximum}-word limit')
        elif not target_min <= len(words) <= target_max:
            warnings.append(f'{title}: {len(words)} words; target {target_min} to {target_max}, without filler')
        if not brief:
            first = re.split(r'\n\s*\n', prose)[0]
            summary_words = len(first.split())
            if summary_words > 60:
                issues.append(f'{title}: opening summary exceeds 60 words')
            elif not 25 <= summary_words <= 40:
                warnings.append(f'{title}: opening summary has {summary_words} words; target 25 to 40')

    for title, content in stories:
        check_story(title, content)
    brief_sections = [content for title, content in sections if title.casefold() == 'in brief']
    if len(brief_sections) > 1:
        issues.append('multiple In brief sections')
    for content in brief_sections:
        briefs = list(re.finditer(r'^###\s+(.+?)\s*$', content, re.M))
        if not 1 <= len(briefs) <= 3 or content[:briefs[0].start()].strip():
            issues.append('In brief must contain 1 to 3 short items with ### headlines')
        for i, item in enumerate(briefs):
            check_story(item.group(1), content[item.end():briefs[i + 1].start() if i + 1 < len(briefs) else len(content)], brief=True)
    return issues, warnings


def main() -> int:
    vault = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else Path('/Users/skypawalker/Dropbox/Obsidian')
    digests = vault / 'public' / 'digests'
    files = sorted(digests.glob('x-ai-????-??-??.md'))
    issues: list[str] = []
    warnings: list[str] = []

    if not digests.exists():
        issues.append(f'missing digest directory: {digests}')
    if not files:
        issues.append(f'no x-ai daily digest files found under: {digests}')

    forbidden = [
        'Clinical daily digest note',
        'Practical takeaway for a CTO/builder',
        '### Run metadata',
        '[[Obsidian Value Map]]',
        '[[obsidian-value-map]]',
    ]

    for path in files:
        text = path.read_text(encoding='utf-8')
        rel = path.relative_to(vault)
        expected_title = display_stem(path)
        frontmatter = re.match(r'\A---\n(.*?)\n---(?:\n|$)', text, re.S)
        version = re.search(r'^digest_format:\s*(.*?)\s*$', frontmatter.group(1), re.M) if frontmatter else None
        digest_format = version.group(1).strip('"\'') if version else None
        editorial = digest_format == 'editorial-v1'
        if digest_format is not None and not editorial:
            issues.append(f'{rel}: unsupported digest_format: {digest_format}')

        if path.name != path.name.lower() or ' ' in path.name:
            issues.append(f'{rel}: filename is not lowercase kebab-case')

        for token in forbidden:
            if token in text:
                issues.append(f'{rel}: forbidden text remains: {token}')

        if not text.startswith('---\n'):
            issues.append(f'{rel}: missing YAML frontmatter at top')
        if f'title: "{expected_title}"' not in text and f'title: {expected_title}' not in text:
            issues.append(f'{rel}: title does not match {expected_title}')
        if not editorial and f'# {expected_title}\n' not in text:
            issues.append(f'{rel}: H1 does not match {expected_title}')
        if re.search(rf'^# {re.escape(expected_title)}\n## ', text, flags=re.M):
            issues.append(f'{rel}: missing blank line after H1')

        headings = [m.group(1).strip() for m in re.finditer(r'^##\s+(.+?)\s*$', text, flags=re.M)]
        if len(headings) < 2 or headings[-2:] != ['Navigation', 'Backlinks']:
            issues.append(f'{rel}: final top-level sections are not Navigation then Backlinks: {headings[-4:]}')

        # Current generated notes should use this label; older imported sparse days may not have takeaways.
        if not editorial and path.name >= 'x-ai-2026-05-11.md' and '**Practical takeaway:**' not in text:
            issues.append(f'{rel}: no Practical takeaway labels found')
        if editorial:
            errors, notes = check_editorial(text, path.stem.removeprefix('x-ai-'))
            issues.extend(f'{rel}: {message}' for message in errors)
            warnings.extend(f'{rel}: {message}' for message in notes)
        m = re.match(r'x-ai-(\d{4})-(\d{2})-\d{2}\.md$', path.name)
        if m:
            year, month = m.group(1), m.group(2)
            if f'[[digests/x-ai-{year}|X-AI {year}]]' not in text:
                issues.append(f'{rel}: missing X-AI {year} backlink')
            if f'[[digests/x-ai-{year}-{month}|X-AI-{year}-{month}]]' not in text:
                issues.append(f'{rel}: missing X-AI-{year}-{month} monthly index backlink')
            if '[[index|Mindscape]]' not in text:
                issues.append(f'{rel}: missing public index backlink')

    print(f'checked {len(files)} x-ai daily digest files')
    for warning in warnings:
        print(f'warning: {warning}')
    if issues:
        print('issues:')
        for issue in issues:
            print(f'- {issue}')
        return 1
    print('ok')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
