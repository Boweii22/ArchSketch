"""Tests for Gradle detector."""

import tempfile
from pathlib import Path

import pytest

from archsketch.detectors.gradle import detect_from_gradle
from archsketch.models import TechCategory


def test_detect_spring_boot_gradle():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".gradle", delete=False) as f:
        f.write("""
plugins { id 'org.springframework.boot' version '3.0.0' }
dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web'
}
""")
        f.flush()
        path = Path(f.name)
    try:
        detections = detect_from_gradle(path)
        assert any(d.tech == "Spring Boot" for d in detections)
        assert any(d.category == TechCategory.BACKEND for d in detections)
    finally:
        path.unlink(missing_ok=True)
