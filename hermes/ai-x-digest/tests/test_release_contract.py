"""Negative HTTP proofs preserve full prose, figures, discovery, RSS and real 404s."""
import json
import unittest
import xml.etree.ElementTree as ET
import daily_release_fixtures as fixtures


class ReleaseContractTest(fixtures.Fixture, unittest.TestCase):
    def assert_rejected(self, expected=None):
        request, receipt = self.pending_request()
        result = self.verify('--request', request)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        value = json.loads(receipt.read_text())
        self.assertEqual(value['phase'], 'published')
        self.assertIn('verificationError', value)
        if expected:
            self.assertIn(expected, result.stderr)
        self.assertFalse((self.state / 'verified-redirects.json').exists())
        self.assertFalse((self.state / 'reader-release.json').exists())

    def change(self, route, before, after):
        page = self.live / route
        text = page.read_text()
        self.assertIn(before, text)
        page.write_text(text.replace(before, after))
        self.assert_rejected()

    def test_matching_figures_full_prose_archives_and_rss_verify(self):
        self.assertEqual(self.verify().returncode, 0)

    def test_same_revision_archive_requires_published_links(self):
        (self.live / 'archive/index.html').write_text('<main>Published editions are coming soon.</main>')
        self.assert_rejected('archive')

    def test_same_revision_search_requires_full_text_and_native_links(self):
        (self.live / 'search/index.html').write_text('<main>Published editions are coming soon.</main>')
        self.assert_rejected('search')

    def test_matching_hash_cannot_hide_omitted_archived_route(self):
        (self.live / 'editions/2026-10-16/stories/vendor-benchmark/index.html').unlink()
        self.assert_rejected()

    def test_matching_hash_cannot_hide_omitted_legacy_edition(self):
        (self.live / 'editions/2026-05-10/read/index.html').unlink()
        self.assert_rejected()

    def test_changed_story_image_url_cannot_verify_from_matching_text(self):
        self.change('editions/2026-10-15/stories/gloss-x-import/index.html', 'media.example/original.jpg', 'media.example/unrelated.jpg')

    def test_changed_chart_drawing_cannot_verify_from_matching_labels(self):
        self.change('editions/2026-10-15/read/index.html', 'height:8.333333333333332%', 'height:83.33333333333333%')

    def test_changed_front_image_alt_cannot_verify_from_matching_body(self):
        self.change('editions/2026-10-15/index.html', 'alt="The launch screen"', 'alt="An unrelated screen"')

    def test_changed_image_credit_is_rejected(self):
        self.change('editions/2026-10-15/read/index.html', 'Image: Author.', 'Image: Another.')

    def test_changed_caption_is_rejected(self):
        self.change('editions/2026-10-15/index.html', 'Reported by the company.', 'Independently verified.')

    def test_missing_chart_visible_qualifier_is_rejected(self):
        self.change('editions/2026-10-15/index.html', '~2,500', '2,500')

    def test_changed_chart_raw_value_is_rejected(self):
        self.change('editions/2026-10-15/read/index.html', 'data-chart-value="2500"', 'data-chart-value="25000"')

    def test_changed_chart_raw_qualifier_is_rejected(self):
        self.change('editions/2026-10-15/read/index.html', 'data-chart-qualifier="approximate"', 'data-chart-qualifier="exact"')

    def test_source_relocated_outside_story_does_not_verify(self):
        self.change('editions/2026-10-16/stories/reproducible-test/index.html', 'href="https://example.com/test"', 'href="https://example.com/other"')

    def test_sitemap_cannot_omit_archived_routes(self):
        sitemap = self.live / 'sitemap.xml'
        root = ET.fromstring(sitemap.read_text())
        for child in list(root):
            if '/vendor-benchmark/' in ''.join(child.itertext()):
                root.remove(child)
        sitemap.write_text(ET.tostring(root, encoding='unicode'))
        self.assert_rejected('sitemap')

    def change_rss(self, field, value, attribute=None):
        rss = ET.parse(self.live / 'rss.xml')
        node = rss.getroot().find('./channel/item/' + field)
        if attribute:
            node.set(attribute, value)
        else:
            node.text = value
        rss.write(self.live / 'rss.xml', encoding='unicode')
        self.assert_rejected('RSS')

    def test_rss_guid_host_must_match_pinned_item(self):
        self.change_rss('guid', 'https://wrong.example/editions/2026-10-16/')

    def test_rss_guid_permalink_attribute_must_match_pinned_item(self):
        self.change_rss('guid', 'false', attribute='isPermaLink')

    def test_rss_link_must_match_pinned_item(self):
        self.change_rss('link', 'https://wrong.example/editions/2026-10-16/')

    def test_rss_pubdate_must_match_pinned_item(self):
        self.change_rss('pubDate', 'Sat, 17 Oct 2026 00:00:00 GMT')

    def test_rss_full_body_must_match_accepted_bytes(self):
        self.change_rss('description', '<p>Truncated</p>')

    def test_rss_parse_error_keeps_published_receipt_and_blocks_delivery(self):
        (self.live / 'rss.xml').write_text('<rss>')
        self.assert_rejected()

    def test_rss_mime_is_enforced(self):
        self.server.RequestHandlerClass.func.extensions_map['.xml'] = 'text/plain'
        self.addCleanup(self.server.RequestHandlerClass.func.extensions_map.update, {'.xml': 'application/rss+xml; charset=utf-8'})
        self.assert_rejected('RSS')

    def test_unknown_route_must_return_real404(self):
        path = self.live / 'editions/0001-01-01/stories/not-a-published-story/index.html'
        path.parent.mkdir(parents=True)
        path.write_text('<main>Not found</main>')
        self.assert_rejected('real 404')

    def test_endpoint503_blocks_delivery_and_retains_same_publication(self):
        handler = self.server.RequestHandlerClass.func
        original = handler.do_GET
        def unavailable(request):
            if request.path == '/deployment.json':
                request.send_error(503)
            else:
                original(request)
        handler.do_GET = unavailable
        self.addCleanup(setattr, handler, 'do_GET', original)
        self.assert_rejected()

    def test_wrong_code_identity_is_rejected_separately(self):
        result = self.verify('--code-revision', '0' * 40)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('code revision', result.stderr)


if __name__ == '__main__':
    unittest.main()
