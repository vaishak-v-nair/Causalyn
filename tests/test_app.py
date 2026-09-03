import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

import app


class TestCausalynApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), app.CausalynHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.server.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, method, path, body=None):
        connection = HTTPConnection("127.0.0.1", self.port)
        payload = json.dumps(body).encode() if body is not None else None
        connection.request(method, path, payload, {"Content-Type": "application/json"})
        response = connection.getresponse()
        data = json.loads(response.read())
        connection.close()
        return response.status, data

    def test_health_and_state(self):
        status, payload = self.request("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(payload["maturity"], "M1_TOY_PROTOTYPE")
        status, payload = self.request("GET", "/api/state")
        self.assertEqual(status, 200)
        self.assertEqual(payload["file_count"], 2)

    def test_intent_pipeline(self):
        status, payload = self.request(
            "POST", "/api/intents",
            {"intent": "Update the public settings to enable the new feature"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["verification"], "allow")
        self.assertEqual(payload["commit"]["decision"], "committed")

    def test_invalid_intent(self):
        status, payload = self.request("POST", "/api/intents", {"intent": ""})
        self.assertEqual(status, 400)
        self.assertIn("non-empty", payload["error"])


if __name__ == "__main__":
    unittest.main()
