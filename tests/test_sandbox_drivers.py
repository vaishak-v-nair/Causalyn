"""Unit tests for Pluggable Sandbox Drivers and Interception Contracts (Phase 1)."""

import asyncio
import os
import unittest

from causalyn.api.contracts import (
    ActionType,
    GateDecision,
    InterceptActionRequest,
    InterceptActionResponse,
)
from causalyn.shadow.drivers import (
    DockerDriver,
    E2BDriver,
    LocalMemoryDriver,
    get_sandbox_driver,
)


class TestSandboxDrivers(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.driver = LocalMemoryDriver(
            initial_files={
                "/app/config.json": {"mode": "production", "port": 8080},
                "/app/server.py": "def start():\n    print('online')\n",
            }
        )

    async def test_contracts_schema_validation(self):
        req = InterceptActionRequest(
            session_id="sess-123",
            request_id="req-456",
            agent_framework="claude_code",
            action_type=ActionType.FILE_WRITE,
            target_path="/app/config.json",
            payload={"content": "{\"mode\": \"staging\"}"},
        )
        self.assertEqual(req.session_id, "sess-123")
        self.assertEqual(req.action_type, ActionType.FILE_WRITE)

        resp = InterceptActionResponse(
            decision=GateDecision.ALLOW,
            paradox_index=0.0,
            reason="All invariants satisfied",
            execution_time_ms=12.5,
            unified_diffs={"/app/config.json": "+ staging"},
        )
        self.assertEqual(resp.decision, GateDecision.ALLOW)
        self.assertEqual(resp.paradox_index, 0.0)

    async def test_local_memory_driver_file_write_and_diff(self):
        sandbox_id = await self.driver.provision()
        self.assertIn(sandbox_id, self.driver.sandboxes)

        action = InterceptActionRequest(
            session_id="sess-01",
            request_id="req-01",
            action_type=ActionType.FILE_WRITE,
            target_path="/app/config.json",
            payload={"content": '{\n  "mode": "staging",\n  "port": 9000\n}'},
        )

        result = await self.driver.execute_action(sandbox_id, action)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("/app/config.json", result.files_modified)
        self.assertIn("/app/config.json", result.unified_diffs)
        self.assertIn("-  \"port\": 8080", result.unified_diffs["/app/config.json"])
        self.assertIn("+  \"port\": 9000", result.unified_diffs["/app/config.json"])

        # Clean annihilation
        await self.driver.annihilate(sandbox_id)
        self.assertNotIn(sandbox_id, self.driver.sandboxes)

    async def test_local_memory_driver_file_delete(self):
        sandbox_id = await self.driver.provision()
        action = InterceptActionRequest(
            session_id="sess-02",
            request_id="req-02",
            action_type=ActionType.FILE_DELETE,
            target_path="/app/server.py",
        )
        result = await self.driver.execute_action(sandbox_id, action)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("/app/server.py", result.files_deleted)
        self.assertIn("/app/server.py", result.unified_diffs)
        await self.driver.annihilate(sandbox_id)

    async def test_local_memory_driver_watchdog_timeout(self):
        # Temporarily shorten watchdog for fast test execution
        old_timeout = self.driver.DEFAULT_WATCHDOG_TIMEOUT_SECONDS
        self.driver.DEFAULT_WATCHDOG_TIMEOUT_SECONDS = 0.5
        try:
            sandbox_id = await self.driver.provision()
            action = InterceptActionRequest(
                session_id="sess-timeout",
                request_id="req-timeout",
                action_type=ActionType.SHELL_COMMAND,
                payload={"command": "python -c \"import time; time.sleep(5)\""},
            )
            result = await self.driver.execute_action(sandbox_id, action)
            self.assertEqual(result.exit_code, 124)
            self.assertIn("timed out", result.stderr.lower())
            await self.driver.annihilate(sandbox_id)
        finally:
            self.driver.DEFAULT_WATCHDOG_TIMEOUT_SECONDS = old_timeout

    async def test_driver_factory(self):
        mem = get_sandbox_driver("memory")
        self.assertIsInstance(mem, LocalMemoryDriver)
        docker = get_sandbox_driver("docker")
        self.assertIsInstance(docker, DockerDriver)
        e2b = get_sandbox_driver("e2b")
        self.assertIsInstance(e2b, E2BDriver)
        with self.assertRaises(ValueError):
            get_sandbox_driver("nonexistent_cloud")

    async def test_e2b_fails_closed_without_credentials(self):
        e2b = E2BDriver(api_key="")
        with self.assertRaises(RuntimeError) as ctx:
            await e2b.provision()
        self.assertIn("E2B_API_KEY is not set", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
