import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import apiverve_client  # noqa: E402

CATALOG = {
    "whoislookup": {
        "title": "WHOIS Lookup", "category": "Domain Data", "description": "WHOIS records for a domain",
        "method": "GET", "path": "/v1/whoislookup",
        "params": [{"name": "domain", "in": "query", "required": True, "type": "string"}],
    },
    "texttopdf": {
        "title": "Text to PDF", "category": "Documents", "description": "Render text as a PDF",
        "method": "POST", "path": "/v1/texttopdf",
        "params": [
            {"name": "text", "in": "body", "required": True, "type": "string"},
            {"name": "format", "in": "query", "required": False, "type": "string"},
        ],
    },
}


class FakeResponse:
    def __init__(self, status, payload):
        self.status = status
        self._body = json.dumps(payload).encode()

    def read(self, *args):
        body, self._body = self._body, b""
        return body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class ClientTests(unittest.TestCase):
    def setUp(self):
        apiverve_client._catalog = CATALOG
        apiverve_client._catalog_at = float("inf")

    def test_fixed_host_and_key_header(self):
        with mock.patch.object(apiverve_client, "_open", return_value=FakeResponse(200, {"status": "ok", "data": {"x": 1}})) as opened:
            self.assertEqual(apiverve_client.call("k-123", "/v1/iplookup", query={"ip": "8.8.8.8", "skip": ""}), {"x": 1})
        request = opened.call_args[0][0]
        self.assertEqual(request.full_url, "https://api.apiverve.com/v1/iplookup?ip=8.8.8.8")
        self.assertEqual(request.get_header("X-api-key"), "k-123")

    def test_rejects_non_v1_path(self):
        with self.assertRaises(apiverve_client.ApiverveError):
            apiverve_client.call("k", "//evil.example/v1/x")

    def test_missing_key(self):
        with self.assertRaises(apiverve_client.ApiverveError):
            apiverve_client.call("", "/v1/iplookup")

    def test_key_redacted_from_output(self):
        with mock.patch.object(apiverve_client, "_open", return_value=FakeResponse(200, {"data": {"echo": "secret-key"}})):
            self.assertEqual(apiverve_client.call("secret-key", "/v1/x"), {"echo": "[redacted]"})

    def test_run_splits_query_and_body(self):
        with mock.patch.object(apiverve_client, "call", return_value={}) as called:
            apiverve_client.run("k", "TextToPDF", {"text": "hi", "format": "a4"})
        self.assertEqual(called.call_args.kwargs, {"method": "POST", "query": {"format": "a4"}, "body": {"text": "hi"}})
        self.assertEqual(called.call_args.args[1], "/v1/texttopdf")

    def test_run_requires_declared_params(self):
        with self.assertRaisesRegex(apiverve_client.ApiverveError, "domain"):
            apiverve_client.run("k", "whoislookup", {})

    def test_run_unknown_api(self):
        with self.assertRaisesRegex(apiverve_client.ApiverveError, "Find APIs"):
            apiverve_client.run("k", "nope", {})

    def test_search_ranks_title_match_first(self):
        self.assertEqual(apiverve_client.search("whois")[0]["api"], "whoislookup")


if __name__ == "__main__":
    unittest.main()
