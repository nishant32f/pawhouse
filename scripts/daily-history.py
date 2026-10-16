#!/usr/bin/env python3
"""Inventory pinned legacy sources, prepare backfill, read published history, and relocate accepted bytes.

Inventory never publishes. Backfill uses publication.py and its common lock. Relocation
is separate so activation can call relocate() while holding that same lock once.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
from publication import Publisher, ROOT, MISE, atomic, save, sha, run
from r2_publication import SOURCE, EDITION


def exact_copy(path, data):
    if path.is_symlink():
        raise ValueError('independent accepted copy cannot be a symlink: ' + str(path))
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError('destination has different bytes: ' + str(path))
    else:
        atomic(path, data)


def relocate(source, destination, backup, hashes, remove_source=False):
    """Caller owns the publication lock. Validate all collisions before copying or deletion."""
    source, destination, backup = [Path(path).resolve() for path in (source, destination, backup)]
    if any(a == b or a in b.parents or b in a.parents for a, b in ((source, destination), (source, backup), (destination, backup))):
        raise ValueError('source, destination and backup must be separate directories')
    accepted = {}
    for name, digest in hashes.items():
        if not SOURCE.fullmatch(name):
            raise ValueError('invalid digest source filename')
        available = source / name if (source / name).exists() else destination / name
        if sha(available) != digest:
            raise ValueError('source hash changed or missing: ' + name)
        accepted[name] = available.read_bytes()
        for directory in (destination, backup):
            path = directory / name
            if path.is_symlink():
                raise ValueError('independent accepted copy cannot be a symlink: ' + str(path))
            if path.exists() and sha(path) != digest:
                raise ValueError('destination has different bytes: ' + str(path))
    for name, data in accepted.items():
        exact_copy(backup / name, data)
        exact_copy(destination / name, data)
    for name, digest in hashes.items():
        if sha(backup / name) != digest or sha(destination / name) != digest:
            raise ValueError('relocation readback failed: ' + name)
    if remove_source:
        for name, digest in hashes.items():
            if (source / name).exists() and sha(source / name) != digest:
                raise ValueError('source changed before removal: ' + name)
        for name in hashes:
            (source / name).unlink(missing_ok=True)
    return {'schemaVersion': 1, 'sourceCount': len(hashes), 'sourceRemoved': remove_source, 'hashes': hashes}


def feed_identities(data):
    return {item.findtext('link'): {**{key: item.findtext(key) for key in ('link', 'guid', 'pubDate')},
                                                       'guidIsPermaLink': item.find('guid').get('isPermaLink') if item.find('guid') is not None else None}
            for item in ET.fromstring(data).findall('./channel/item')}


def inventory(legacy_sha, output, compiler_revision, rss=None):
    if not re.fullmatch('[a-f0-9]{40}', legacy_sha):
        raise ValueError('backfill requires an explicit full pinned legacy Git SHA')
    if not re.fullmatch('[a-f0-9]{40}', compiler_revision) or run(['git', 'rev-parse', 'HEAD'], ROOT) != compiler_revision:
        raise ValueError('compilerRevision must match current full HEAD')
    run(['git', 'diff', '--quiet', 'HEAD', '--', 'hermes/ai-x-digest/content'], ROOT)
    output = Path(output)
    if output.is_symlink():
        raise ValueError('inventory staging cannot be a symlink')
    output = output.resolve()
    for public in (ROOT.resolve(), Path('/Users/skypawalker/Dropbox/Obsidian').resolve()):
        if output == public or public in output.parents:
            raise ValueError('inventory staging must remain outside repository and vault')
    names = run(['git', 'ls-tree', '-r', '--name-only', legacy_sha, '--', 'content/digests'], ROOT).splitlines()
    sources = {}
    for path in names:
        name = Path(path).name
        if not SOURCE.fullmatch(name) or path != 'content/digests/' + name:
            raise ValueError('unexpected legacy digest source: ' + path)
        sources[name] = subprocess.check_output(['git', 'show', legacy_sha + ':' + path], cwd=ROOT)
    if not sources:
        raise ValueError('pinned legacy snapshot has no digest sources')
    if any(path.is_symlink() for path in output.rglob('*')):
        raise ValueError('inventory staging cannot contain symlinks')
    staged = output / 'sources'
    if staged.exists():
        if not staged.is_dir():
            raise ValueError('inventory sources must be a directory')
        for path in staged.iterdir():
            if path.name not in sources or not path.is_file():
                raise ValueError('unexpected staged source: ' + path.name)
    for name, data in sources.items():
        exact_copy(staged / name, data)
    inputs = [{'filename': name, 'text': data.decode('utf-8')} for name, data in sorted(sources.items())]
    with tempfile.TemporaryDirectory(prefix='daily-history-') as tmp:
        input_json = Path(tmp) / 'sources.json'
        input_json.write_text(json.dumps(inputs))
        old_urls = json.loads(run([MISE, 'exec', 'node@22.23.3', '--', 'node', '--import', 'tsx', ROOT / 'scripts/daily-history-urls.mjs', input_json], ROOT))
        compiled = json.loads(run([MISE, 'exec', 'node@22.23.3', '--', 'node', '--import', 'tsx', 'cli.ts', '--input-dir', output / 'sources', '--output-dir', Path(tmp) / 'bundle', '--compiler-revision', compiler_revision], ROOT / 'hermes/ai-x-digest/content'))
        for path in (Path(tmp) / 'bundle').rglob('*'):
            if path.is_file():
                exact_copy(output / 'bundle' / path.relative_to(Path(tmp) / 'bundle'), path.read_bytes())
        exact_copy(output / 'bundle/bundle.json', (json.dumps(compiled) + '\n').encode())
    manifest = compiled['manifest']
    feed = feed_identities((output / 'bundle' / manifest['rss']['key']).read_bytes())
    if rss:
        baseline = feed_identities(Path(rss).read_bytes())
        if baseline != feed:
            raise ValueError('compiled RSS identities differ from the supplied accepted feed')
    edition_refs = {entry['date']: entry for entry in manifest['editions']}
    records = []
    redirects = {route: '/archive/' for route in ('/digests', '/digests/', '/digests/index.html')}
    for old in old_urls:
        name = old['filename']
        day = name[5:15] if EDITION.fullmatch(name) else None
        target = '/editions/' + day + '/' if day else '/archive/'
        wire = json.loads((output / 'bundle' / edition_refs[day]['object']['key']).read_text()) if day else None
        variants = set()
        for slug in [old['canonicalSlug'], *old['aliasSlugs']]:
            base = '/' + slug.strip('/')
            if base.endswith('/index'):
                variants.update([base, base + '.html', base[:-5]])
            else:
                variants.update([base, base + '.html'])
        for route in variants:
            if route in redirects and redirects[route] != target:
                raise ValueError('legacy URL collision: ' + route)
            redirects[route] = target
        records.append({**old, 'kind': 'edition' if day else 'index', 'date': day,
                        'sourceSha256': hashlib.sha256(sources[name]).hexdigest(), 'byteLength': len(sources[name]),
                        'oldPaths': sorted(variants), 'target': target,
                        'rss': feed['https://daily.nishantkhurana.me' + target] if day else None,
                        'editionPath': wire['path'] if wire else None, 'readPath': wire['readPath'] if wire else None,
                        'readerAnchors': wire['anchors'] if wire else [],
                        'stories': [{'id': story['id'], 'path': story['path'], 'kind': story['kind'], 'sources': story['sources']} for story in wire.get('stories', [])] if wire else [],
                        'sources': wire['sources'] if wire else []})
    report = {'schemaVersion': 1, 'legacyRevision': legacy_sha, 'compilerRevision': compiler_revision,
              'publicationId': compiled['head']['manifest']['sha256'], 'editionCount': len(edition_refs),
              'indexCount': len(records) - len(edition_refs), 'sourceCount': len(records),
              'generatedIndexes': [{'oldPaths': ['/digests', '/digests/', '/digests/index.html'], 'target': '/archive/'}],
              'sources': records, 'redirects': [{'path': route, 'target': target} for route, target in sorted(redirects.items())]}
    exact_copy(output / 'inventory.json', (json.dumps(report, indent=2, sort_keys=True) + '\n').encode())
    return report


def backfill(owner, directory):
    """Caller holds owner.locked(); publish only the pinned, byte-checked inventory."""
    directory = Path(directory).resolve()
    report = json.loads((directory / 'inventory.json').read_text())
    if report.get('schemaVersion') != 1 or not re.fullmatch('[a-f0-9]{40}', report.get('legacyRevision', '')):
        raise ValueError('backfill requires a pinned legacy inventory')
    legacy_revision = report['legacyRevision']
    pinned = owner.git('ls-tree', '-r', '--name-only', legacy_revision, '--', 'content/digests').splitlines()
    if set(pinned) != {'content/digests/' + entry['filename'] for entry in report['sources']}:
        raise ValueError('inventory does not cover the complete pinned legacy source set')
    active = owner.r2()
    if not active:
        raise ValueError('backfill requires explicit R2 backend')
    files = {}
    for entry in report['sources']:
        name = entry['filename']
        source = directory / 'sources' / name
        if not SOURCE.fullmatch(name) or sha(source) != entry['sourceSha256']:
            raise ValueError('inventory source changed: ' + name)
        legacy_bytes = subprocess.check_output(['git', 'show', legacy_revision + ':content/digests/' + name], cwd=owner.repo)
        if source.read_bytes() != legacy_bytes:
            raise ValueError('inventory source differs from pinned legacy source: ' + name)
        files[name] = {'staged': str(source), 'stagedSha256': entry['sourceSha256'], 'beforeSha256': sha(active.sources / name)}
    request_path = directory / 'backfill-request.json'
    if not request_path.exists():
        current = active.transport('inspect')
        expected = {'manifestSha256': current['head']['manifest']['sha256'] if current['head'] else None, 'etag': current['etag']}
        if current['head']:
            raise ValueError('pinned legacy import is bootstrap only; resume its original request')
        save(request_path, {'schemaVersion': 2, 'backend': 'r2', 'kind': 'backfill',
                            'date': max(entry['date'] for entry in report['sources'] if entry['date']),
                            'compilerRevision': report['compilerRevision'], 'expected': expected, 'files': files})
    request = json.loads(request_path.read_text())
    if request.get('kind') != 'backfill' or request.get('expected') != {'manifestSha256': None, 'etag': None} or request.get('compilerRevision') != report['compilerRevision'] or set(request.get('files', {})) != set(files):
        raise ValueError('existing bootstrap request differs from pinned inventory')
    for name, entry in request['files'].items():
        if entry['stagedSha256'] != files[name]['stagedSha256'] or entry['staged'] != files[name]['staged']:
            raise ValueError('existing bootstrap request differs from pinned inventory')
    return active.digest(request_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    scan = commands.add_parser('inventory')
    scan.add_argument('--legacy-sha', required=True)
    scan.add_argument('--compiler-revision', required=True)
    scan.add_argument('--output', type=Path, required=True)
    scan.add_argument('--rss', type=Path)
    commands.add_parser('published')
    load = commands.add_parser('backfill')
    load.add_argument('--inventory-dir', type=Path, required=True)
    move = commands.add_parser('relocate')
    move.add_argument('--inventory', type=Path, required=True)
    move.add_argument('--source', type=Path, required=True)
    move.add_argument('--destination', type=Path, required=True)
    move.add_argument('--backup', type=Path, required=True)
    move.add_argument('--remove-source', action='store_true')
    args = parser.parse_args()
    if args.command == 'inventory':
        result = inventory(args.legacy_sha, args.output, args.compiler_revision, args.rss)
        print(json.dumps({key: result[key] for key in ('schemaVersion', 'publicationId', 'sourceCount', 'editionCount', 'indexCount')}))
        return
    owner = Publisher()
    with owner.locked():
        if args.command == 'published':
            active = owner.r2()
            if not active:
                raise ValueError('published history requires explicit R2 backend')
            result = active.published_history()
        elif args.command == 'backfill':
            result = backfill(owner, args.inventory_dir)
        else:
            report = json.loads(args.inventory.read_text())
            result = relocate(args.source, args.destination, args.backup,
                              {entry['filename']: entry['sourceSha256'] for entry in report['sources']}, args.remove_source)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError, OSError, KeyError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
