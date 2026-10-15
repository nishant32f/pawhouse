"""Release checks must preserve the pinned discovery and RSS contracts."""
import hashlib
import json
import unittest
import xml.etree.ElementTree as ET

import test_daily_release as fixtures


class ReleaseContractTest(unittest.TestCase):
    git = fixtures.ReleaseTest.git
    cli = fixtures.ReleaseTest.cli
    verify = fixtures.ReleaseTest.verify

    def setUp(self):
        fixtures.ReleaseTest.setUp(self)
        discovery = ('<main><h1>Published editions</h1>'
                     '<a href="/editions/2026-10-16/">October 16</a>'
                     '<a href="/editions/2026-10-16/stories/stable-id/">A full story</a></main>')
        for folder in (self.artifact, self.live):
            for route in ('archive', 'search'):
                (folder / route / 'index.html').write_text(discovery)
            rss = ET.parse(folder / 'rss.xml')
            item = rss.getroot().find('./channel/item')
            item.find('guid').set('isPermaLink', 'true')
            ET.SubElement(item, 'link').text = 'https://daily.example/editions/2026-10-16/'
            ET.SubElement(item, 'pubDate').text = 'Fri, 16 Oct 2026 00:00:00 GMT'
            rss.write(folder / 'rss.xml', encoding='unicode')

    def pending_request(self):
        relative = 'digests/x-ai-2026-10-16.md'
        accepted = {'date': '2026-10-16', 'expected_head': self.old, 'files': {
            relative: {'staged': str(self.home / 'accepted.md'), 'before_sha256': None,
                       'staged_sha256': 'a' * 64}}}
        request = self.home / 'accepted.json'
        request.write_text(json.dumps(accepted))
        key = hashlib.sha256(json.dumps(accepted, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        receipt = self.home / 'state/receipts' / (key + '.json')
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(json.dumps({'phase': 'readerpending', 'commit': self.old,
                                       'files': {relative: 'a' * 64}}))
        return request, receipt

    def descendant(self):
        pinned = json.loads((self.artifact / 'deployment.json').read_text())
        pinned['sourceRevision'] = self.old
        (self.artifact / 'deployment.json').write_text(json.dumps(pinned))
        live = json.loads((self.live / 'deployment.json').read_text())
        latest = dict(live['editions'][0], date='2026-10-17', path='/editions/2026-10-17/',
                      readPath='/editions/2026-10-17/read/', stories=[])
        live['editions'].append(latest)
        (self.live / 'deployment.json').write_text(json.dumps(live))
        front = self.live / 'editions/2026-10-17/index.html'
        front.parent.mkdir(parents=True)
        front.write_text('<main>The newer October 17 edition</main>')
        (self.live / 'index.html').write_bytes(front.read_bytes())
        for route in ('archive', 'search'):
            path = self.live / route / 'index.html'
            path.write_text(path.read_text().replace('</main>',
                '<a href="/editions/2026-10-17/">October 17</a></main>'))
        rss = ET.parse(self.live / 'rss.xml')
        extra = ET.SubElement(rss.getroot().find('channel'), 'item')
        ET.SubElement(extra, 'guid', isPermaLink='true').text = 'https://daily.example/editions/2026-10-17/'
        ET.SubElement(extra, 'link').text = 'https://daily.example/editions/2026-10-17/'
        ET.SubElement(extra, 'pubDate').text = 'Sat, 17 Oct 2026 00:00:00 GMT'
        ET.SubElement(extra, 'description').text = '<main>The newer October 17 edition</main>'
        rss.write(self.live / 'rss.xml', encoding='unicode')

    def assert_rejected_without_state_writes(self):
        request, receipt = self.pending_request()
        result = self.cli('verify', '--artifact', str(self.artifact), '--origin', self.origin,
                          '--request', str(request))
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertEqual(json.loads(receipt.read_text())['phase'], 'readerpending')
        self.assertFalse((self.home / 'state/verified-redirects.json').exists())
        self.assertFalse((self.home / 'state/reader-release.json').exists())

    def assert_linkless_discovery_rejected(self, route, descendant=False):
        if descendant:
            self.descendant()
        (self.live / route / 'index.html').write_text('<main>Published editions are coming soon.</main>')
        self.assert_rejected_without_state_writes()

    def test_same_revision_archive_requires_pinned_content(self):
        self.assert_linkless_discovery_rejected('archive')

    def test_same_revision_search_requires_pinned_content(self):
        self.assert_linkless_discovery_rejected('search')

    def test_descendant_archive_requires_pinned_native_links(self):
        self.assert_linkless_discovery_rejected('archive', descendant=True)

    def test_descendant_search_requires_pinned_native_links(self):
        self.assert_linkless_discovery_rejected('search', descendant=True)

    def test_descendant_keeps_pinned_links_and_accepts_newer_links_and_rss_item(self):
        self.descendant()
        request, receipt = self.pending_request()
        result = self.cli('verify', '--artifact', str(self.artifact), '--origin', self.origin,
                          '--request', str(request))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(receipt.read_text())['phase'], 'readerverified')
        self.assertEqual(set(json.loads((self.home / 'state/verified-redirects.json').read_text())['redirects']),
                         {'/digests/x-ai-2026-10-16'})

    def change_rss(self, field, value, attribute=None):
        rss = ET.parse(self.live / 'rss.xml')
        node = rss.getroot().find('./channel/item/' + field)
        if attribute:
            node.set(attribute, value)
        else:
            node.text = value
        rss.write(self.live / 'rss.xml', encoding='unicode')
        self.assert_rejected_without_state_writes()

    def test_rss_guid_host_must_match_pinned_item(self):
        self.change_rss('guid', 'https://wrong.example/editions/2026-10-16/')

    def test_rss_guid_permalink_attribute_must_match_pinned_item(self):
        self.change_rss('guid', 'false', attribute='isPermaLink')

    def test_rss_link_must_match_pinned_item(self):
        self.change_rss('link', 'https://wrong.example/editions/2026-10-16/')

    def test_rss_pubdate_must_match_pinned_item(self):
        self.change_rss('pubDate', 'Sat, 17 Oct 2026 00:00:00 GMT')


if __name__ == '__main__':
    unittest.main()
