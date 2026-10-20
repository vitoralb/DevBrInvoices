import os
import shutil
import tempfile
import requests
from django.conf import settings
from django.test.runner import DiscoverRunner


class BlockedNetworkCallError(RuntimeError):
    """Raised whenever an unmocked remote HTTP call is attempted during test execution."""
    pass


class TempMediaTestRunner(DiscoverRunner):
    """Test runner that:
    1. Isolates MEDIA_ROOT inside a temporary directory during tests to prevent
       test executions from polluting production or development media directories.
    2. Blocks all unmocked external HTTP/HTTPS network calls to ensure no tests can
       leak requests to fiscal providers (Sefin Nacional, Paulistana Prefeitura,
       eSocial, BCB, etc.).
    """

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        self._temp_media_dir = tempfile.mkdtemp(prefix="notas_test_media_")
        self._original_media_root = settings.MEDIA_ROOT
        settings.MEDIA_ROOT = self._temp_media_dir

        # Install global network safety guard
        self._original_session_send = requests.Session.send

        def _guarded_send(session_self, request, **kwargs):
            raise BlockedNetworkCallError(
                f"External network call blocked during tests: {request.method} {request.url}. "
                "All remote calls to fiscal providers, eSocial, and external APIs must be mocked."
            )

        requests.Session.send = _guarded_send

    def teardown_test_environment(self, **kwargs):
        if hasattr(self, "_original_session_send"):
            requests.Session.send = self._original_session_send

        settings.MEDIA_ROOT = self._original_media_root
        if hasattr(self, "_temp_media_dir") and os.path.exists(self._temp_media_dir):
            shutil.rmtree(self._temp_media_dir, ignore_errors=True)
        super().teardown_test_environment(**kwargs)

