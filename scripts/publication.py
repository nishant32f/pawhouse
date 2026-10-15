#!/usr/bin/env python3
"""Serialize vault publication and keep private accepted-revision receipts.

Only the digest command promotes declared paths. Ordinary notes retain full sync.
All entry points share this lock and recover the preceding promotion first.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import date
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MISE = shutil.which('mise') or '/opt/homebrew/bin/mise'
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'hermes/ai-x-digest'))
from story_identity import validate_revision, parse_edition


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def atomic(path, data, temporary=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if temporary is None:
        descriptor, temporary = tempfile.mkstemp(prefix='.' + path.name + '-', dir=path.parent)
    else:
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
    # The journal must survive a process or host interruption before promotion.
    descriptor = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def save(path, value):
    atomic(path, (json.dumps(value, indent=2, sort_keys=True) + '\n').encode())


def run(args, cwd=None):
    result = subprocess.run([str(arg) for arg in args], cwd=cwd, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f'command failed: {args[0]}')
    return result.stdout.strip()


class Publisher:
    def __init__(self):
        self.repo = Path(os.environ.get('PUBLISH_REPO', ROOT)).resolve()
        self.vault = Path(os.environ.get('PUBLISH_VAULT_PUBLIC', '/Users/skypawalker/Dropbox/Obsidian/public')).resolve()
        self.content = self.repo / 'content'
        self.state = Path(os.environ.get('PUBLISH_STATE_DIR', '~/.local/state/pawhouse-publication')).expanduser().resolve()
        for public in (self.repo, self.vault):
            if self.state == public or public in self.state.parents:
                raise ValueError('publication state must stay outside the repository and public vault')
        self.state.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.state, 0o700)
        self.journal = self.state / 'promotion.json'

    def git(self, *args):
        return run(['git', '-C', self.repo, *args])

    @contextmanager
    def locked(self):
        with (self.state / 'host.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            self.recover()
            yield

    def recover(self):
        if not self.journal.exists():
            return
        journal = json.loads(self.journal.read_text())
        head = self.git('rev-parse', 'HEAD')
        paths = ['content/' + path for path in journal['files']]
        for item in journal['targets']:
            target = Path(item['target']).resolve()
            relative = target.relative_to(self.vault if self.vault in target.parents else self.content).as_posix()
            original = sha(Path(item['backup'])) if item['backup'] else None
            candidate = journal['files'].get(relative)
            if sha(target) not in (original, candidate):
                raise RuntimeError(f'interrupted promotion target has a manual edit: {target}')
        for item in journal['targets']:
            if item.get('temporary'):
                Path(item['temporary']).unlink(missing_ok=True)
        committed = False
        if journal['files'] and head != journal['expected_head']:
            parents = self.git('rev-list', '--parents', '-n', '1', head).split()[1:]
            changed = self.git('diff', '--name-only', journal['expected_head'], head).splitlines()
            committed = (parents == [journal['expected_head']] and set(changed) <= set(paths)
                         and all(hashlib.sha256(subprocess.check_output(['git', '-C', str(self.repo), 'show', head + ':content/' + path])).hexdigest() == digest
                                 for path, digest in journal['files'].items()))
            if not committed:
                raise RuntimeError('interrupted promotion has an unexpected Git revision; resolve before publishing')
        if committed:
            receipt_path = Path(journal['receipt'])
            receipt = json.loads(receipt_path.read_text())
            receipt.update(phase='committed', commit=head)
            save(receipt_path, receipt)
        else:
            for item in journal['targets']:
                target = Path(item['target'])
                if item['backup'] is None:
                    target.unlink(missing_ok=True)
                else:
                    atomic(target, Path(item['backup']).read_bytes(), item.get('temporary'))
            if paths:
                self.git('reset', '--quiet', 'HEAD', '--', *paths)
            if journal['receipt']:
                receipt_path = Path(journal['receipt'])
                receipt = json.loads(receipt_path.read_text())
                receipt['phase'] = 'accepted'
                save(receipt_path, receipt)
        self.journal.unlink()

    def request(self, filename):
        filename = Path(filename).resolve()
        if any(public == filename or public in filename.parents for public in (self.repo, self.vault)):
            raise ValueError('accepted request must remain private, outside repository and public vault')
        request = json.loads(filename.read_text())
        day = date.fromisoformat(request['date']).isoformat()
        if not re.fullmatch(r'[0-9a-f]{40}', request['expected_head']):
            raise ValueError('expected_head must be a full Git SHA')
        edition = f'digests/x-ai-{day}.md'
        allowed = {edition, f'digests/x-ai-{day[:7]}.md', f'digests/x-ai-{day[:4]}.md'}
        previous = self.git('ls-tree', '-r', '--name-only', request['expected_head'], '--', 'content/digests').splitlines()
        previous = sorted(path.removeprefix('content/') for path in previous
                          if re.fullmatch(r'content/digests/x-ai-\d{4}-\d{2}-\d{2}\.md', path) and path < 'content/' + edition)
        if previous:
            allowed.add(previous[-1])
        if edition not in request['files'] or not set(request['files']) <= allowed:
            raise ValueError('only the edition, its month/year indexes, and previous daily navigation may be declared')
        identity = hashlib.sha256(json.dumps(request, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        return request, self.state / 'receipts' / (identity + '.json')

    def clean(self):
        if self.git('branch', '--show-current') != 'main':
            raise RuntimeError('digest publication requires the canonical main checkout')
        if self.git('status', '--porcelain', '--untracked-files=all'):
            raise RuntimeError('repository has unrelated or uncommitted changes')

    def inventory(self, root):
        result = {}
        for path in root.rglob('*'):
            relative = path.relative_to(root)
            if any(part in ('.DS_Store', '.obsidian', '.git') for part in relative.parts):
                continue
            if path.is_symlink():
                raise ValueError(f'public tree contains a symlink: {relative}')
            if path.is_file():
                result[relative.as_posix()] = sha(path)
        return result

    def validate(self, request):
        self.clean()
        if self.git('rev-parse', 'HEAD') != request['expected_head']:
            raise RuntimeError('source revision changed since acceptance')
        if self.inventory(self.vault) != self.inventory(self.content):
            raise RuntimeError('vault contains changes outside the accepted staged revision')
        day = request['date']
        edition = f'digests/x-ai-{day}.md'
        accepted = {}
        for relative, entry in request['files'].items():
            staged = Path(entry['staged']).resolve()
            if any(public == staged or public in staged.parents for public in (self.repo, self.vault)):
                raise ValueError('staged accepted files must remain outside repository and public vault')
            for base in (self.vault, self.content):
                if sha(base / relative) != entry['before_sha256']:
                    raise RuntimeError(f'accepted base hash changed: {relative}')
            data = staged.read_bytes()
            if hashlib.sha256(data).hexdigest() != entry['staged_sha256']:
                raise RuntimeError(f'staged accepted hash changed: {relative}')
            accepted[relative] = data
        candidate = accepted[edition].decode('utf-8')
        previous = self.content / edition
        previous_text = previous.read_text() if previous.exists() else None
        if previous_text is not None:
            validate_revision(previous_text, candidate)
        else:
            parse_edition(candidate)
        with tempfile.TemporaryDirectory(prefix='pawhouse-validate-', dir=self.state) as temporary:
            private_vault = Path(temporary)
            staged_path = private_vault / 'public' / edition
            staged_path.parent.mkdir(parents=True)
            staged_path.write_bytes(accepted[edition])
            checker = ROOT / 'hermes/ai-x-digest/runtime/skills/note-taking/obsidian/scripts/verify-x-ai-digest-format.py'
            run([sys.executable, checker, private_vault])
            validation = [MISE, 'exec', 'node@22.23.3', '--', 'node', '--import', 'tsx', 'scripts/validate-edition.ts', staged_path]
            if previous_text is not None:
                previous_path = private_vault / 'previous' / staged_path.name
                previous_path.parent.mkdir()
                previous_path.write_text(previous_text)
                validation.append(previous_path)
            run(validation, ROOT / 'apps/daily')
        for relative, data in accepted.items():
            if re.fullmatch(r'digests/x-ai-\d{4}-\d{2}-\d{2}\.md', relative) and relative != edition:
                old = (self.content / relative).read_text()
                updated = re.sub(r'^- Next:.*$', f'- Next: [[digests/x-ai-{day}|X-AI-{day}]]', old, flags=re.M)
                if data.decode() != updated:
                    raise ValueError('previous edition may change only its Next navigation link')
        return accepted

    def digest(self, filename):
        request, receipt_path = self.request(filename)
        receipt = json.loads(receipt_path.read_text()) if receipt_path.exists() else None
        if receipt and receipt['phase'] == 'deliverypending':
            raise RuntimeError('delivery result is ambiguous; resolve it explicitly before retrying')
        if receipt and receipt.get('commit'):
            if receipt['phase'] == 'complete':
                return receipt
            self.push(receipt_path, receipt)
            return receipt
        accepted = self.validate(request)
        receipt = {'date': request['date'], 'expected_head': request['expected_head'], 'phase': 'accepted',
                   'files': {path: hashlib.sha256(data).hexdigest() for path, data in accepted.items()},
                   'main': {'status': 'pending'}}
        save(receipt_path, receipt)
        backups = self.state / 'backups' / receipt_path.stem
        backups.mkdir(parents=True, exist_ok=True)
        targets = []
        for base in (self.vault, self.content):
            for relative in accepted:
                target = base / relative
                backup = backups / str(len(targets)) if target.exists() else None
                if backup:
                    atomic(backup, target.read_bytes())
                targets.append({'target': str(target), 'backup': str(backup) if backup else None,
                                'temporary': str(target.with_name('.' + target.name + '.pawhouse-' + uuid.uuid4().hex))})
        save(self.journal, {'targets': targets, 'expected_head': request['expected_head'],
                            'files': receipt['files'], 'receipt': str(receipt_path)})
        for item in targets:
            target = Path(item['target'])
            relative = target.relative_to(self.vault if self.vault in target.parents else self.content).as_posix()
            atomic(target, accepted[relative], item['temporary'])
        receipt['phase'] = 'promoted'
        save(receipt_path, receipt)
        paths = ['content/' + relative for relative in accepted]
        self.git('add', '--', *paths)
        if self.git('diff', '--cached', '--name-only'):
            self.git('commit', '-m', f'Publish AI digest {request["date"]}', '--', *paths)
        receipt.update(phase='committed', commit=self.git('rev-parse', 'HEAD'))
        save(receipt_path, receipt)
        self.journal.unlink()
        self.push(receipt_path, receipt)
        return receipt

    def push(self, receipt_path, receipt):
        self.clean()
        self.git('merge-base', '--is-ancestor', receipt['commit'], 'HEAD')
        remote = self.git('ls-remote', 'origin', 'refs/heads/main').split()
        contained = False
        if remote:
            remote_head = remote[0]
            self.git('fetch', '--quiet', 'origin', 'main')
            contained = subprocess.run(['git', '-C', str(self.repo), 'merge-base', '--is-ancestor',
                                        receipt['commit'], remote_head], capture_output=True).returncode == 0
        if not contained:
            self.git('push', 'origin', receipt['commit'] + ':refs/heads/main')
        if receipt['phase'] == 'committed':
            receipt['phase'] = 'readerpending'
        receipt.pop('error', None)
        save(receipt_path, receipt)

    def sync(self):
        self.content.mkdir(parents=True, exist_ok=True)
        run(['rsync', '-a', '--delete', '--exclude', '.DS_Store', '--exclude', '.obsidian', '--exclude', '.git',
             str(self.vault) + '/', str(self.content) + '/'])

    def notes(self, message):
        branch = self.git('branch', '--show-current')
        self.sync()
        run([MISE, 'x', 'node@22.16.0', '--', 'npx', 'quartz', 'build'], self.repo)
        self.git('add', '-A')
        if self.git('diff', '--cached', '--name-only'):
            self.git('commit', '-m', message)
            self.git('push', 'origin', branch)
        return {'branch': branch}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('digest', 'delivery-begin', 'delivery-complete', 'delivery-resolve', 'main-result'):
        command = sub.add_parser(name)
        command.add_argument('--request', required=True)
        if name in ('delivery-complete', 'delivery-resolve'):
            command.add_argument('--reference', required=True)
        if name == 'delivery-resolve':
            command.add_argument('--outcome', choices=['delivered', 'not-delivered'], required=True)
        if name == 'main-result':
            command.add_argument('--status', choices=['pending', 'verified', 'failed'], required=True)
            command.add_argument('--reference', required=True)
    sub.add_parser('sync')
    sub.add_parser('recover')
    notes = sub.add_parser('notes')
    notes.add_argument('--message', default='Update content')
    args = parser.parse_args()
    publisher = Publisher()
    with publisher.locked():
        if args.command == 'digest':
            result = publisher.digest(args.request)
        elif args.command == 'notes':
            result = publisher.notes(args.message)
        elif args.command == 'sync':
            publisher.sync()
            result = {'synced': True}
        elif args.command == 'recover':
            result = {'recovered': True}
        else:
            _, receipt_path = publisher.request(args.request)
            result = json.loads(receipt_path.read_text())
            if args.command == 'delivery-begin':
                if result['phase'] != 'readerverified':
                    raise ValueError('dated delivery requires readerverified; ambiguous delivery requires manual resolution')
                result['phase'] = 'deliverypending'
            elif args.command == 'delivery-complete':
                if result['phase'] != 'deliverypending':
                    raise ValueError('no pending delivery')
                result.update(phase='complete', delivery_reference=args.reference)
            elif args.command == 'delivery-resolve':
                if result['phase'] != 'deliverypending':
                    raise ValueError('no ambiguous delivery to resolve')
                result.update(phase='complete' if args.outcome == 'delivered' else 'readerverified', delivery_reference=args.reference)
            elif args.command == 'main-result':
                result['main'] = {'status': args.status, 'reference': args.reference}
            save(receipt_path, result)
        print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError, OSError, KeyError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
