"""Shared test fixtures and dependency shims."""

from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

VALIDATION_DEPS = PROJECT_ROOT / ".validation_deps"
if VALIDATION_DEPS.exists() and str(VALIDATION_DEPS) not in sys.path:
    sys.path.insert(0, str(VALIDATION_DEPS))

try:
    import cv2
except ImportError:
    cv2 = types.ModuleType("cv2")
    cv2.FONT_HERSHEY_SIMPLEX = 0
    cv2.LINE_AA = 0
    cv2.rectangle = lambda *args, **kwargs: None
    cv2.putText = lambda *args, **kwargs: None
    cv2.setNumThreads = lambda *args, **kwargs: None
    cv2.imwrite = lambda *args, **kwargs: True
    cv2.imshow = lambda *args, **kwargs: None
    cv2.waitKey = lambda *args, **kwargs: -1
    cv2.destroyAllWindows = lambda *args, **kwargs: None
    cv2.VideoWriter_fourcc = lambda *args: 0
    cv2.VideoCapture = lambda *args, **kwargs: MagicMock()
    cv2.VideoWriter = lambda *args, **kwargs: MagicMock()
    cv2.IMREAD_COLOR = 1
    sys.modules["cv2"] = cv2
