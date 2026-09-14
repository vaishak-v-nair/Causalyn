import unittest

import app
from fastapi.testclient import TestClient


class TestCausalynApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app.api)

    def setUp(self):
        app.WORLD_STATE.reset()
        app.WORLD_STATE.set_file_content("/protected/config.json", {"debug": True, "secret_key": "redacted"})
        app.WORLD_STATE.set_file_content("/app/public/settings.json", {"feature_flag": False, "version": "1.0.0"})

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

    def test_analyze_mode_stays_before_commit(self):
        status, payload = self.request(
            "POST",
            "/api/intents",
            {"intent": "Update the public settings", "execution_mode": "analyze"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["execution_mode"], "analyze")
        self.assertIsNone(payload["commit"])
        self.assertEqual(payload["verification"], "allow")

    def test_providers_endpoint(self):
        status, payload = self.request("GET", "/api/providers")
        self.assertEqual(status, 200)
        self.assertIn("providers", payload)
        self.assertIn("active_provider", payload)
        self.assertTrue(len(payload["providers"]) >= 1)

    def test_files_and_content_endpoints(self):
        status, payload = self.request("GET", "/api/files")
        self.assertEqual(status, 200)
        self.assertEqual(payload["count"], 2)
        self.assertTrue(any(f["path"] == "/protected/config.json" for f in payload["files"]))

        # Test content endpoint
        res = self.client.get("/api/files/content", params={"path": "/protected/config.json"})
        self.assertEqual(res.status_code, 200)
        file_payload = res.json()
        self.assertEqual(file_payload["path"], "/protected/config.json")
        self.assertTrue(file_payload["exists"])
        self.assertTrue(len(file_payload["content"]) > 0)

        # Test traversal security rejection
        res_traversal = self.client.get("/api/files/content", params={"path": "../../../etc/passwd"})
        self.assertEqual(res_traversal.status_code, 403)

    def test_diff_and_audit_endpoints(self):
        status, payload = self.request(
            "POST", "/api/intents",
            {"intent": "Update the public settings to enable diff testing"},
        )
        self.assertEqual(status, 200)
        pipeline_id = payload["pipeline_id"]

        # Diff endpoint
        diff_res = self.client.get(f"/api/diff/{pipeline_id}")
        self.assertEqual(diff_res.status_code, 200)
        diff_payload = diff_res.json()
        self.assertEqual(diff_payload["pipeline_id"], pipeline_id)
        self.assertIn("diffs", diff_payload)

        # Audit endpoint
        audit_res = self.client.get("/api/audit")
        self.assertEqual(audit_res.status_code, 200)
        audit_payload = audit_res.json()
        self.assertEqual(audit_payload["framework"], "EU AI Act (Regulation 2024/1689 Article 10)")
        self.assertIn("records", audit_payload)


if __name__ == "__main__":
    unittest.main()
