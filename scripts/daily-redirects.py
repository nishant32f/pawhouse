#!/usr/bin/env python3
"""Prepare, apply and prove the one-time Pawhouse digest redirects.

Apply is a production write and requires explicit deployment authorization.
Its API result never substitutes for verify's HTTP proof before Quartz retirement.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

sys.dont_write_bytecode = True
from publication import Publisher, save

ACCOUNT = '1688bfec49a43a217df10ed33b86e300'
HOST = 'nishantkhurana.me'
READER = 'https://daily.nishantkhurana.me'
NAME = 'pawhouse_daily_legacy'
REF = 'pawhouse_daily_legacy_redirects'
BASE = '/accounts/' + ACCOUNT
ENTRYPOINT = BASE + '/rulesets/phases/http_request_redirect/entrypoint'


def encoded_path(path):
    # Match Cloudflare's literal-byte encoding and uppercase escapes. Leave reserved bytes intact.
    encoded = quote(path, safe="/%:@!$&'()*+,;=[]")
    return re.sub(r'%[0-9a-fA-F]{2}', lambda match: match[0].upper(), encoded)


def source_key(url):
    hostname, separator, path = url.partition('/')
    return hostname + separator + encoded_path(path)


def prepare(filename):
    data = Path(filename).read_bytes()
    inventory = json.loads(data)
    if inventory.get('schemaVersion') != 1 or not re.fullmatch('[a-f0-9]{40}', inventory.get('legacyRevision', '')):
        raise ValueError('requires the pinned U5 inventory')
    expected = {}
    for source in [*inventory['sources'], *inventory['generatedIndexes']]:
        target = '/archive/'
        if source.get('kind') == 'edition':
            from datetime import date
            day = date.fromisoformat(source['date']).isoformat()
            target = '/editions/' + day + '/'
        if source['target'] != target:
            raise ValueError('inventory target differs from its accepted edition or index')
        for path in source['oldPaths']:
            if not path.startswith('/') or path.startswith('//') or any(char in path for char in ('?', '#', '\r', '\n')):
                raise ValueError('invalid old inventory path')
            if path in expected and expected[path] != target:
                raise ValueError('inventory path collision')
            expected[path] = target
    actual = {entry['path']: entry['target'] for entry in inventory['redirects']}
    if actual != expected or len(actual) != len(inventory['redirects']) or not actual:
        raise ValueError('redirect inventory does not exactly cover accepted old paths')
    digest = hashlib.sha256(data).hexdigest()
    description = 'Pawhouse U6 legacy digest redirects, inventory sha256 ' + digest
    items = [{'redirect': {'source_url': HOST + encoded_path(path), 'target_url': READER + target,
                          'status_code': 301, 'include_subdomains': False, 'subpath_matching': False,
                          'preserve_query_string': True, 'preserve_path_suffix': False}}
             for path, target in sorted(actual.items())]
    if len(item_map(items)) != len(items):
        raise ValueError('inventory paths collide after URL encoding')
    return {'schemaVersion': 1, 'accountId': ACCOUNT, 'inventorySha256': digest,
            'legacyRevision': inventory['legacyRevision'], 'publicationId': inventory['publicationId'],
            'compilerRevision': inventory['compilerRevision'],
            'dates': sorted(source['date'] for source in inventory['sources'] if source['kind'] == 'edition'),
            'requiredRoutes': sorted({'/', '/archive/', '/search/', '/rss.xml', '/sitemap.xml'} |
                {route for source in inventory['sources'] if source['kind'] == 'edition'
                 for route in [source['editionPath'], source['readPath'], *[story['path'] for story in source['stories']]]}),
            'list': {'name': NAME, 'description': description, 'kind': 'redirect'},
            'rule': {'ref': REF, 'description': description, 'expression': 'http.request.full_uri in $' + NAME,
                     'action': 'redirect', 'action_parameters': {'from_list': {'name': NAME, 'key': 'http.request.full_uri'}},
                     'enabled': True}, 'items': items}


class APIError(RuntimeError):
    def __init__(self, status):
        self.status = status
        super().__init__('Cloudflare API request failed, HTTP ' + str(status))


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, url):
        return None


class API:
    def __init__(self, token, origin='https://api.cloudflare.com/client/v4'):
        parsed = urlsplit(origin)
        if origin != 'https://api.cloudflare.com/client/v4' and not (parsed.scheme == 'http' and parsed.hostname == '127.0.0.1'):
            raise ValueError('API origin must be Cloudflare or the loopback fixture')
        self.token, self.origin = token, origin
        self.http = build_opener(NoRedirect())

    def request(self, method, path, body=None):
        request = Request(self.origin + path, method=method,
                          data=json.dumps(body).encode() if body is not None else None,
                          headers={'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json'})
        try:
            with self.http.open(request, timeout=30) as response:
                value = json.load(response)
        except HTTPError as error:
            raise APIError(error.code) from None
        except (URLError, OSError, ValueError):
            raise RuntimeError('Cloudflare API transport or JSON response failed') from None
        if value.get('success') is not True:
            raise RuntimeError('Cloudflare API rejected the request')
        return value

    def get(self, path):
        return self.request('GET', path)['result']

    def collection(self, path):
        result, page, cursor, seen = [], 1, None, set()
        while True:
            query = {'per_page': 500 if path.endswith('/items') else 50}
            if cursor:
                query['cursor'] = cursor
            elif page > 1:
                query['page'] = page
            value = self.request('GET', path + ('&' if '?' in path else '?') + urlencode(query))
            result.extend(value['result'])
            info = value.get('result_info', {})
            cursor = info.get('cursors', {}).get('after')
            if cursor:
                if cursor in seen:
                    raise RuntimeError('Cloudflare pagination repeated a cursor')
                seen.add(cursor)
            elif page < info.get('total_pages', 1):
                page += 1
            else:
                return result


def entrypoint(api):
    try:
        return api.get(ENTRYPOINT)
    except APIError as error:
        if error.status == 404:
            return None
        raise


def preflight(plan, api, state):
    token = api.get(BASE + '/tokens/verify')
    if token.get('status') != 'active':
        raise ValueError('Cloudflare token is not active')
    policies = api.get(BASE + '/tokens/' + token['id'])['policies']
    groups = set()
    for policy in policies:
        if policy['effect'] == 'allow' and policy.get('resources', {}).get('com.cloudflare.api.account.' + ACCOUNT) == '*':
            groups.update(group['name'] for group in policy['permission_groups'])
    if not groups.intersection({'Account Filter Lists Edit', 'Account Rule Lists Write'}) or not groups.intersection({'Mass URL Redirects Write', 'Account Rulesets Write'}):
        raise ValueError('token policy does not prove account list and redirect edit permissions')
    zones = api.collection('/zones?' + urlencode({'name': HOST, 'account.id': ACCOUNT}))
    if len(zones) != 1 or zones[0]['account']['id'] != ACCOUNT:
        raise ValueError('main hostname zone is not in the personal account')
    dns = api.collection('/zones/' + zones[0]['id'] + '/dns_records?' + urlencode({'name': HOST}))
    if len(dns) != 1 or not (dns[0]['type'] == 'CNAME' and dns[0]['name'] == HOST and dns[0]['content'].rstrip('.') == 'nishant32f.github.io' and dns[0]['proxied'] is True):
        raise ValueError('main hostname must retain the proxied GitHub Pages CNAME origin')
    lists = api.collection(BASE + '/rules/lists')
    matching = [item for item in lists if item['name'] == NAME]
    if matching and (len(matching) != 1 or state.get('listId') != matching[0]['id'] or any(matching[0].get(key) != value for key, value in plan['list'].items())):
        raise ValueError('unowned or changed dedicated list name collision')
    ruleset = entrypoint(api)
    rules = ruleset['rules'] if ruleset else []
    owned = [rule for rule in rules if rule.get('ref') == REF]
    if owned and (len(owned) != 1 or state.get('ruleId') != owned[0]['id'] or any(owned[0].get(key) != value for key, value in plan['rule'].items())):
        raise ValueError('unowned or changed dedicated rule collision')
    if any(NAME in rule.get('expression', '') or rule.get('action_parameters', {}).get('from_list', {}).get('name') == NAME
           for rule in rules if rule not in owned):
        raise ValueError('another rule references the dedicated list')
    redirect_lists = [item for item in lists if item['kind'] == 'redirect']
    projected_lists = len(redirect_lists) + (0 if matching else 1)
    projected_urls = sum(item['num_items'] for item in redirect_lists if item not in matching) + len(plan['items'])
    projected_rules = len(rules) + (0 if owned else 1)
    if projected_lists > 5 or projected_urls > 10000 or projected_rules > 15:
        raise ValueError('insufficient conservative Cloudflare Free redirect capacity')
    return {'lists': lists, 'ruleset': ruleset, 'capacity': {'lists': projected_lists, 'urls': projected_urls, 'rules': projected_rules},
            'accountId': ACCOUNT, 'originPreserved': True, 'permissionsVerified': True}


def item_map(items):
    return {source_key(item['redirect']['source_url']): {**item['redirect'], 'source_url': source_key(item['redirect']['source_url'])}
            for item in items}


def reader_ready(plan, proof_path, origin=READER):
    proof = json.loads(Path(proof_path).read_text())
    if (proof.get('origin') != READER or proof.get('publicationRevision') != plan['publicationId'] or
            proof.get('compilerRevision') != plan['compilerRevision'] or
            not re.fullmatch('[a-f0-9]{40}', proof.get('codeRevision', '')) or not proof.get('version') or
            sorted(proof.get('dates', [])) != plan['dates'] or
            not set(plan['requiredRoutes']) <= set(proof.get('tested_routes', []))):
        raise ValueError('U4 reader proof does not cover this exact accepted inventory')
    if origin != READER and not (urlsplit(origin).scheme == 'http' and urlsplit(origin).hostname == '127.0.0.1'):
        raise ValueError('alternate reader origin must be the loopback fixture')
    try:
        with build_opener(NoRedirect()).open(origin + '/deployment.json', timeout=30) as response:
            live = json.load(response)
    except (HTTPError, URLError, OSError, ValueError):
        raise ValueError('current reader publication could not be verified') from None
    if any(live.get(field) != proof[field] for field in ('publicationRevision', 'compilerRevision', 'codeRevision')):
        raise ValueError('currently served publication differs from U4 reader proof')


class OperationFailed(RuntimeError):
    pass


def apply(plan, api, state_path, reader_proof, reader_origin=READER):
    state_path = Path(state_path)
    state = json.loads(state_path.read_text()) if state_path.exists() else {'inventorySha256': plan['inventorySha256']}
    if state['inventorySha256'] != plan['inventorySha256']:
        raise ValueError('private ownership state belongs to another inventory')
    reader_ready(plan, reader_proof, reader_origin)
    before = preflight(plan, api, state)
    if not state.get('listId'):
        value = api.request('POST', BASE + '/rules/lists', plan['list'])['result']
        state['listId'] = value['id']
        save(state_path, state)
    path = BASE + '/rules/lists/' + state['listId'] + '/items'
    if state.get('operationId'):
        try:
            wait_operation(api, state['operationId'])
        except OperationFailed:
            state.pop('operationId')
            save(state_path, state)
            raise
        state.pop('operationId')
        save(state_path, state)
    current = api.collection(path)
    desired, present = item_map(plan['items']), item_map(current)
    if len(present) != len(current) or any(desired.get(key) != value for key, value in present.items()):
        raise ValueError('dedicated list contains different redirect items')
    missing = [item for item in plan['items'] if item['redirect']['source_url'] not in present]
    if missing:
        if state.get('ruleId'):
            raise ValueError('active dedicated list differs; stop before modifying live redirects')
        state['operationId'] = api.request('POST', path, missing)['result']['operation_id']
        save(state_path, state)
        try:
            wait_operation(api, state['operationId'])
        except OperationFailed:
            # A failed operation may leave inactive items. A later explicit retry checks them.
            state.pop('operationId')
            save(state_path, state)
            raise
        state.pop('operationId')
        save(state_path, state)
    readback = api.collection(path)
    if len(readback) != len(plan['items']) or item_map(readback) != desired:
        raise ValueError('redirect list readback differs; rule remains inactive')
    ruleset = entrypoint(api)
    prior_rules = before['ruleset']['rules'] if before['ruleset'] else []
    if (ruleset['rules'] if ruleset else []) != prior_rules:
        raise ValueError('redirect rules changed during apply; stop before enabling')
    reader_ready(plan, reader_proof, reader_origin)
    if not state.get('ruleId'):
        if ruleset:
            api.request('POST', BASE + '/rulesets/' + ruleset['id'] + '/rules', plan['rule'])
        else:
            api.request('POST', BASE + '/rulesets', {'name': 'Pawhouse bulk redirects', 'kind': 'root',
                                                  'phase': 'http_request_redirect', 'rules': [plan['rule']]})
        after = entrypoint(api)
        owned = [rule for rule in after['rules'] if rule.get('ref') == REF]
        unrelated = [rule for rule in after['rules'] if rule.get('ref') != REF]
        if unrelated != prior_rules or len(owned) != 1 or any(owned[0].get(key) != value for key, value in plan['rule'].items()):
            raise ValueError('rule readback differs from exact dedicated addition')
        state['ruleId'] = owned[0]['id']
        save(state_path, state)
    return {'accountId': ACCOUNT, 'listId': state['listId'], 'ruleId': state['ruleId'],
            'redirectCount': len(plan['items']), 'apiApplied': True, 'liveVerified': False}


def wait_operation(api, operation):
    for attempt in range(60):
        status = api.get(BASE + '/rules/lists/bulk_operations/' + operation)['status']
        if status == 'completed':
            return
        if status == 'failed':
            raise OperationFailed('Cloudflare redirect list operation failed; rule remains inactive')
        time.sleep(0.1 if api.origin.startswith('http://127.0.0.1') else 1)
    raise RuntimeError('Cloudflare redirect list operation is still pending; resume later')


def http_get(url):
    parsed = urlsplit(url)
    url = urlunsplit(parsed._replace(path=encoded_path(parsed.path)))
    try:
        with build_opener(NoRedirect()).open(Request(url), timeout=30) as response:
            return response.status, response.headers
    except HTTPError as error:
        return error.code, error.headers
    except (URLError, OSError):
        raise RuntimeError('HTTP verification request failed') from None


def verify(plan, source_origin=None, reader_origin=READER):
    origins = [source_origin] if source_origin else ['http://' + HOST, 'https://' + HOST]
    if source_origin and not (urlsplit(source_origin).scheme == 'http' and urlsplit(source_origin).hostname == '127.0.0.1'):
        raise ValueError('alternate verification origin must be the loopback fixture')
    if reader_origin != READER and not (source_origin == reader_origin):
        raise ValueError('alternate reader origin must be the same loopback fixture')
    query = '?pawhouse_redirect=one%20two&repeat=1&repeat=2'
    probes = 0
    for item in plan['items']:
        redirect = item['redirect']
        path = redirect['source_url'].removeprefix(HOST)
        target = reader_origin + redirect['target_url'].removeprefix(READER)
        for origin in origins:
            for suffix in ('', query):
                status, headers = http_get(origin + path + suffix)
                if status != 301:
                    raise ValueError('expected HTTP 301 for ' + origin + path + suffix + ', got ' + str(status))
                if headers.get('Location') != target + suffix:
                    raise ValueError('wrong Location for ' + origin + path + suffix)
                final, _ = http_get(target + suffix)
                if final != 200:
                    raise ValueError('expected final HTTP 200 for ' + target + suffix + ', got ' + str(final))
                probes += 1
    unknown = '/digests/x-ai-1900-01-01'
    if any(item['redirect']['source_url'] == HOST + unknown for item in plan['items']):
        raise ValueError('unknown-date probe unexpectedly exists in accepted inventory')
    for origin in origins:
        for suffix in ('', '.html', '/'):
            status, _ = http_get(origin + unknown + suffix)
            if status != 404:
                raise ValueError('unknown digest date must return HTTP 404')
    return {'inventorySha256': plan['inventorySha256'], 'redirectsVerified': len(plan['items']),
            'redirectProbes': probes, 'unknownDateStatus': 404, 'liveVerified': source_origin is None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'preflight', 'apply', 'verify'])
    parser.add_argument('--inventory', required=True, help='private pinned U5 inventory.json')
    parser.add_argument('--output', help='private JSON plan or proof report')
    parser.add_argument('--reader-proof', default='~/.local/state/pawhouse-publication/reader-release.json', help='U4 exhaustive proof for the exact inventory publication')
    parser.add_argument('--credentials', default='~/.config/pawhouse-daily/cloudflare.json')
    parser.add_argument('--state', default='~/.local/state/pawhouse-publication/daily-redirects.json', help='private owned-resource record; retain for retries')
    args = parser.parse_args()
    token = None
    try:
        plan = prepare(args.inventory)
        if args.command == 'prepare':
            result = plan
        elif args.command == 'verify':
            result = verify(plan)
        else:
            publisher = Publisher()
            spec = importlib.util.spec_from_file_location('daily_release_credentials', Path(__file__).with_name('release-daily-from-pluto.py'))
            credentials = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(credentials)
            token = credentials.credentials_at(args.credentials, publisher)
            api = API(token)
            state = Path(args.state).expanduser().resolve()
            private_path(state, publisher)
            if args.command == 'apply':
                with publisher.locked():
                    proof = Path(args.reader_proof).expanduser().resolve()
                    private_path(proof, publisher)
                    result = apply(plan, api, state, proof)
            else:
                owned = json.loads(state.read_text()) if state.exists() else {}
                if owned and owned.get('inventorySha256') != plan['inventorySha256']:
                    raise ValueError('private ownership state belongs to another inventory')
                checked = preflight(plan, api, owned)
                result = {key: checked[key] for key in ('accountId', 'originPreserved', 'permissionsVerified', 'capacity')}
        if args.output:
            output = Path(args.output).expanduser().resolve()
            private_path(output, Publisher())
            save(output, result)
        print(json.dumps(result, sort_keys=True))
    except (ValueError, RuntimeError, OSError, KeyError, TypeError) as error:
        message = str(error)
        if token:
            message = message.replace(token, '[redacted]')
        print(message, file=sys.stderr)
        raise SystemExit(1)


def private_path(path, publisher):
    for public in (publisher.repo, publisher.vault):
        if path == public or public in path.parents:
            raise ValueError('redirect state and reports must stay outside repository and public vault')


if __name__ == '__main__':
    main()
