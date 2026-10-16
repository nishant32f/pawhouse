#!/usr/bin/env python3
"""Install only this package's listed Hermes files, preserving recovery copies."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hermes-home', type=Path, required=True)
    parser.add_argument('--phase', choices=('verifier', 'producer'), default='producer',
                        help='Install the dual checker first; producer installs the complete package')
    args = parser.parse_args()
    package = Path(__file__).resolve().parent
    manifest = json.loads((package / 'runtime-manifest.json').read_text())
    home = args.hermes_home.expanduser().resolve()
    if not home.is_dir():
        parser.error('Hermes home must already exist')
    entries = []
    files = manifest['verifier_files'] if args.phase == 'verifier' else manifest['files']
    for relative in files:
        source = (package / manifest['sources'][relative]).resolve() if relative in manifest.get('sources', {}) else (package / 'runtime' / relative).resolve()
        target = (home / relative).resolve()
        if not source.is_relative_to(package) or not target.is_relative_to(home / 'skills'):
            parser.error(f'file is outside the owned skill paths: {relative}')
        if not source.is_file():
            parser.error(f'missing package file: {relative}')
        if hashlib.sha256(source.read_bytes()).hexdigest() != manifest['sha256'][relative]:
            parser.error(f'owned runtime source hash differs from reviewed manifest: {relative}')
        entries.append((relative, source, target))
    stamp = datetime.now().astimezone().strftime('%Y%m%d-%H%M%S-%f')
    backup = home / 'backups' / f'ai-x-digest-{manifest["version"]}-{stamp}'
    backup.mkdir(parents=True, mode=0o700)
    receipt = {'version': manifest['version'], 'phase': args.phase, 'status': 'preparing', 'files': {}, 'backup': str(backup)}
    receipt_path = backup / 'receipt.json'
    staged_files = []
    replaced = []
    try:
        for relative, source, target in entries:
            existed = target.exists()
            if existed:
                saved = backup / relative
                saved.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, saved)
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
                staged = Path(temporary.name)
                staged_files.append(staged)
                temporary.write(source.read_bytes())
            shutil.copymode(source, staged)
            receipt['files'][relative] = {
                'existed': existed,
                'sha256': hashlib.sha256(staged.read_bytes()).hexdigest(),
            }
        receipt['status'] = 'prepared'
        receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
        for (relative, _, target), staged in zip(entries, staged_files):
            staged.replace(target)
            replaced.append((relative, target))
            if hashlib.sha256(target.read_bytes()).hexdigest() != manifest['sha256'][relative]:
                raise OSError(f'installed runtime hash differs from reviewed manifest: {relative}')
        receipt['status'] = 'installed'
        receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    except Exception:
        recovery_errors = []
        for relative, target in reversed(replaced):
            try:
                if receipt['files'][relative]['existed']:
                    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
                        restored = Path(temporary.name)
                        staged_files.append(restored)
                    shutil.copy2(backup / relative, restored)
                    restored.replace(target)
                else:
                    target.unlink(missing_ok=True)
            except OSError as error:
                recovery_errors.append(f'{relative}: {error}')
        receipt['status'] = 'recovery-failed' if recovery_errors else 'rolled-back'
        receipt['recovery_errors'] = recovery_errors
        receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
        raise
    finally:
        for staged in staged_files:
            staged.unlink(missing_ok=True)
    print(json.dumps(receipt, indent=2))
    print('Cron is unchanged. Follow rollout.md before producer or cron activation.')


if __name__ == '__main__':
    main()
