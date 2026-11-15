"""Verify fetches the live routes concurrently and still checks every one, and one failed route fails it."""
from collections import Counter
import json
import threading
import time
import unittest
from unittest.mock import patch
import urllib.error
import daily_release_fixtures as fixtures

MISSING = '/editions/0001-01-01/stories/not-a-published-story/'


class ParallelFetchTest(fixtures.Fixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.original = fixtures.release.fetch
        self.fetched, self.lock = [], threading.Lock()

    def verify_with(self, fetch):
        from publication import Publisher
        with patch.dict('os.environ', self.env), patch.object(fixtures.release, 'fetch', fetch):
            return fixtures.release.verify_publication(Publisher(), self.bundle, self.runtime_origin, self.actual_code)

    def recording(self, origin, route):
        with self.lock:
            self.fetched.append(route)
        return self.original(origin, route)

    def test_every_route_is_fetched_once_and_checked(self):
        result = self.verify_with(self.recording)
        counts = Counter(self.fetched)
        self.assertEqual({route: n for route, n in counts.items() if n != 1}, {})
        tested = result['tested_routes']
        self.assertEqual(len(tested), len(set(tested)))
        self.assertEqual(set(tested), set(self.fetched) - {'/deployment.json'})
        live = json.loads(self.original(self.runtime_origin, '/deployment.json')[0])['routes']
        self.assertEqual(set(tested) - {MISSING}, set(live) - {'/deployment.json'})

    def test_pages_are_fetched_concurrently(self):
        active, peak = [0], [0]
        def slow(origin, route):
            with self.lock:
                active[0] += 1
                peak[0] = max(peak[0], active[0])
            try:
                time.sleep(0.05)
                return self.original(origin, route)
            finally:
                with self.lock:
                    active[0] -= 1
        self.verify_with(slow)
        self.assertGreater(peak[0], 1)

    def test_one_failing_route_fails_verify(self):
        live = json.loads(self.original(self.runtime_origin, '/deployment.json')[0])['routes']
        story = sorted(route for route in live if '/stories/' in route)[-1]
        def failing(origin, route):
            if route == story:
                raise urllib.error.HTTPError(origin + route, 503, 'Service Unavailable', {}, None)
            return self.recording(origin, route)
        with self.assertRaises(urllib.error.HTTPError) as caught:
            self.verify_with(failing)
        self.assertEqual(caught.exception.code, 503)
        self.assertNotIn('/rss.xml', self.fetched)


if __name__ == '__main__':
    unittest.main()
