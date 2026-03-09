"""Tests for the scanner module."""

import tempfile
from pathlib import Path

import pytest

from archsketch.scanner import scan_directory, should_skip_dir


def test_should_skip_dir():
    """Test directory skip logic."""
    assert should_skip_dir("node_modules") is True
    assert should_skip_dir(".git") is True
    assert should_skip_dir("__pycache__") is True
    assert should_skip_dir("venv") is True
    assert should_skip_dir("src") is False
    assert should_skip_dir("app") is False


def test_scan_empty_directory():
    """Test scanning an empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = scan_directory(tmpdir)
        assert result.root_path == Path(tmpdir).resolve()
        assert len(result.files) == 0


def test_scan_with_package_json():
    """Test scanning a directory with package.json."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pkg_path = Path(tmpdir) / "package.json"
        pkg_path.write_text('{"name": "test"}')
        
        result = scan_directory(tmpdir)
        assert result.has_file("package.json")
        assert len(result.get_files("package.json")) == 1


def test_scan_with_docker_compose():
    """Test scanning a directory with docker-compose.yml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        compose_path = Path(tmpdir) / "docker-compose.yml"
        compose_path.write_text("version: '3'\nservices: {}")
        
        result = scan_directory(tmpdir)
        assert result.has_file("docker-compose.yml")


def test_scan_with_dockerfile():
    """Test scanning a directory with Dockerfile."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dockerfile_path = Path(tmpdir) / "Dockerfile"
        dockerfile_path.write_text("FROM python:3.11")
        
        result = scan_directory(tmpdir)
        assert result.has_file("Dockerfile")


def test_scan_with_env_file():
    """Test scanning a directory with .env file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".env"
        env_path.write_text("DATABASE_URL=postgres://localhost/db")
        
        result = scan_directory(tmpdir)
        assert result.has_file(".env")


def test_scan_skips_node_modules():
    """Test that node_modules is skipped."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create node_modules with a package.json inside
        nm_dir = Path(tmpdir) / "node_modules" / "some-pkg"
        nm_dir.mkdir(parents=True)
        (nm_dir / "package.json").write_text("{}")
        
        # Create a root package.json
        (Path(tmpdir) / "package.json").write_text('{"name": "root"}')
        
        result = scan_directory(tmpdir)
        # Should only find the root package.json
        assert len(result.get_files("package.json")) == 1


def test_scan_nonexistent_directory():
    """Test scanning a non-existent directory raises error."""
    with pytest.raises(FileNotFoundError):
        scan_directory("/nonexistent/path/that/does/not/exist")
