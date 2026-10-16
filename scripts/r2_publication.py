"""Private accepted-source publication. The explicit backend switch owns activation."""
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

EDITION = re.compile(r'x-ai-\d{4}-\d{2}-\d{2}\.md')
SOURCE = re.compile(r'x-ai-\d{4}(?:-\d{2}(?:-\d{2})?)?\.md')
PHASES = ('accepted', 'source-promoted', 'objects-verified', 'published', 'readerverified', 'deliverypending', 'complete')


class R2Publisher:
    def __init__(self, owner, backend):
        self.owner = owner
        self.state = owner.state
        self.root = Path(backend['vaultRoot']).expanduser().resolve()
        self.sources = self.root / 'digests'
        configured = Path(backend['configPath']).expanduser().absolute()
        if configured.is_symlink():
            raise ValueError('private S3 configuration cannot be a symlink')
        self.config = configured.resolve()
        for path in (self.state, self.config):
            if any(path == public or public in path.parents for public in (owner.repo, owner.vault, self.root)):
                raise ValueError('R2 state and credentials must stay outside repository and vault')
        if self.root == owner.repo or owner.repo in self.root.parents or self.sources == owner.vault / 'digests':
            raise ValueError('R2 accepted sources must use a private vault root')
        for receipt_path in (self.state / 'receipts').glob('*.json'):
            receipt = json.loads(receipt_path.read_text())
            if receipt.get('schemaVersion') != 2 and receipt.get('phase') != 'complete':
                raise RuntimeError('unresolved legacy publication receipt blocks R2 activation')
        if owner.journal.exists():
            raise RuntimeError('legacy promotion journal blocks R2 activation')
        self.package = owner.repo / 'hermes/ai-x-digest/content'
        self.journal = self.state / 'r2-promotion.json'

    def save(self, path, value):
        from publication import save
        save(path, value)

    def atomic(self, path, data):
        from publication import atomic
        atomic(path, data)

    def sha(self, path):
        from publication import sha
        return sha(path)

    def node(self, script, *args):
        from publication import MISE, run
        return run([MISE, 'exec', 'node@22.23.3', '--', 'node', '--import', 'tsx', script, *args], self.package)

    def transport(self, action, *args):
        import subprocess
        from publication import MISE
        result = subprocess.run([MISE, 'exec', 'node@22.23.3', '--', 'node', '--import', 'tsx', 'r2-cli.ts', action, *map(str, args)],
                                cwd=self.package, env=dict(os.environ, PUBLISH_R2_CONFIG=str(self.config), PUBLISH_R2_VAULT_ROOT=str(self.root)), capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError('R2 transport failed: ' + (result.stderr.strip() or 'unknown error'))
        return json.loads(result.stdout)

    def private(self, path):
        path = Path(path).expanduser().resolve()
        if any(path == public or public in path.parents for public in (self.owner.repo, self.owner.vault, self.root)):
            raise ValueError('accepted requests and staged files must remain outside repository and vault')
        return path

    def request(self, filename):
        filename = self.private(filename)
        request = json.loads(filename.read_text())
        if request.get('schemaVersion') != 2 or request.get('backend') != 'r2' or 'expected_head' in request:
            raise ValueError('R2 backend requires a version 2 R2 request; legacy Git requests are rejected')
        if set(request) != {'schemaVersion', 'backend', 'kind', 'date', 'compilerRevision', 'expected', 'files'}:
            raise ValueError('unsupported R2 request fields')
        day = date.fromisoformat(request['date']).isoformat()
        if request['kind'] not in ('scheduled', 'correction', 'backfill'):
            raise ValueError('invalid publication kind')
        expected = request['expected']
        if set(expected) != {'manifestSha256', 'etag'}:
            raise ValueError('expected manifest and ETag are required')
        if expected['manifestSha256'] is None:
            if expected['etag'] is not None or request['kind'] != 'backfill':
                raise ValueError('bootstrap requires an explicit backfill and absent head')
        elif not re.fullmatch('[a-f0-9]{64}', expected['manifestSha256']) or not isinstance(expected['etag'], str) or not expected['etag']:
            raise ValueError('invalid expected publication')
        if not re.fullmatch('[a-f0-9]{40}', request['compilerRevision']):
            raise ValueError('compilerRevision must be a full code revision')
        files = request['files']
        if not isinstance(files, dict) or not files or any(not SOURCE.fullmatch(name) for name in files):
            raise ValueError('only explicit digest source filenames are allowed')
        if f'x-ai-{day}.md' not in files:
            raise ValueError('request must include its dated edition')
        for entry in files.values():
            if set(entry) != {'staged', 'beforeSha256', 'stagedSha256'}:
                raise ValueError('invalid accepted file entry')
            self.private(entry['staged'])
            if not re.fullmatch('[a-f0-9]{64}', entry['stagedSha256']) or (entry['beforeSha256'] is not None and not re.fullmatch('[a-f0-9]{64}', entry['beforeSha256'])):
                raise ValueError('invalid accepted source hash')
        identity = hashlib.sha256(json.dumps(request, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        return request, self.state / 'receipts' / (identity + '.json')

    def load_publication(self, filename):
        """U4 reads this under owner.locked(), then persists real reader proof to receipt_path."""
        request, receipt_path = self.request(filename)
        receipt = json.loads(receipt_path.read_text())
        if receipt.get('schemaVersion') != 2 or receipt.get('requestHash') != receipt_path.stem or receipt.get('phase') not in PHASES:
            raise ValueError('invalid R2 receipt')
        bundle = self.state / 'bundles' / receipt_path.stem
        if receipt['bundle'] != str(bundle):
            raise ValueError('invalid frozen bundle location')
        metadata = json.loads((bundle / 'bundle.json').read_text())
        if json.loads((bundle / 'v1/head.json').read_text()) != receipt['head'] or metadata['manifest'] != receipt['manifest']:
            raise ValueError('frozen publication metadata changed')
        if metadata['head']['manifest']['sha256'] != receipt['publicationId']:
            raise ValueError('frozen publication identity changed')
        for ref in metadata['objects']:
            path = bundle / ref['key']
            if not re.fullmatch(r'v1/(objects|manifests)/[a-f0-9]{64}\.(json|xml)', ref['key']) or self.sha(path) != ref['sha256'] or path.stat().st_size != ref['byteLength']:
                raise ValueError('frozen publication object changed')
        return {'request': request, 'receipt': receipt, 'receipt_path': receipt_path, 'bundle': bundle}

    def prepare(self, filename, request, receipt_path):
        current = self.transport('inspect')
        actual = {'manifestSha256': current['head']['manifest']['sha256'] if current['head'] else None, 'etag': current['etag']}
        if actual != request['expected']:
            raise RuntimeError('unexpected published head; publication conflict')
        if self.owner.git('rev-parse', 'HEAD') != request['compilerRevision']:
            raise RuntimeError('compilerRevision does not match the executing compiler code')
        try:
            self.owner.git('diff', '--quiet', 'HEAD', '--', self.package)
        except RuntimeError:
            raise RuntimeError('compiler package differs from the claimed compilerRevision') from None
        manifest = current['manifest']
        prior = {f'x-ai-{edition["date"]}.md': edition['sourceSha256'] for edition in manifest['editions']} if manifest else {}
        day = request['date']
        edition_name = f'x-ai-{day}.md'
        if request['kind'] == 'scheduled' and (edition_name in prior or (prior and day <= max(name[5:15] for name in prior))):
            raise ValueError('scheduled publication requires a new latest date')
        if request['kind'] == 'correction' and edition_name not in prior:
            raise ValueError('correction requires a published edition')
        if request['kind'] != 'backfill':
            allowed = {edition_name, f'x-ai-{day[:7]}.md', f'x-ai-{day[:4]}.md'}
            earlier = sorted(name for name in prior if name < edition_name)
            previous = earlier[-1] if earlier else None
            if previous and request['kind'] == 'scheduled':
                allowed.add(previous)
            if not set(request['files']) <= allowed:
                raise ValueError('only the edition, its month/year indexes and previous daily navigation may change')
        accepted = {}
        for name, entry in request['files'].items():
            if self.sha(self.sources / name) != entry['beforeSha256']:
                raise RuntimeError(f'accepted base hash changed: {name}')
            data = self.private(entry['staged']).read_bytes()
            if hashlib.sha256(data).hexdigest() != entry['stagedSha256']:
                raise RuntimeError(f'staged accepted hash changed: {name}')
            if name in prior and entry['beforeSha256'] != prior[name]:
                raise RuntimeError(f'published accepted source hash changed: {name}')
            accepted[name] = data
        with tempfile.TemporaryDirectory(prefix='r2-compile-', dir=self.state) as tmp:
            work = Path(tmp)
            inputs = work / 'sources'
            inputs.mkdir()
            for name, digest in prior.items():
                source = self.state / 'accepted' / (digest + '.md')
                if self.sha(source) != digest:
                    raise RuntimeError(f'published accepted snapshot missing or changed: {name}')
                (inputs / name).write_bytes(source.read_bytes())
            for name, data in accepted.items():
                if not EDITION.fullmatch(name):
                    continue
                old = inputs / name
                previous_path = None
                if old.exists():
                    previous_path = work / name
                    previous_path.write_bytes(old.read_bytes())
                    if request['kind'] == 'scheduled' and name != edition_name:
                        updated = re.sub(r'^- Next:.*$', f'- Next: [[digests/x-ai-{day}|X-AI-{day}]]', old.read_text(), flags=re.M)
                        if data.decode() != updated:
                            raise ValueError('previous edition may change only its Next navigation link')
                old.write_bytes(data)
                if name == edition_name and request['kind'] != 'backfill':
                    from publication import run
                    import sys
                    private_vault = work / 'editorial-check'
                    checker_input = private_vault / 'public' / 'digests' / name
                    checker_input.parent.mkdir(parents=True)
                    checker_input.write_bytes(data)
                    checker = self.owner.repo / 'hermes/ai-x-digest/runtime/skills/note-taking/obsidian/scripts/verify-x-ai-digest-format.py'
                    run([sys.executable, checker, private_vault])
                self.node('r2-cli.ts', 'validate', old, *([previous_path] if previous_path else []))
            output = work / 'output'
            metadata = json.loads(self.node('cli.ts', '--input-dir', inputs, '--output-dir', output, '--compiler-revision', request['compilerRevision']))
            bundle = self.state / 'bundles' / receipt_path.stem
            if bundle.exists():
                raise RuntimeError('unreceipted frozen bundle exists; inspect before retrying')
            # Each frozen file reaches disk before the promotion journal can authorize a source rename.
            for path in output.rglob('*'):
                if path.is_file():
                    self.atomic(bundle / path.relative_to(output), path.read_bytes())
            self.save(bundle / 'bundle.json', metadata)
            for name in inputs.iterdir():
                self.atomic(self.state / 'accepted' / (self.sha(name) + '.md'), name.read_bytes())
            for name, data in accepted.items():
                self.atomic(bundle / 'sources' / name, data)
        receipt = {'schemaVersion': 2, 'backend': 'r2', 'date': day, 'kind': request['kind'], 'requestHash': receipt_path.stem,
                   'phase': 'accepted', 'compilerRevision': request['compilerRevision'], 'previous': request['expected'],
                   'publicationId': metadata['head']['manifest']['sha256'], 'head': metadata['head'], 'manifest': metadata['manifest'],
                   'objects': metadata['objects'], 'bundle': str(bundle),
                   'files': {name: hashlib.sha256(data).hexdigest() for name, data in accepted.items()}}
        self.save(bundle / 'acceptance.json', receipt)
        self.save(receipt_path, receipt)
        return receipt

    def publish(self, filename, receipt_path, receipt):
        loaded = self.load_publication(filename)
        request, bundle = loaded['request'], loaded['bundle']
        current = self.transport('inspect')
        current_id = current['head']['manifest']['sha256'] if current['head'] else None
        if current_id == receipt['publicationId']:
            receipt.update(phase='published', etag=current['etag'])
            receipt.pop('error', None)
            self.save(receipt_path, receipt)
            self.journal.unlink(missing_ok=True)
            return receipt
        if {'manifestSha256': current_id, 'etag': current['etag']} != receipt['previous']:
            raise RuntimeError('unexpected published head; publication conflict; accepted sources preserved')
        for name, digest in receipt['files'].items():
            target = self.sources / name
            original = request['files'][name]['beforeSha256']
            candidate = bundle / 'sources' / name
            if self.sha(candidate) != digest:
                raise RuntimeError('frozen accepted source changed')
            if self.sha(target) not in (original, digest):
                raise RuntimeError(f'interrupted promotion target has a manual edit: {target}')
        if not self.journal.exists():
            targets = []
            for name, digest in receipt['files'].items():
                target = self.sources / name
                backup = self.state / 'backups' / receipt_path.stem / name if target.exists() else None
                if backup:
                    self.atomic(backup, target.read_bytes())
                targets.append({'name': name, 'target': str(target), 'backup': str(backup) if backup else None,
                                'beforeSha256': request['files'][name]['beforeSha256'], 'sha256': digest})
            self.save(self.journal, {'schemaVersion': 2, 'request': str(Path(filename).resolve()),
                                    'receipt': str(receipt_path), 'previous': receipt['previous'],
                                    'publicationId': receipt['publicationId'], 'targets': targets})
        for name in receipt['files']:
            self.atomic(self.sources / name, (bundle / 'sources' / name).read_bytes())
        receipt['phase'] = 'source-promoted'
        self.save(receipt_path, receipt)
        try:
            self.transport('objects', bundle, json.dumps(receipt['previous']))
            receipt['phase'] = 'objects-verified'
            self.save(receipt_path, receipt)
            self.transport('publish', bundle, json.dumps(receipt['previous']))
            current = self.transport('inspect')
            if not current['head'] or current['head']['manifest']['sha256'] != receipt['publicationId']:
                raise RuntimeError('published head changed before receipt persistence')
            receipt.update(phase='published', etag=current['etag'])
            receipt.pop('error', None)
            self.save(receipt_path, receipt)
            self.journal.unlink()
            return receipt
        except (RuntimeError, OSError, ValueError) as error:
            receipt['error'] = str(error)
            self.save(receipt_path, receipt)
            raise

    def digest(self, filename):
        request, receipt_path = self.request(filename)
        receipt = json.loads(receipt_path.read_text()) if receipt_path.exists() else None
        bundle = self.state / 'bundles' / receipt_path.stem
        if receipt is None and bundle.exists():
            frozen_receipt = bundle / 'acceptance.json'
            if not frozen_receipt.exists():
                raise RuntimeError('incomplete unreceipted bundle; no sources promoted; inspect before retrying')
            receipt = json.loads(frozen_receipt.read_text())
            self.save(receipt_path, receipt)
            self.load_publication(filename)
        if receipt and receipt['phase'] == 'deliverypending':
            raise RuntimeError('delivery result is ambiguous; resolve it explicitly before retrying')
        if receipt and receipt['phase'] in ('published', 'readerverified', 'complete'):
            return self.load_publication(filename)['receipt']
        receipt = receipt or self.prepare(filename, request, receipt_path)
        return self.publish(filename, receipt_path, receipt)

    def recover(self):
        if self.journal.exists():
            journal = json.loads(self.journal.read_text())
            if journal.get('schemaVersion') != 2:
                raise ValueError('unsupported R2 promotion journal')
            loaded = self.load_publication(journal['request'])
            if str(loaded['receipt_path']) != journal['receipt']:
                raise ValueError('promotion journal receipt mismatch')
            self.publish(journal['request'], loaded['receipt_path'], loaded['receipt'])
