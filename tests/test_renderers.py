"""Tests for renderers."""

import tempfile
from pathlib import Path

import pytest

from archsketch.models import (
    Architecture,
    ArchitectureEdge,
    ArchitectureNode,
    ArchitectureRole,
)
from archsketch.renderers import render_mermaid
from archsketch.renderers.mermaid_renderer import export_mermaid


class TestMermaidRenderer:
    """Tests for Mermaid renderer."""
    
    def test_empty_architecture(self):
        """Test rendering empty architecture."""
        architecture = Architecture()
        result = render_mermaid(architecture)
        
        assert "No architecture detected" in result
    
    def test_single_node(self):
        """Test rendering a single node."""
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
        
        result = render_mermaid(architecture)
        
        assert "graph TD" in result
        assert "Backend: FastAPI" in result
    
    def test_two_nodes_with_edge(self):
        """Test rendering two nodes with an edge."""
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
                ArchitectureEdge(
                    source="frontend",
                    target="backend",
                    relation="calls",
                )
            ],
        )
        
        result = render_mermaid(architecture)
        
        assert "graph TD" in result
        assert "frontend --> backend" in result
    
    def test_full_stack_mermaid(self):
        """Test rendering full stack architecture."""
        architecture = Architecture(
            nodes=[
                ArchitectureNode(
                    id="frontend",
                    label="Frontend: Next.js",
                    role=ArchitectureRole.FRONTEND,
                    technologies=["Next.js"],
                ),
                ArchitectureNode(
                    id="backend",
                    label="Backend: FastAPI",
                    role=ArchitectureRole.BACKEND,
                    technologies=["FastAPI"],
                ),
                ArchitectureNode(
                    id="database",
                    label="Database: PostgreSQL",
                    role=ArchitectureRole.DATABASE,
                    technologies=["PostgreSQL"],
                ),
                ArchitectureNode(
                    id="cache",
                    label="Cache: Redis",
                    role=ArchitectureRole.CACHE,
                    technologies=["Redis"],
                ),
            ],
            edges=[
                ArchitectureEdge(source="frontend", target="backend", relation="calls"),
                ArchitectureEdge(source="backend", target="database", relation="queries"),
                ArchitectureEdge(source="backend", target="cache", relation="caches"),
            ],
        )
        
        result = render_mermaid(architecture)
        
        assert "graph TD" in result
        assert "Frontend: Next.js" in result
        assert "Backend: FastAPI" in result
        assert "Database: PostgreSQL" in result
        assert "Cache: Redis" in result
        assert "frontend --> backend" in result
        assert "backend --> database" in result
        assert "backend --> cache" in result


class TestMermaidExport:
    """Tests for Mermaid export functionality."""
    
    def test_export_creates_file(self):
        """Test that export creates a file."""
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
            output_path = Path(tmpdir) / "test.mmd"
            result = export_mermaid(architecture, output_path)
            
            assert result.exists()
            content = result.read_text()
            assert "graph TD" in content
            assert "Backend: FastAPI" in content
    
    def test_export_adds_extension(self):
        """Test that export adds .mmd extension if missing."""
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
            output_path = Path(tmpdir) / "architecture"
            result = export_mermaid(architecture, output_path)
            
            assert result.suffix == ".mmd"
