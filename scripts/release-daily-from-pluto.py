#!/usr/bin/env python3
"""Release a pinned daily reader from Pluto using private Cloudflare credentials."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
from publication import MISE, Publisher, save

spec = importlib.util.spec_from_file_location('daily_release', Path(__file__).with_name('daily-release.py'))
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)

ORIGIN = 'https://daily.nishantkhurana.me'
ACCOUNT = '1688bfec49a43a217df10ed33b86e300'


def credentials_at(filename, publisher):
    filename = Path(filename).expanduser().resolve()
    for public in (publisher.repo, publisher.vault):
        if filename == public or public in filename.parents:
            raise ValueError('Cloudflare credentials must stay outside the repository and public vault')
    if not filename.is_file() or stat.S_IMODE(filename.stat().st_mode) & 0o077:
        raise ValueError('Cloudflare credentials must be a private file with mode 0600 or stricter')
    credentials = json.loads(filename.read_text())
    if not isinstance(credentials, dict) or credentials.get('account_id') != ACCOUNT:
        raise ValueError('Cloudflare credentials must use the personal Pawhouse account')
    token = credentials.get('api_token')
    if not isinstance(token, str) or not token.strip():
        raise ValueError('Cloudflare credentials must contain an API token')
    return token


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--request')
    parser.add_argument('--bundle', help='frozen accepted publication, including before backend activation')
    parser.add_argument('--bootstrap', action='store_true')
    parser.add_argument('--credentials', default='~/.config/pawhouse-daily/cloudflare.json')
    args = parser.parse_args(argv)
    token = None
    try:
        publisher = Publisher()
        token = credentials_at(args.credentials, publisher)
        variables = {'CLOUDFLARE_ACCOUNT_ID': ACCOUNT, 'CLOUDFLARE_API_TOKEN': token}
        previous = {name: os.environ.get(name) for name in variables}
        os.environ.update(variables)
        try:
            with publisher.locked():
                phase = 'preflight'
                artifact = None
                version = None
                try:
                    release.cloudflare_deployments(args.bootstrap)
                    release.guard(publisher, args.commit, ORIGIN, args.bootstrap)
                    bundle, loaded = release.selected_publication(publisher, args.request, args.bundle)
                    phase = 'build'
                    built = release.build(publisher, args.commit)
                    artifact = str(Path(built['artifact']).resolve())
                    phase = 'acceptance'
                    expected = release.code_artifact(artifact)
                    phase = 'tools'
                    with tempfile.TemporaryDirectory(prefix='reader-deploy-', dir=publisher.state) as temporary:
                        checkout = Path(temporary) / 'source'
                        release.run(['git', 'clone', '--shared', '--no-checkout', publisher.repo, checkout])
                        release.run(['git', '-C', checkout, 'checkout', '--detach', expected['codeRevision']])
                        app = checkout / 'apps/daily'
                        release.run([MISE, 'exec', 'node@22.23.3', '--', 'npm', 'ci'], app)
                        command = [MISE, 'exec', 'node@22.23.3', '--', 'node',
                                   app / 'node_modules/wrangler/bin/wrangler.js', 'deploy',
                                   '--config', Path(artifact) / 'server/wrangler.json']
                        phase = 'deploy'
                        if loaded:
                            loaded['receipt'].update(phase='published', verificationError='code release awaiting reader verification')
                            publisher.r2().save(loaded['receipt_path'], loaded['receipt'])
                        release.deploy(publisher, artifact, bundle, ORIGIN, command, args.bootstrap)
                    phase = 'version'
                    deployments = release.cloudflare_deployments()
                    with tempfile.TemporaryDirectory(prefix='reader-version-', dir=publisher.state) as temporary:
                        filename = Path(temporary) / 'deployments.json'
                        save(filename, deployments)
                        version = release.deployment_version(filename)
                    phase = 'verify'
                    result = release.verify(publisher, bundle, ORIGIN, args.request, version, expected['codeRevision'])
                except (ValueError, RuntimeError, OSError, KeyError, ET.ParseError) as error:
                    save(publisher.state / 'reader-failure.json', {
                        'origin': ORIGIN, 'codeRevision': args.commit, 'artifact': artifact,
                        'phase': phase, 'version': version, 'error': release.redacted(error)})
                    raise
        finally:
            for name, value in previous.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value
        print(json.dumps(result, sort_keys=True))
    except (ValueError, RuntimeError, OSError, KeyError, ET.ParseError) as error:
        message = str(error)
        if token:
            message = message.replace(token, '[redacted]')
        print(message, file=sys.stderr)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
