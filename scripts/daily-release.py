#!/usr/bin/env python3
"""Build pinned SSR code and independently verify a frozen accepted publication."""
from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
import math
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
ACCOUNT = '1688bfec49a43a217df10ed33b86e300'
BASE_ROUTES = {'/', '/archive/', '/search/', '/rss.xml', '/sitemap.xml', '/deployment.json'}


def normalized(value):
    return ' '.join(value.split())


class Node:
    def __init__(self, tag='', attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []

    def nodes(self, tag=None, css=None):
        return [node for node in self.walk() if (tag is None or node.tag == tag)
                and (css is None or css in node.attrs.get('class', '').split())]

    def walk(self):
        yield self
        for child in self.children:
            if isinstance(child, Node):
                yield from child.walk()

    def text(self):
        return normalized(''.join((' ' + child.text() + ' ' if child.tag in ('p', 'div', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'section', 'article', 'figcaption', 'span') else child.text()) if isinstance(child, Node) else child for child in self.children))

    def links(self):
        return [node.attrs.get('href') for node in self.nodes('a')]


class Document(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.stack = [self.root]
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in ('area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'):
            self.stack.append(node)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def main_content(html):
    nodes = Document(html).root.nodes('main')
    if len(nodes) != 1 or not nodes[0].text():
        raise ValueError('rendered page has no unique main content')
    return nodes[0]


def fetch(origin, path):
    request = urllib.request.Request(origin.rstrip('/') + path, headers={'Cache-Control': 'no-cache', 'User-Agent': 'pawhouse-release-verifier/2'})
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
    revision = manifest.get('codeRevision', manifest.get('sourceRevision', '')) if isinstance(manifest, dict) else ''
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('live deployment manifest has no valid code revision')
    if not isinstance(manifest.get('editions'), list):
        raise ValueError('live deployment manifest has no editions')
    return manifest


def code_revision(manifest):
    return manifest.get('codeRevision', manifest.get('sourceRevision'))


def guard(publisher, candidate, origin, bootstrap=False):
    candidate = publisher.git('rev-parse', '--verify', candidate + '^{commit}')
    live = manifest_at(origin, bootstrap)
    if live is not None:
        publisher.git('merge-base', '--is-ancestor', code_revision(live), candidate)
    return {'candidate': candidate, 'live_revision': code_revision(live) if live else None}


def routes(manifest):
    if 'routes' in manifest:
        return set(manifest['routes'])
    return BASE_ROUTES | {route for edition in manifest['editions'] for route in [edition['path'], edition['readPath'], *edition['stories']]}


def frozen_publication(publisher, bundle):
    bundle = Path(bundle).resolve()
    metadata = json.loads((bundle / 'bundle.json').read_text())
    head, manifest = metadata['head'], metadata['manifest']
    if json.loads((bundle / 'v1/head.json').read_text()) != head:
        raise ValueError('frozen publication head changed')
    refs = metadata['objects']
    for ref in [*refs, head['manifest']]:
        if not re.fullmatch(r'v1/(objects|manifests)/[a-f0-9]{64}\.(json|xml)', ref['key']):
            raise ValueError('unsafe frozen object key')
        data = (bundle / ref['key']).read_bytes()
        if hashlib.sha256(data).hexdigest() != ref['sha256'] or len(data) != ref['byteLength']:
            raise ValueError('frozen publication object changed')
    if json.loads((bundle / head['manifest']['key']).read_text()) != manifest:
        raise ValueError('frozen publication manifest changed')
    referenced = [entry['object'] for entry in manifest['editions']] + [manifest[name] for name in ('catalog', 'routes', 'search', 'rss')]
    if any(ref not in refs for ref in referenced):
        raise ValueError('frozen publication is missing a referenced object')
    package = publisher.repo / 'hermes/ai-x-digest/content'
    editions = json.loads(run([MISE, 'exec', 'node@22.23.3', '--', 'node', '--import', 'tsx',
                              publisher.repo / 'scripts/daily-content-proof.ts',
                              *[bundle / entry['object']['key'] for entry in manifest['editions']]], package))
    expected = {'publicationRevision': head['manifest']['sha256'], 'compilerRevision': manifest['compilerRevision'],
                'routes': list(BASE_ROUTES | {entry['path'] for entry in json.loads((bundle / manifest['routes']['key']).read_text())['routes']}),
                'editions': []}
    if not editions:
        raise ValueError('frozen publication contains no editions')
    if len(manifest['editions']) != len(editions):
        raise ValueError('frozen edition count differs from its manifest')
    for entry, edition in zip(manifest['editions'], editions):
        if entry['date'] != edition['date'] or entry['sourceSha256'] != edition['sourceSha256']:
            raise ValueError('frozen edition differs from its manifest')
        expected['editions'].append({'date': edition['date'], 'sourceSha256': edition['sourceSha256'],
                                    'contentSha256': entry['object']['sha256'], 'path': edition['path'],
                                    'readPath': edition['readPath'], 'stories': [s['path'] for s in edition.get('stories', [])]})
    return expected, editions, (bundle / manifest['rss']['key']).read_text(), json.loads((bundle / manifest['search']['key']).read_text())['documents']


def check_prose(node, html):
    expected = Document(html).root
    if node.text() != expected.text() or node.links() != expected.links():
        raise ValueError('rendered prose or adjacent sources differ from accepted content')
    def images(root):
        return [{key: image.attrs.get(key) for key in ('src', 'alt', 'title')} for image in root.nodes('img')]
    if images(node) != images(expected):
        raise ValueError('prose images differ from accepted content')


def check_visual(node, visual, point_values):
    figures = [figure for figure in node.nodes('figure') if 'data-story-visual' in figure.attrs]
    if len(figures) != (1 if visual else 0):
        raise ValueError('accepted story figure is missing or duplicated')
    if not visual:
        return
    figure = figures[0]
    if figure.attrs.get('data-story-visual') != visual['kind']:
        raise ValueError('story figure kind differs')
    captions = figure.nodes('figcaption')
    caption = f'{visual["caption"]} Source: {visual["source"]["label"]}.'
    if visual['kind'] == 'image':
        caption += f' Image: {visual["credit"]}.'
    if len(captions) != 1 or captions[0].text() != normalized(caption) or captions[0].links() != [visual['source']['url']]:
        raise ValueError('figure caption or source differs')
    if visual['kind'] == 'image':
        images = figure.nodes('img')
        if len(images) != 1 or any(images[0].attrs.get(key) != str(visual[key]) for key in ('src', 'alt', 'width', 'height')) or normalized(visual['credit']) not in captions[0].text():
            raise ValueError('figure image or credit differs')
    else:
        titles = figure.nodes(css='chart-title')
        if len(titles) != 1 or titles[0].text() != normalized(f'{visual["title"]} {visual["unit"]}'):
            raise ValueError('chart title or unit differs')
        points = [point for point in figure.nodes('li') if 'data-chart-value' in point.attrs]
        if len(points) != len(visual['points']):
            raise ValueError('chart values are missing')
        maximum = max(point['value'] for point in visual['points'])
        for point, expected, display in zip(points, visual['points'], point_values):
            if float(point.attrs.get('data-chart-value', 'nan')) != expected['value'] or point.attrs.get('data-chart-qualifier') != expected['qualifier'] or normalized(expected['label']) not in point.text():
                raise ValueError('chart value, qualifier or label differs')
            visible = point.nodes(css='bar-value')
            labels = point.nodes(css='bar-label')
            if len(visible) != 1 or visible[0].text() != display or len(labels) != 1 or labels[0].text() != normalized(expected['label']):
                raise ValueError('visible chart value or qualifier differs')
            fills = point.nodes(css='bar-fill')
            height = re.fullmatch(r'height:\s*([+\-]?(?:\d*\.?\d+)(?:[eE][+\-]?\d+)?)%\s*;?', fills[0].attrs.get('style', '')) if len(fills) == 1 else None
            if height is None:
                raise ValueError('chart drawing is missing')
            if not math.isclose(float(height[1]), expected['value'] / maximum * 100, rel_tol=1e-12, abs_tol=0):
                raise ValueError('chart drawing differs from accepted value')


def check_story(node, story, preview=False):
    copies = node.nodes(css='reading-copy')
    if len(copies) != 1:
        raise ValueError('story requires one complete reading copy')
    check_prose(copies[0], story['summaryHtml'] if preview else story['html'])
    if preview:
        citations = node.nodes('p', css='source')
        sources = story['sources']
        label = 'Source: ' if len(sources) == 1 else 'Sources: '
        expected = normalized(label + ', '.join(source['label'] for source in sources))
        if (len(citations) != 1 or citations[0].text() != expected
                or citations[0].links() != [source['url'] for source in sources]):
            raise ValueError('story preview sources differ from accepted content')
    if normalized(story['headline']) not in node.text():
        raise ValueError('story headline is missing')
    editorial = story.get('editorial')
    if editorial:
        for field in ('section', 'deck'):
            if editorial[field] and normalized(editorial[field]) not in node.text():
                raise ValueError('story editorial text is missing')
    check_visual(node, editorial['visual'] if editorial else None, story['proofPointValues'])


def check_edition(html, edition, front=False):
    node = main_content(html)
    if edition['kind'] == 'legacy':
        copies = node.nodes(css='reading-copy')
        if len(copies) != 1:
            raise ValueError('edition requires one complete reading copy')
        check_prose(copies[0], edition['html'])
    else:
        for story in edition['activeStories']:
            matches = [child for child in node.walk() if child.attrs.get('id') == story['id'] and child.tag in ('article', 'section')]
            if len(matches) != 1:
                raise ValueError('edition is missing an accepted story')
            check_story(matches[0], story, preview=front and story['id'] != edition['lead']['id'])
        for story in edition['archivedStories']:
            if story['path'] not in node.links():
                raise ValueError('edition is missing an archived story link')


def verify_publication(publisher, bundle, origin, code, version=None):
    expected, editions, rss, search = frozen_publication(publisher, bundle)
    live = manifest_at(origin)
    if not re.fullmatch(r'[0-9a-f]{40}', code or '') or live.get('codeRevision') != code:
        raise ValueError('live code revision differs from selected release')
    for field in ('publicationRevision', 'compilerRevision', 'editions'):
        if live.get(field) != expected[field]:
            raise ValueError(f'live {field} differs from accepted publication')
    if routes(live) != routes(expected):
        raise ValueError('live routes differ from accepted publication')
    tested = []
    def page(route):
        html, _ = fetch(origin, route)
        tested.append(route)
        return html
    check_edition(page('/'), max(editions, key=lambda edition: edition['date']), front=True)
    for edition in editions:
        for route in (edition['path'], edition['readPath']):
            check_edition(page(route), edition, front=route == edition['path'])
        for story in edition.get('stories', []):
            check_story(main_content(page(story['path'])), story)
    archive = main_content(page('/archive/'))
    archive_links = {path for edition in editions for path in (edition['path'], edition['readPath'])} | {story['path'] for edition in editions for story in edition.get('stories', []) if story['kind'] != 'archived'}
    if not archive_links <= set(archive.links()):
        raise ValueError('archive is missing accepted reader links')
    search_page = main_content(page('/search/'))
    for document in search:
        entries = [entry for entry in search_page.nodes('li') if document['path'] in entry.links()]
        if len(entries) != 1 or normalized(document['text']) not in entries[0].text():
            raise ValueError('search is missing accepted full text or route')
    sitemap = ET.fromstring(page('/sitemap.xml'))
    namespace = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
    paths = {urllib.parse.urlparse(node.text).path for node in sitemap.findall('.//' + namespace + 'loc') if node.text}
    if sitemap.tag != namespace + 'urlset' or not routes(expected) - {'/rss.xml', '/deployment.json', '/sitemap.xml'} <= paths:
        raise ValueError('sitemap is missing accepted reader URLs')
    actual_rss, headers = fetch(origin, '/rss.xml')
    if headers.get_content_type() != 'application/rss+xml' or headers.get_content_charset() != 'utf-8':
        raise ValueError('RSS must serve application/rss+xml; charset=utf-8')
    root = ET.fromstring(actual_rss)
    if root.tag != 'rss' or root.attrib.get('version') != '2.0' or actual_rss != rss:
        raise ValueError('RSS bytes, identity or full edition content differ')
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
    return {'origin': origin.rstrip('/'), 'codeRevision': live['codeRevision'],
            'publicationRevision': expected['publicationRevision'], 'compilerRevision': expected['compilerRevision'],
            'version': version, 'tested_routes': tested, 'dates': [edition['date'] for edition in editions]}


def selected_publication(publisher, request=None, bundle=None):
    loaded = None
    if request:
        active = publisher.r2()
        if active is None:
            raise ValueError('content verification requires the explicit R2 backend; use --bundle for preview')
        loaded = active.load_publication(request)
        if loaded['receipt']['phase'] not in ('published', 'readerverified'):
            raise ValueError('only a published R2 publication can be verified')
        if bundle and Path(bundle).resolve() != loaded['bundle'].resolve():
            raise ValueError('selected bundle differs from accepted publication')
        bundle = loaded['bundle']
    if bundle is None:
        raise ValueError('select --request or a frozen --bundle')
    return Path(bundle).resolve(), loaded


def verify(publisher, bundle, origin, request=None, version=None, code=None):
    bundle, loaded = selected_publication(publisher, request, bundle)
    try:
        result = verify_publication(publisher, bundle, origin, code, version)
    except (ValueError, RuntimeError, OSError, KeyError, ET.ParseError) as error:
        if loaded:
            loaded['receipt'].update(phase='published', verificationError=redacted(error))
            publisher.r2().save(loaded['receipt_path'], loaded['receipt'])
        raise
    entries = json.loads((bundle / 'bundle.json').read_text())['manifest']['editions']
    mapping_path = publisher.state / 'verified-redirects.json'
    mapping = json.loads(mapping_path.read_text()) if mapping_path.exists() else {'redirects': {}}
    for edition in entries:
        mapping['redirects'][f'/digests/x-ai-{edition["date"]}'] = {
            'destination': origin.rstrip('/') + f'/editions/{edition["date"]}/', 'publicationRevision': result['publicationRevision'],
            'codeRevision': result['codeRevision'], 'sourceSha256': edition['sourceSha256']}
    save(mapping_path, mapping)
    save(publisher.state / 'reader-release.json', result)
    if loaded:
        loaded['receipt'].update(phase='readerverified', reader=result)
        loaded['receipt'].pop('verificationError', None)
        publisher.r2().save(loaded['receipt_path'], loaded['receipt'])
    return result


def code_artifact(artifact):
    artifact = Path(artifact).resolve()
    manifest = json.loads((artifact / 'code.json').read_text())
    if not re.fullmatch(r'[0-9a-f]{40}', manifest.get('codeRevision', '')):
        raise ValueError('artifact has no valid code revision')
    config = json.loads((artifact / 'server/wrangler.json').read_text())
    if not (artifact / 'server' / config['main']).is_file() or not (artifact / 'server' / config['assets']['directory']).is_dir() or config.get('no_bundle') is not True:
        raise ValueError('artifact is missing its SSR handler or assets')
    return manifest


def build(publisher, commit):
    commit = publisher.git('rev-parse', '--verify', commit + '^{commit}')
    output = publisher.state / 'artifacts' / commit
    if output.exists():
        if code_artifact(output)['codeRevision'] != commit:
            raise ValueError('stored artifact code revision mismatch')
        return {'artifact': str(output), 'codeRevision': commit}
    with tempfile.TemporaryDirectory(prefix='reader-build-', dir=publisher.state) as temporary:
        checkout = Path(temporary) / 'source'
        run(['git', 'clone', '--shared', '--no-checkout', publisher.repo, checkout])
        run(['git', '-C', checkout, 'checkout', '--detach', commit])
        for folder in ('hermes/ai-x-digest/content', 'apps/daily'):
            for command in (['npm', 'ci'], ['npm', 'run', 'check'], ['npm', 'test']):
                run([MISE, 'exec', 'node@22.23.3', '--', *command], checkout / folder)
        app = checkout / 'apps/daily'
        run([MISE, 'exec', 'node@22.23.3', '--', 'npm', 'run', 'build'], app)
        save(app / 'dist/code.json', {'codeRevision': commit})
        code_artifact(app / 'dist')
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(app / 'dist'), output)
    return {'artifact': str(output), 'codeRevision': commit}


def cloudflare_deployments(bootstrap=False):
    account = os.environ.get('CLOUDFLARE_ACCOUNT_ID', '')
    token = os.environ.get('CLOUDFLARE_API_TOKEN', '')
    if account != ACCOUNT or not token:
        raise ValueError('configured personal Cloudflare account and API token are required')
    url = CLOUDFLARE_API + '/accounts/' + account + '/workers/scripts/pawhouse-daily/deployments'
    deployments, page = [], 1
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


def deploy(publisher, artifact, bundle, origin, command, bootstrap=False):
    manifest = code_artifact(artifact)
    guard(publisher, manifest['codeRevision'], origin, bootstrap)
    expected, _, _, _ = frozen_publication(publisher, bundle)
    live = manifest_at(origin, bootstrap)
    previous_routes = routes(live) if live is not None else set()
    if live is not None and 'sourceRevision' in live and 'codeRevision' not in live:
        previous_routes.discard('/404.html')
    if not previous_routes <= routes(expected):
        raise ValueError('candidate would remove previously deployed reader URLs')
    if live and live.get('publicationRevision') and live['publicationRevision'] != expected['publicationRevision']:
        raise ValueError('code release must retain the current selected publication')
    if command and command[0] == '--':
        command = command[1:]
    if not command:
        raise ValueError('pass the deployment executable and arguments after --')
    if '--assets' in command or '--config' not in command or Path(command[command.index('--config') + 1]).resolve() != Path(artifact).resolve() / 'server/wrangler.json':
        raise ValueError('deployment must use the complete SSR artifact server/wrangler.json')
    try:
        run(command, publisher.repo)
    except (ValueError, RuntimeError, OSError) as error:
        save(publisher.state / 'reader-failure.json', {'origin': origin, 'codeRevision': manifest['codeRevision'], 'phase': 'deploy', 'error': redacted(error)})
        raise
    return {'codeRevision': manifest['codeRevision'], 'phase': 'readerpending'}


def redacted(error):
    return str(error).replace(os.environ.get('CLOUDFLARE_API_TOKEN') or '\0', '[redacted]')


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
    command = sub.add_parser('guard')
    command.add_argument('--candidate', required=True)
    command.add_argument('--origin', required=True)
    command.add_argument('--bootstrap', action='store_true')
    command = sub.add_parser('build')
    command.add_argument('--commit', required=True)
    command = sub.add_parser('deploy')
    command.add_argument('--artifact', required=True)
    command.add_argument('--bundle', required=True)
    command.add_argument('--origin', required=True)
    command.add_argument('--bootstrap', action='store_true')
    command.add_argument('deploy_command', nargs=argparse.REMAINDER)
    command = sub.add_parser('verify')
    command.add_argument('--bundle')
    command.add_argument('--request')
    command.add_argument('--origin', required=True)
    command.add_argument('--code-revision', required=True)
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
            result = deploy(publisher, args.artifact, args.bundle, args.origin, args.deploy_command, args.bootstrap)
        elif args.command == 'build':
            result = build(publisher, args.commit)
        else:
            try:
                result = verify(publisher, args.bundle, args.origin, args.request, args.version, args.code_revision)
            except (ValueError, RuntimeError, OSError, KeyError, ET.ParseError) as error:
                save(publisher.state / 'reader-failure.json', {'origin': args.origin, 'bundle': args.bundle, 'error': redacted(error), 'version': args.version})
                raise
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError, OSError, KeyError, ET.ParseError) as error:
        print(redacted(error), file=sys.stderr)
        raise SystemExit(1)
