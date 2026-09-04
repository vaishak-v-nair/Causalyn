import unittest
import tempfile
import os
import shutil
from causalyn.model.world_state import WorldStateManager
from causalyn.harness.context import HarnessContext
from causalyn.shadow.executor import ShadowExecutor

class TestHarnessContext(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for the world state
        self.temp_dir = tempfile.mkdtemp()
        self.world_state_manager = WorldStateManager(self.temp_dir)
        self.harness_context = HarnessContext(self.world_state_manager)
        self.shadow_executor = ShadowExecutor(self.world_state_manager, self.harness_context)

    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.temp_dir)

    def test_initial_state(self):
        self.assertIsNone(self.harness_context.get_intent())
        self.assertEqual(self.harness_context.get_state(), {})

    def test_set_and_get_intent(self):
        self.harness_context.set_intent("test intent")
        self.assertEqual(self.harness_context.get_intent(), "test intent")

    def test_update_and_get_state(self):
        self.harness_context.update_state("key", "value")
        self.assertEqual(self.harness_context.get_state("key"), "value")
        self.assertEqual(self.harness_context.get_state(), {"key": "value"})

    def test_register_and_execute_tool(self):
        def dummy_tool(x):
            return x * 2
        self.harness_context.register_tool("dummy", dummy_tool)
        result = self.harness_context.execute_tool("dummy", 5)
        self.assertEqual(result, 10)

    def test_shadow_mode_toggle(self):
        # Initially not in shadow
        self.assertFalse(self.harness_context._in_shadow)
        # Enter shadow mode via the shadow executor
        self.shadow_executor.enter_shadow_mode()
        # The harness context should be set to shadow mode by the executor
        self.assertTrue(self.harness_context._in_shadow)
        # Exit shadow mode
        self.shadow_executor.exit_shadow_mode(commit=False)
        self.assertFalse(self.harness_context._in_shadow)

    def test_file_operations_in_shadow(self):
        # Enter shadow mode
        self.shadow_executor.enter_shadow_mode()
        # Write a file
        self.harness_context.write_file("/test.txt", "Hello World")
        # Check that the file exists in the shadow directory
        shadow_file = os.path.join(self.shadow_executor.shadow_dir, "test.txt")
        self.assertTrue(os.path.exists(shadow_file))
        with open(shadow_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, "Hello World")
        # Read the file via the harness context
        read_content = self.harness_context.read_file("/test.txt")
        self.assertEqual(read_content, "Hello World")
        # Delete the file
        self.harness_context.delete_file("/test.txt")
        self.assertFalse(os.path.exists(shadow_file))
        # Exit shadow mode
        self.shadow_executor.exit_shadow_mode(commit=False)

    def test_path_traversal_is_rejected(self):
        with self.assertRaises(ValueError):
            self.harness_context._resolve_path("/../../outside.txt")

if __name__ == '__main__':
    unittest.main()