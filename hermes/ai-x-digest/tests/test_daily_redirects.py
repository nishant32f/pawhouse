from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from urllib.parse import parse_qs, quote, urlsplit

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('daily_redirects', ROOT / 'scripts/daily-redirects.py')
redirects = importlib.util.module_from_spec(spec)
spec.loader.exec_module(redirects)


@contextmanager
def server(handler):
    http = ThreadingHTTPServer(('127.0.0.1', 0), handler)
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    try:
        yield 'http://127.0.0.1:' + str(http.server_port)
    finally:
        http.shutdown()
        http.server_close()
        thread.join()


class RedirectTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        source = {'kind': 'edition', 'date': '2026-10-15', 'oldPaths': ['/digests/x-ai-2026-10-15', '/alias.html'], 'target': '/editions/2026-10-15/', 'editionPath': '/editions/2026-10-15/', 'readPath': '/editions/2026-10-15/read/', 'stories': [{'path': '/editions/2026-10-15/stories/one/'}]}
        self.inventory = self.root / 'inventory.json'
        self.inventory.write_text(json.dumps({'schemaVersion': 1, 'legacyRevision': 'a' * 40,
            'publicationId': 'b' * 64, 'compilerRevision': 'c' * 40, 'sources': [source],
            'generatedIndexes': [{'oldPaths': ['/digests', '/digests/'], 'target': '/archive/'}],
            'redirects': [{'path': '/alias.html', 'target': source['target']},
                          {'path': '/digests', 'target': '/archive/'},
                          {'path': '/digests/', 'target': '/archive/'},
                          {'path': '/digests/x-ai-2026-10-15', 'target': source['target']}]}))

    def plan(self):
        return redirects.prepare(self.inventory)

    def test_list_readback_follows_cloudflare_500_item_cursor_limit(self):
        rows = [{'id': str(index)} for index in range(619)]
        queries = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                query = parse_qs(urlsplit(self.path).query)
                queries.append(query)
                size = int(query['per_page'][0])
                if size > 500:
                    self.send_response(400)
                    self.end_headers()
                    return
                start = int(query.get('cursor', ['0'])[0])
                end = start + size
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'result': rows[start:end],
                    'result_info': {'cursors': {'after': str(end) if end < len(rows) else None}}}).encode())
        with server(Handler) as origin:
            result = redirects.API('token', origin).collection('/accounts/account/rules/lists/list/items')
        self.assertEqual(result, rows)
        self.assertEqual(len(queries), 2)
        self.assertEqual(queries[1]['cursor'], ['500'])

    def test_inventory_is_exact_and_never_invents_missing_dates(self):
        plan = self.plan()
        self.assertEqual(len(plan['items']), 4)
        self.assertEqual(plan['items'][0]['redirect'], {
            'source_url': 'nishantkhurana.me/alias.html',
            'target_url': 'https://daily.nishantkhurana.me/editions/2026-10-15/',
            'status_code': 301, 'include_subdomains': False, 'subpath_matching': False,
            'preserve_query_string': True, 'preserve_path_suffix': False})
        value = json.loads(self.inventory.read_text())
        value['redirects'].append({'path': '/digests/x-ai-2099-01-01', 'target': '/editions/2099-01-01/'})
        self.inventory.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, 'inventory'):
            self.plan()

    def proof(self):
        path = self.root / 'reader-release.json'
        path.write_text(json.dumps({'origin': redirects.READER, 'publicationRevision': 'b' * 64,
            'compilerRevision': 'c' * 40, 'codeRevision': 'd' * 40, 'version': 'worker-version',
            'dates': ['2026-10-15'], 'tested_routes': ['/', '/archive/', '/search/', '/rss.xml', '/sitemap.xml',
                '/editions/2026-10-15/', '/editions/2026-10-15/read/', '/editions/2026-10-15/stories/one/']}))
        return path

    def test_reader_proof_and_still_served_publication_are_required_before_writes(self):
        state, handler = self.api_fixture()
        with server(handler) as origin:
            api = redirects.API('token', origin)
            with self.assertRaises((ValueError, FileNotFoundError)):
                redirects.apply(self.plan(), api, self.root / 'state.json', self.root / 'missing.json', origin)
            proof = self.proof()
            value = json.loads(proof.read_text())
            value['tested_routes'].remove('/editions/2026-10-15/stories/one/')
            proof.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, 'proof'):
                redirects.apply(self.plan(), api, self.root / 'state.json', proof, origin)
            state['publication'] = 'e' * 64
            with self.assertRaisesRegex(ValueError, 'publication'):
                redirects.apply(self.plan(), api, self.root / 'state.json', self.proof(), origin)
        self.assertEqual(state['writes'], [])

    def api_fixture(self, fail=False):
        state = {'lists': [], 'items': [], 'rules': [{'id': 'other', 'ref': 'unrelated', 'action': 'redirect', 'enabled': True}],
                 'writes': [], 'fail': fail, 'polls': 0, 'publication': 'b' * 64, 'proxied': True, 'origin': 'nishant32f.github.io', 'denied': False, 'permissions': True, 'corrupt_readback': False, 'normalize_unicode': False, 'requests': [], 'policy_read': True}
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                self.dispatch('GET')

            def do_POST(self):
                self.dispatch('POST')

            def do_PATCH(self):
                self.dispatch('PATCH')

            def dispatch(self, method):
                path = urlsplit(self.path).path
                state['requests'].append((method, path))
                payload = json.loads(self.rfile.read(int(self.headers.get('Content-Length', '0'))) or b'null')
                if method != 'GET':
                    state['writes'].append((method, path, payload))
                account = '/accounts/' + redirects.ACCOUNT
                if path == account or path.startswith('/user/'):
                    self.send_response(403 if path == account else 401)
                    self.end_headers()
                    return
                if not state['policy_read'] and path == account + '/tokens/token-id':
                    self.send_response(403)
                    self.end_headers()
                    return
                if state['denied'] and path == account + '/rules/lists':
                    self.send_response(403)
                    self.end_headers()
                    self.wfile.write(b'private-token must never be copied into errors')
                    return
                if path == '/deployment.json':
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(json.dumps({'publicationRevision': state['publication'], 'compilerRevision': 'c' * 40, 'codeRevision': 'd' * 40}).encode())
                    return
                if path == account + '/tokens/verify':
                    value = {'id': 'token-id', 'status': 'active'}
                elif path == account + '/tokens/token-id':
                    value = {'policies': [{'effect': 'allow', 'resources': {'com.cloudflare.api.account.' + redirects.ACCOUNT: '*'},
                        'permission_groups': [{'name': 'Account Filter Lists Edit'}, {'name': 'Mass URL Redirects Write'}] if state['permissions'] else []}]}
                elif path == '/zones':
                    value = [{'id': 'zone', 'name': 'nishantkhurana.me', 'account': {'id': redirects.ACCOUNT}}]
                elif path == '/zones/zone/dns_records':
                    value = [{'type': 'CNAME', 'name': 'nishantkhurana.me', 'content': state['origin'], 'proxied': state['proxied']}]
                elif path == account + '/rules/lists':
                    if method == 'POST':
                        state['lists'].append(dict(payload, id='owned-list', num_items=0))
                        value = state['lists'][-1]
                    else:
                        value = state['lists']
                elif path == account + '/rules/lists/owned-list/items':
                    if method == 'POST':
                        state['pending'] = payload
                        value = {'operation_id': 'operation'}
                    else:
                        value = state['items']
                elif path == account + '/rules/lists/bulk_operations/operation':
                    state['polls'] += 1
                    status = 'pending' if state['polls'] % 2 else ('failed' if state['fail'] else 'completed')
                    if status == 'completed':
                        state['items'].extend(state.pop('pending', []))
                        if state['normalize_unicode']:
                            for item in state['items']:
                                source = item['redirect']['source_url']
                                item['redirect']['source_url'] = quote(source, safe='/%,:').replace('%E2%80%94', '%e2%80%94')
                        if state['corrupt_readback']:
                            state['items'][0]['redirect']['target_url'] = 'https://wrong.example/'
                        state['lists'][0]['num_items'] = len(state['items'])
                    value = {'status': status}
                elif path == account + '/rulesets/phases/http_request_redirect/entrypoint':
                    value = {'id': 'entrypoint', 'rules': state['rules']}
                elif path == account + '/rulesets/entrypoint/rules' and method == 'POST':
                    state['rules'].append(dict(payload, id='owned-rule'))
                    value = {'id': 'entrypoint', 'rules': state['rules']}
                else:
                    raise AssertionError((method, path, payload))
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'result': value}).encode())
        return state, Handler

    def test_apply_waits_readbacks_preserves_other_rules_and_retry_is_idempotent(self):
        state, handler = self.api_fixture()
        original = copy.deepcopy(state['rules'])
        with server(handler) as origin:
            api = redirects.API('private-token', origin)
            result = redirects.apply(self.plan(), api, self.root / 'state.json', self.proof(), origin)
            writes = len(state['writes'])
            self.assertEqual(redirects.apply(self.plan(), api, self.root / 'state.json', self.proof(), origin), result)
        self.assertEqual(len(state['writes']), writes)
        self.assertEqual(state['rules'][:1], original)
        self.assertEqual(len(state['rules']), 2)
        self.assertTrue(state['rules'][-1]['enabled'])
        self.assertGreaterEqual(state['polls'], 2)
        self.assertEqual(state['items'], self.plan()['items'])
        self.assertTrue(all(method == 'POST' for method, _, _ in state['writes']))
        self.assertIn(('GET', '/accounts/' + redirects.ACCOUNT + '/tokens/verify'), state['requests'])
        self.assertIn(('GET', '/accounts/' + redirects.ACCOUNT + '/tokens/token-id'), state['requests'])
        self.assertFalse(any(path.startswith('/user/') for _, path in state['requests']))

    def test_async_failure_never_enables_a_rule_and_owned_list_can_resume(self):
        state, handler = self.api_fixture(fail=True)
        original = copy.deepcopy(state['rules'])
        with server(handler) as origin:
            api = redirects.API('private-token', origin)
            with self.assertRaisesRegex(RuntimeError, 'failed'):
                redirects.apply(self.plan(), api, self.root / 'state.json', self.proof(), origin)
            self.assertEqual(state['rules'], original)
            self.assertEqual(len(state['lists']), 1)
            state['fail'] = False
            redirects.apply(self.plan(), api, self.root / 'state.json', self.proof(), origin)
        self.assertEqual(len(state['lists']), 1)
        self.assertEqual(state['rules'][:1], original)
        self.assertEqual(len(state['rules']), 2)

    def test_completed_operation_with_wrong_readback_cannot_enable_rule(self):
        state, handler = self.api_fixture()
        state['corrupt_readback'] = True
        original = copy.deepcopy(state['rules'])
        with server(handler) as origin:
            with self.assertRaisesRegex(ValueError, 'readback'):
                redirects.apply(self.plan(), redirects.API('token', origin), self.root / 'state.json', self.proof(), origin)
        self.assertEqual(state['rules'], original)
        self.assertFalse(any('/rulesets/' in path for _, path, _ in state['writes']))

    def test_preflight_refuses_unproxied_changed_origin_missing_permission_capacity_and_403(self):
        for change, message in [({'proxied': False}, 'CNAME'), ({'origin': 'another-origin.example'}, 'CNAME'),
                                ({'permissions': False}, 'permissions'), ({'denied': True}, '403'), ({'policy_read': False}, '403'),
                                ({'lists': [{'id': 'other', 'name': 'other', 'kind': 'redirect', 'num_items': 10000}]}, 'capacity')]:
            with self.subTest(change=change):
                state, handler = self.api_fixture()
                state.update(change)
                with server(handler) as origin:
                    with self.assertRaisesRegex((ValueError, RuntimeError), message) as caught:
                        redirects.apply(self.plan(), redirects.API('private-token', origin), self.root / 'state.json', self.proof(), origin)
                    self.assertNotIn('private-token', str(caught.exception))
                self.assertEqual(state['writes'], [])

    def test_unowned_list_collision_fails_without_writes(self):
        state, handler = self.api_fixture()
        state['lists'] = [dict(self.plan()['list'], id='unowned', num_items=0)]
        with server(handler) as origin:
            with self.assertRaisesRegex(ValueError, 'unowned'):
                redirects.apply(self.plan(), redirects.API('token', origin), self.root / 'state.json', self.proof(), origin)
        self.assertEqual(state['writes'], [])

    def test_api_normalized_unicode_alias_readback_allows_exact_idempotent_retry(self):
        alias = '/AI-Digest-\u2014-Apr-01,-2026-Evening'
        inventory = json.loads(self.inventory.read_text())
        inventory['sources'][0]['oldPaths'].append(alias)
        inventory['redirects'].append({'path': alias, 'target': '/editions/2026-10-15/'})
        self.inventory.write_text(json.dumps(inventory))
        state, handler = self.api_fixture()
        state['normalize_unicode'] = True
        with server(handler) as origin:
            api = redirects.API('token', origin)
            redirects.apply(self.plan(), api, self.root / 'state.json', self.proof(), origin)
            writes = len(state['writes'])
            redirects.apply(self.plan(), api, self.root / 'state.json', self.proof(), origin)
            self.assertEqual(len(state['writes']), writes)
        items = self.plan()['items']
        self.assertTrue(all(item['redirect']['source_url'].isascii() for item in items))
        self.assertTrue(any('%E2%80%94' in item['redirect']['source_url'] for item in items))

    def test_unicode_inventory_alias_uses_encoded_http_path_and_preserves_query_bytes(self):
        alias = '/AI-Digest-\u2014-Apr-01,-2026-Evening'
        inventory = json.loads(self.inventory.read_text())
        inventory['sources'][0]['oldPaths'].append(alias)
        inventory['redirects'].append({'path': alias, 'target': '/editions/2026-10-15/'})
        self.inventory.write_text(json.dumps(inventory))
        plan = self.plan()
        # Use the inventoried Unicode spelling even if the prepared API item is encoded.
        for item in plan['items']:
            if quote(alias, safe='/,') in item['redirect']['source_url']:
                item['redirect']['source_url'] = redirects.HOST + alias
        mapping = {quote(item['redirect']['source_url'].removeprefix(redirects.HOST), safe='/%,'):
                   item['redirect']['target_url'].removeprefix(redirects.READER) for item in plan['items']}
        seen = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                seen.append(self.path)
                url = urlsplit(self.path)
                if url.path in mapping:
                    self.send_response(301)
                    self.send_header('Location', 'http://' + self.headers['Host'] + mapping[url.path] +
                                     ('?' + url.query if url.query else ''))
                elif url.path.startswith(('/archive/', '/editions/')):
                    self.send_response(200)
                else:
                    self.send_response(404)
                self.end_headers()
        with server(Handler) as origin:
            self.assertEqual(redirects.verify(plan, origin, origin)['redirectsVerified'], 5)
            query = '?value=already%2Fencoded&space=one%20two&repeat=1&repeat=2'
            status, _ = redirects.http_get(origin + alias + query)
            self.assertEqual(status, 301)
        self.assertIn(quote(alias, safe='/,') + query, seen)
        self.assertFalse(any('%252F' in path or '%2520' in path for path in seen))

    def test_verifier_requires_real_301_exact_location_query_and_final_200(self):
        state = {'status': 200, 'wrong': False, 'final': 200}
        plan = self.plan()
        mapping = {item['redirect']['source_url'].removeprefix('nishantkhurana.me'): item['redirect']['target_url'].removeprefix(redirects.READER) for item in plan['items']}
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                url = urlsplit(self.path)
                if url.path.startswith(('/archive/', '/editions/')):
                    self.send_response(state['final'])
                elif url.path in mapping:
                    self.send_response(state['status'])
                    target = '/wrong' if state['wrong'] else mapping[url.path]
                    self.send_header('Location', 'http://' + self.headers['Host'] + target + ('?' + url.query if url.query else ''))
                else:
                    self.send_response(404)
                self.end_headers()
                self.wfile.write(b'fixture')
        with server(Handler) as origin:
            with self.assertRaisesRegex(ValueError, '301'):
                redirects.verify(plan, origin, origin)
            state['status'] = 301
            state['wrong'] = True
            with self.assertRaisesRegex(ValueError, 'Location'):
                redirects.verify(plan, origin, origin)
            state['wrong'] = False
            state['final'] = 404
            with self.assertRaisesRegex(ValueError, '200'):
                redirects.verify(plan, origin, origin)
            state['final'] = 200
            result = redirects.verify(plan, origin, origin)
            self.assertEqual(result['redirectsVerified'], 4)
            self.assertEqual(result['unknownDateStatus'], 404)
