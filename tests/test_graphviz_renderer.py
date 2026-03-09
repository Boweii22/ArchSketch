"""Tests for Graphviz/DOT renderer."""

import tempfile
from pathlib import Path

import pytest

from archsketch.models import (
    Architecture,
    ArchitectureEdge,
    ArchitectureNode,
    ArchitectureRole,
)
from archsketch.renderers.graphviz_renderer import export_dot, render_dot


class TestGraphvizRenderer:
    """Tests for Graphviz DOT output (no binary required)."""
    
    def test_render_dot_empty(self):
        """Test DOT output for empty architecture."""
        architecture = Architecture()
        result = render_dot(architecture)
        assert "digraph" in result
        assert "No architecture detected" in result
    
    def test_render_dot_single_node(self):
        """Test DOT output for single node."""
        architecture = Architecture(
            nodes=[
                ArchitectureNode(
                    id="backend",
                    label="Backend: FastAPI",
                    role=ArchitectureRole.BACKEND,
                    technologies=["FastAPI"],
                )
            ]
        )
        result = render_dot(architecture)
        assert "digraph Architecture" in result
        assert "backend" in result
        assert "Backend: FastAPI" in result
    
    def test_render_dot_with_edges(self):
        """Test DOT output with edges."""
        architecture = Architecture(
            nodes=[
                ArchitectureNode(
                    id="frontend",
                    label="Frontend: React",
                    role=ArchitectureRole.FRONTEND,
                    technologies=["React"],
                ),
                ArchitectureNode(
                    id="backend",
                    label="Backend: Express",
                    role=ArchitectureRole.BACKEND,
                    technologies=["Express"],
                ),
            ],
            edges=[
                ArchitectureEdge(source="frontend", target="backend", relation="calls"),
            ],
        )
        result = render_dot(architecture)
        assert "frontend -> backend" in result
    
    def test_export_dot_creates_file(self):
        """Test that export_dot creates a .dot file."""
        architecture = Architecture(
            nodes=[
                ArchitectureNode(
                    id="backend",
                    label="Backend: FastAPI",
                    role=ArchitectureRole.BACKEND,
                    technologies=["FastAPI"],
                )
            ]
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "arch"
            result = export_dot(architecture, output_path)
            assert result.suffix == ".dot"
            assert result.exists()
            content = result.read_text()
            assert "digraph" in content
