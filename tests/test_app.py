import unittest

import app
from fastapi.testclient import TestClient


class TestCausalynApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app.api)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def request(self, method, path, body=None):
        response = self.client.request(method, path, json=body)
        return response.status_code, response.json()

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
        pipeline_id = payload["pipeline_id"]
        status, payload = self.request("GET", "/api/pipelines")
        self.assertEqual(status, 200)
        self.assertTrue(payload["pipelines"])
        self.assertIn(pipeline_id, [item["pipeline_id"] for item in payload["pipelines"]])

    def test_invalid_intent(self):
        status, payload = self.request("POST", "/api/intents", {"intent": ""})
        self.assertEqual(status, 422)
        self.assertEqual(payload["error"]["code"], "validation_error")


if __name__ == "__main__":
    unittest.main()
