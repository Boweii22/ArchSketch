"""Tests for Procfile detector."""

import tempfile
from pathlib import Path

import pytest

from archsketch.detectors.procfile import detect_from_procfile
from archsketch.models import TechCategory


def test_detect_web_and_worker():
    with tempfile.NamedTemporaryFile(mode="w", suffix="Procfile", delete=False) as f:
        f.write("web: gunicorn app:app\nworker: celery -A app worker\n")
        f.flush()
        path = Path(f.name)
    try:
        detections = detect_from_procfile(path)
        assert any("web" in d.tech.lower() or d.category == TechCategory.BACKEND for d in detections)
        assert any("worker" in d.tech.lower() or d.category == TechCategory.WORKER for d in detections)
        assert any(d.tech == "Gunicorn" for d in detections)
        assert any(d.tech == "Celery" for d in detections)
    finally:
        path.unlink(missing_ok=True)