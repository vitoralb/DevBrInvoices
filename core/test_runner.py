import os
import shutil
import tempfile
from django.conf import settings
from django.test.runner import DiscoverRunner


class TempMediaTestRunner(DiscoverRunner):
    """Test runner that isolates MEDIA_ROOT inside a temporary directory during tests
    to prevent test executions from polluting production or development media directories.
    """

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        self._temp_media_dir = tempfile.mkdtemp(prefix="notas_test_media_")
        self._original_media_root = settings.MEDIA_ROOT
        settings.MEDIA_ROOT = self._temp_media_dir

    def teardown_test_environment(self, **kwargs):
        settings.MEDIA_ROOT = self._original_media_root
        if hasattr(self, "_temp_media_dir") and os.path.exists(self._temp_media_dir):
            shutil.rmtree(self._temp_media_dir, ignore_errors=True)
        super().teardown_test_environment(**kwargs)

