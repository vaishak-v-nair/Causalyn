import os
import unittest
from unittest.mock import patch

from causalyn.config import RuntimeSettings
from causalyn.model.provider import (
    DisabledModelProvider,
    ModelProviderDisabled,
    ModelRequest,
    create_model_provider,
)


class TestBackendFramework(unittest.TestCase):
    def test_settings_are_local_and_safe_by_default(self):
        with patch.dict(os.environ, {}, clear=True):
            settings = RuntimeSettings.from_env()
        self.assertEqual(settings.host, "127.0.0.1")
        self.assertEqual(settings.port, 8000)
        self.assertFalse(settings.model_enabled)
        self.assertIsNone(settings.model_provider)

    def test_invalid_port_falls_back_to_local_default(self):
        with patch.dict(os.environ, {"CAUSALYN_PORT": "not-a-port"}, clear=True):
            self.assertEqual(RuntimeSettings.from_env().port, 8000)

    def test_model_provider_is_disabled_without_network_call(self):
        provider = create_model_provider()
        self.assertIsInstance(provider, DisabledModelProvider)
        with self.assertRaises(ModelProviderDisabled):
            provider.generate(ModelRequest("hello"))

    def test_enabling_without_registered_provider_fails_closed(self):
        with self.assertRaises(ValueError):
            create_model_provider(enabled=True)


if __name__ == "__main__":
    unittest.main()
