"""Tests for the fallback extension scanner."""

import tempfile
from pathlib import Path

import pytest

from archsketch.detectors.extension_scanner import detect_from_extensions
from archsketch.models import TechCategory


def _make_files(tmp: str, *names: str) -> None:
    for name in names:
        p = Path(tmp) / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("// placeholder\n", encoding="utf-8")


class TestExtensionScanner:

    def test_empty_directory_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            assert detect_from_extensions(Path(tmp)) == []

    def test_single_rust_file_below_threshold(self):
        """One file is below MIN_FILES=2, so nothing returned."""
        with tempfile.TemporaryDirectory() as tmp:
            _make_files(tmp, "main.rs")
            assert detect_from_extensions(Path(tmp)) == []

    def test_two_rust_files_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            _make_files(tmp, "main.rs", "lib.rs")
            d = detect_from_extensions(Path(tmp))
            techs = {x.tech for x in d}
            assert "Rust" in techs

    def test_rust_category_is_backend(self):
        with tempfile.TemporaryDirectory() as tmp:
            _make_files(tmp, "main.rs", "lib.rs", "server.rs")
            d = detect_from_extensions(Path(tmp))
            rust = next(x for x in d if x.tech == "Rust")
            assert rust.category == TechCategory.BACKEND

    def test_go_files_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            _make_files(tmp, "main.go", "handler.go", "models.go")
            d = detect_from_extensions(Path(tmp))
            assert any(x.tech == "Go" for x in d)

    def test_csharp_files_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            _make_files(tmp, "Program.cs", "Startup.cs")
            d = detect_from_extensions(Path(tmp))
            assert any(x.tech == "C#" for x in d)

    def test_ruby_files_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            _make_files(tmp, "app.rb", "config.rb", "routes.rb")
            d = detect_from_extensions(Path(tmp))
            assert any(x.tech == "Ruby" for x in d)

    def test_php_files_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            _make_files(tmp, "index.php", "router.php")
            d = detect_from_extensions(Path(tmp))
            assert any(x.tech == "PHP" for x in d)

    def test_dart_category_is_frontend(self):
        with tempfile.TemporaryDirectory() as tmp:
            _make_files(tmp, "main.dart", "app.dart", "widgets.dart")
            d = detect_from_extensions(Path(tmp))
            dart = next(x for x in d if x.tech == "Dart")
            assert dart.category == TechCategory.FRONTEND

    def test_elixir_files_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            _make_files(tmp, "app.ex", "router.ex", "controller.exs")
            d = detect_from_extensions(Path(tmp))
            assert any(x.tech == "Elixir" for x in d)

    def test_swift_files_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            _make_files(tmp, "main.swift", "app.swift")
            d = detect_from_extensions(Path(tmp))
            assert any(x.tech == "Swift" for x in d)

    def test_c_files_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            _make_files(tmp, "main.c", "utils.c")
            d = detect_from_extensions(Path(tmp))
            assert any(x.tech in ("C", "C/C++") for x in d)

    def test_cpp_files_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            _make_files(tmp, "main.cpp", "server.cpp", "handler.cpp")
            d = detect_from_extensions(Path(tmp))
            assert any(x.tech == "C++" for x in d)

    def test_haskell_files_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            _make_files(tmp, "Main.hs", "Server.hs")
            d = detect_from_extensions(Path(tmp))
            assert any(x.tech == "Haskell" for x in d)

    def test_kotlin_files_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            _make_files(tmp, "App.kt", "Service.kt")
            d = detect_from_extensions(Path(tmp))
            assert any(x.tech == "Kotlin" for x in d)

    def test_java_files_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            _make_files(tmp, "Main.java", "App.java", "Service.java")
            d = detect_from_extensions(Path(tmp))
            assert any(x.tech == "Java" for x in d)

    def test_skips_node_modules(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Put RS files only inside node_modules — should be ignored
            _make_files(tmp, "node_modules/dep/index.rs", "node_modules/other/lib.rs")
            d = detect_from_extensions(Path(tmp))
            assert d == []

    def test_skips_dotgit(self):
        with tempfile.TemporaryDirectory() as tmp:
            _make_files(tmp, ".git/hooks/pre-commit.rs", ".git/info/exclude.rs")
            assert detect_from_extensions(Path(tmp)) == []

    def test_skips_venv(self):
        with tempfile.TemporaryDirectory() as tmp:
            _make_files(tmp, "venv/bin/activate.py", "venv/lib/site.py")
            assert detect_from_extensions(Path(tmp)) == []

    def test_confidence_range(self):
        with tempfile.TemporaryDirectory() as tmp:
            for i in range(10):
                _make_files(tmp, f"file_{i}.rs")
            d = detect_from_extensions(Path(tmp))
            for det in d:
                assert 0.0 < det.confidence <= 1.0

    def test_most_common_language_comes_first(self):
        """Language with the most files should appear first."""
        with tempfile.TemporaryDirectory() as tmp:
            for i in range(10):
                _make_files(tmp, f"file_{i}.rs")
            _make_files(tmp, "one.go", "two.go")
            d = detect_from_extensions(Path(tmp))
            assert d[0].tech == "Rust"

    def test_mixed_project_detects_all_languages(self):
        with tempfile.TemporaryDirectory() as tmp:
            _make_files(tmp, "server.go", "handler.go", "ui.tsx", "app.tsx")
            d = detect_from_extensions(Path(tmp))
            techs = {x.tech for x in d}
            assert "Go" in techs
            # tsx → TypeScript/React (frontend)
            assert any("TypeScript" in t for t in techs)

    def test_source_file_points_to_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            _make_files(tmp, "a.rs", "b.rs")
            d = detect_from_extensions(Path(tmp))
            assert any(tmp in x.source_file for x in d)

    def test_details_mentions_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            _make_files(tmp, "a.rs", "b.rs", "c.rs")
            d = detect_from_extensions(Path(tmp))
            rust = next(x for x in d if x.tech == "Rust")
            assert "3" in rust.details
