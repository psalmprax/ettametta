import pytest
#!/usr/bin/env python3
"""
Test Remotion Service on Remote
=============================
"""

import os
import sys
import shutil

PROJECT_DIR = "/app" if os.path.exists("/app") else "/root/ettametta"
sys.path.insert(0, PROJECT_DIR)

os.environ["DEBUG"] = "true"

STUDIO_PATH = os.path.join(PROJECT_DIR, "apps/remotion-studio")

_REMOTION_CLI = shutil.which("npx") and os.path.exists(os.path.join(STUDIO_PATH, "node_modules", ".bin", "remotion"))
pytestmark = pytest.mark.skipif(not _REMOTION_CLI, reason="Remotion CLI not available")

import pytest


def test_remotion_available():
    assert _REMOTION_CLI, "Remotion CLI not available on this server"
