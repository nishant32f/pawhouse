#!/usr/bin/env python3
"""Build a pinned reader, verify served pages, and emit verified date redirects."""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
from publication import Publisher, MISE, run, save

CLOUDFLARE_API = 'https://api.cloudflare.com/client/v4'


class MainContent(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.hidden = 0
        self.text = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'main':
            self.depth += 1
        if self.depth:
            if tag in ('script', 'style'):
                self.hidden += 1
            if tag == 'a':
                self.links.extend(value for name, value in attrs if name == 'href')

    def handle_endtag(self, tag):
        if self.depth and tag in ('script', 'style'):
            self.hidden -= 1
        if tag == 'main':
            self.depth -= 1

    def handle_data(self, text):
        if self.depth and not self.hidden:
            self.text.append(text)


def content(html):
    parsed = MainContent()
    parsed.feed(html)
    text = ' '.join(' '.join(parsed.text).split())
    if not text:
        raise ValueError('rendered page has no main content')
    return text, parsed.links


def fetch(origin, path):
    request = urllib.request.Request(origin.rstrip('/') + path, headers={'Cache-Control': 'no-cache', 'User-Agent': 'pawhouse-release-verifier/1'})
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise ValueError(f'route did not return 200: {path}')
        return response.read().decode('utf-8'), response.headers


def manifest_at(origin, bootstrap=False):
    try:
        payload, _ = fetch(origin, '/deployment.json')
    except urllib.error.HTTPError as error:
        if bootstrap and error.code == 404:
            return None
        raise
    manifest = json.loads(payload)
    if not isinstance(manifest, dict) or not re.fullmatch(r'[0-9a-f]{40}', manifest.get('sourceRevision', '')):
        raise ValueError('live deployment manifest has no valid source revision')
    if not isinstance(manifest.get('editions'), list):
        raise ValueError('live deployment manifest has no editions')
    return manifest


def guard(publisher, candidate, origin, bootstrap=False):
    candidate = publisher.git('rev-parse', '--verify', candidate + '^{commit}')
    live = manifest_at(origin, bootstrap)
    if live is not None:
        # An unknown live SHA, unavailable origin, or unrelated history fails closed.
        publisher.git('merge-base', '--is-ancestor', live['sourceRevision'], candidate)
    return {'candidate': candidate, 'live_revision': live['sourceRevision'] if live else None}


def route_file(artifact, route):
    if not route.startswith('/') or '..' in route.split('/'):
        raise ValueError('invalid public route in manifest')
    return artifact / route.lstrip('/') / 'index.html' if route.endswith('/') else artifact / route.lstrip('/')


def verify(publisher, artifact, origin, request=None, version=None):
    artifact = Path(artifact).resolve()
    expected = json.loads((artifact / 'deployment.json').read_text())
    live = manifest_at(origin)
    publisher.git('merge-base', '--is-ancestor', expected['sourceRevision'], live['sourceRevision'])
    editions = expected['editions']
    receipt_path = None
    receipt = None
    if request:
        accepted, receipt_path = publisher.request(request)
        receipt = json.loads(receipt_path.read_text())
        if receipt['phase'] not in ('readerpending', 'readerverified'):
            raise ValueError('only a committed pending publication can be verified')
        publisher.git('merge-base', '--is-ancestor', receipt['commit'], expected['sourceRevision'])
        editions = [edition for edition in editions if edition['date'] == accepted['date']]
        if len(editions) != 1 or editions[0]['sourceSha256'] != receipt['files'][f'digests/x-ai-{accepted["date"]}.md']:
            raise ValueError('reader artifact does not contain the accepted date and source hash')
    home, _ = fetch(origin, '/')
    if live['sourceRevision'] == expected['sourceRevision']:
        expected_home = (artifact / 'index.html').read_text()
    else:
        latest = max(live['editions'], key=lambda edition: edition['date'])
        expected_home, _ = fetch(origin, latest['path'])
    if content(home) != content(expected_home):
        raise ValueError('home does not show the latest deployed dated edition')
    tested = ['/']
    for route in ('/archive/', '/search/'):
        page, _ = fetch(origin, route)
        content(page)
        tested.append(route)
    sitemap, _ = fetch(origin, '/sitemap.xml')
    live_sitemap = ET.fromstring(sitemap)
    local_sitemap = ET.parse(artifact / 'sitemap.xml').getroot()
    namespace = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
    def sitemap_paths(root):
        return {urllib.parse.urlparse(node.text).path for node in root.findall('.//' + namespace + 'loc') if node.text}
    if live_sitemap.tag != namespace + 'urlset' or not sitemap_paths(local_sitemap) <= sitemap_paths(live_sitemap):
        raise ValueError('sitemap is missing accepted reader URLs')
    tested.append('/sitemap.xml')
    verified_dates = []
    for edition in editions:
        matches = [other for other in live['editions'] if other['date'] == edition['date']]
        if len(matches) != 1 or matches[0] != edition:
            raise ValueError(f'live edition differs from accepted source: {edition["date"]}')
        for route in [edition['path'], edition['readPath'], *edition['stories']]:
            served, _ = fetch(origin, route)
            if content(served) != content(route_file(artifact, route).read_text()):
                raise ValueError(f'complete rendered prose or source links differ: {route}')
            tested.append(route)
        verified_dates.append(edition['date'])
    if not tested:
        raise ValueError('artifact contains no dated editions')
    rss, headers = fetch(origin, '/rss.xml')
    if headers.get_content_type() != 'application/rss+xml' or headers.get_content_charset() != 'utf-8':
        raise ValueError('RSS must serve application/rss+xml; charset=utf-8')
    actual_rss = ET.fromstring(rss)
    local_rss = ET.parse(artifact / 'rss.xml').getroot()
    if actual_rss.tag != 'rss' or actual_rss.attrib.get('version') != '2.0':
        raise ValueError('RSS is not version 2.0')
    for edition in editions:
        def item_for(root):
            matches = [item for item in root.findall('./channel/item') if (item.findtext('guid') or '').endswith(edition['path'])]
            if len(matches) != 1:
                raise ValueError('RSS is missing its unique dated item')
            return matches[0]
        actual_item, expected_item = item_for(actual_rss), item_for(local_rss)
        if actual_item.findtext('description') != expected_item.findtext('description'):
            raise ValueError('RSS full edition content differs')
        if not actual_item.findtext('description'):
            raise ValueError('RSS edition has no full text')
    tested.append('/rss.xml')
    missing = '/editions/0001-01-01/stories/not-a-published-story/'
    try:
        fetch(origin, missing)
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
    else:
        raise ValueError('unpublished route did not return a real 404')
    tested.append(missing)
    result = {'origin': origin.rstrip('/'), 'sourceRevision': live['sourceRevision'], 'version': version,
              'tested_routes': tested, 'dates': verified_dates}
    # Only a complete successful probe can extend the dates available to an activation consumer.
    mapping_path = publisher.state / 'verified-redirects.json'
    mapping = json.loads(mapping_path.read_text()) if mapping_path.exists() else {'redirects': {}}
    for edition in editions:
        mapping['redirects'][f'/digests/x-ai-{edition["date"]}'] = {
            'destination': origin.rstrip('/') + edition['path'], 'sourceRevision': live['sourceRevision'],
            'sourceSha256': edition['sourceSha256']}
    save(mapping_path, mapping)
    save(publisher.state / 'reader-release.json', result)
    if receipt is not None:
        receipt.update(phase='readerverified', reader=result)
        save(receipt_path, receipt)
    return result


def build(publisher, commit):
    commit = publisher.git('rev-parse', '--verify', commit + '^{commit}')
    output = publisher.state / 'artifacts' / commit
    if output.exists():
        manifest = json.loads((output / 'deployment.json').read_text())
        if manifest['sourceRevision'] != commit:
            raise ValueError('stored artifact source revision mismatch')
        return {'artifact': str(output), 'sourceRevision': commit}
    with tempfile.TemporaryDirectory(prefix='reader-build-', dir=publisher.state) as temporary:
        checkout = Path(temporary) / 'source'
        run(['git', 'clone', '--shared', '--no-checkout', publisher.repo, checkout])
        run(['git', '-C', checkout, 'checkout', '--detach', commit])
        app = checkout / 'apps/daily'
        for command in (['npm', 'ci'], ['npm', 'run', 'check'], ['npm', 'test'], ['npm', 'run', 'build']):
            run([MISE, 'exec', 'node@22.23.3', '--', *command], app)
        manifest = json.loads((app / 'dist/deployment.json').read_text())
        if manifest['sourceRevision'] != commit:
            raise ValueError('built artifact source revision mismatch')
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(app / 'dist'), output)
    return {'artifact': str(output), 'sourceRevision': commit}


def routes(manifest):
    if 'routes' in manifest:
        return set(manifest['routes'])
    return {route for edition in manifest['editions'] for route in [edition['path'], edition['readPath'], *edition['stories']]}


def cloudflare_deployments(bootstrap=False):
    account = os.environ.get('CLOUDFLARE_ACCOUNT_ID', '')
    token = os.environ.get('CLOUDFLARE_API_TOKEN', '')
    if not re.fullmatch(r'[0-9a-f]{32}', account) or not token:
        raise ValueError('configured Cloudflare account and API token are required')
    url = CLOUDFLARE_API + '/accounts/' + account + '/workers/scripts/pawhouse-daily/deployments'
    deployments = []
    page = 1
    while True:
        request = urllib.request.Request(url + f'?page={page}&per_page=100', headers={'Authorization': 'Bearer ' + token})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.load(response)
        except urllib.error.HTTPError as error:
            if bootstrap and page == 1 and error.code == 404:
                return []
            raise
        if payload.get('success') is not True:
            raise ValueError('Cloudflare deployment lookup failed')
        records = payload['result']['deployments']
        if not isinstance(records, list):
            raise ValueError('Cloudflare deployment response is malformed')
        deployments.extend(records)
        if page >= payload.get('result_info', {}).get('total_pages', 1):
            break
        page += 1
    if not deployments and not bootstrap:
        raise ValueError('Cloudflare has no deployment; explicit bootstrap is required')
    return deployments



def deploy(publisher, artifact, origin, command, bootstrap=False):
    manifest = json.loads((Path(artifact) / 'deployment.json').read_text())
    guard(publisher, manifest['sourceRevision'], origin, bootstrap)
    live = manifest_at(origin, bootstrap)
    if live is not None and not routes(live) <= routes(manifest):
        raise ValueError('candidate would remove previously deployed reader URLs')
    for route in routes(manifest):
        if not route_file(Path(artifact), route).is_file():
            raise ValueError(f'candidate artifact is missing a declared route: {route}')
    if command and command[0] == '--':
        command = command[1:]
    if not command:
        raise ValueError('pass the deployment executable and arguments after --')
    try:
        output = run(command, publisher.repo)
    except (ValueError, RuntimeError, OSError) as error:
        save(publisher.state / 'reader-failure.json', {'origin': origin, 'sourceRevision': manifest['sourceRevision'], 'phase': 'deploy', 'error': str(error)})
        raise
    return {'sourceRevision': manifest['sourceRevision'], 'phase': 'readerpending', 'deployment_output': output}


def deployment_version(filename):
    deployments = json.loads(Path(filename).read_text())
    if not deployments:
        raise ValueError('Cloudflare has no deployed version')
    deployment = max(deployments, key=lambda item: item['created_on'])
    versions = deployment['versions']
    if len(versions) != 1 or versions[0]['percentage'] != 100:
        raise ValueError('release verification requires one version serving all traffic')
    return versions[0]['version_id']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    command = sub.add_parser('cloudflare-deployments')
    command.add_argument('--bootstrap', action='store_true')
    command = sub.add_parser('version')
    command.add_argument('--deployments', required=True)
    command = sub.add_parser('deploy')
    command.add_argument('--artifact', required=True)
    command.add_argument('--origin', required=True)
    command.add_argument('--bootstrap', action='store_true')
    command.add_argument('deploy_command', nargs=argparse.REMAINDER)
    command = sub.add_parser('guard')
    command.add_argument('--candidate', required=True)
    command.add_argument('--origin', required=True)
    command.add_argument('--bootstrap', action='store_true')
    command = sub.add_parser('build')
    command.add_argument('--commit', required=True)
    command = sub.add_parser('verify')
    command.add_argument('--artifact', required=True)
    command.add_argument('--origin', required=True)
    command.add_argument('--request')
    command.add_argument('--version')
    args = parser.parse_args()
    if args.command == 'cloudflare-deployments':
        print(json.dumps(cloudflare_deployments(args.bootstrap)))
        return
    if args.command == 'version':
        print(deployment_version(args.deployments))
        return
    publisher = Publisher()
    with publisher.locked():
        if args.command == 'guard':
            result = guard(publisher, args.candidate, args.origin, args.bootstrap)
        elif args.command == 'deploy':
            result = deploy(publisher, args.artifact, args.origin, args.deploy_command, args.bootstrap)
        elif args.command == 'build':
            result = build(publisher, args.commit)
        else:
            try:
                result = verify(publisher, args.artifact, args.origin, args.request, args.version)
            except (ValueError, RuntimeError, OSError, KeyError, ET.ParseError) as error:
                save(publisher.state / 'reader-failure.json', {'origin': args.origin, 'artifact': args.artifact, 'error': str(error), 'version': args.version})
                raise
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError, OSError, KeyError, ET.ParseError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
