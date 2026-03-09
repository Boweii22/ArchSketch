"""Tests for inference engine."""

import pytest

from archsketch.inference import InferenceEngine
from archsketch.models import (
    ArchitectureRole,
    TechCategory,
    TechnologyDetection,
)


class TestInferenceEngine:
    """Tests for the InferenceEngine."""
    
    def test_empty_detections(self):
        """Test inference with no detections."""
        engine = InferenceEngine()
        architecture = engine.infer([])
        
        assert len(architecture.nodes) == 0
        assert len(architecture.edges) == 0
    
    def test_frontend_inference(self):
        """Test frontend node creation."""
        detections = [
            TechnologyDetection(
                source_file="package.json",
                tech="React",
                category=TechCategory.FRONTEND,
                confidence=0.9,
            )
        ]
        
        engine = InferenceEngine()
        architecture = engine.infer(detections)
        
        assert len(architecture.nodes) == 1
        assert architecture.nodes[0].role == ArchitectureRole.FRONTEND
        assert "React" in architecture.nodes[0].technologies
    
    def test_backend_inference(self):
        """Test backend node creation."""
        detections = [
            TechnologyDetection(
                source_file="requirements.txt",
                tech="FastAPI",
                category=TechCategory.BACKEND,
                confidence=0.9,
            )
        ]
        
        engine = InferenceEngine()
        architecture = engine.infer(detections)
        
        assert len(architecture.nodes) == 1
        assert architecture.nodes[0].role == ArchitectureRole.BACKEND
        assert "FastAPI" in architecture.nodes[0].technologies
    
    def test_database_inference(self):
        """Test database node creation."""
        detections = [
            TechnologyDetection(
                source_file="docker-compose.yml",
                tech="PostgreSQL",
                category=TechCategory.DATABASE,
                confidence=0.95,
            )
        ]
        
        engine = InferenceEngine()
        architecture = engine.infer(detections)
        
        assert len(architecture.nodes) == 1
        assert architecture.nodes[0].role == ArchitectureRole.DATABASE
        assert "PostgreSQL" in architecture.nodes[0].technologies
    
    def test_frontend_backend_edge(self):
        """Test edge creation between frontend and backend."""
        detections = [
            TechnologyDetection(
                source_file="package.json",
                tech="Next.js",
                category=TechCategory.FRONTEND,
                confidence=0.9,
            ),
            TechnologyDetection(
                source_file="requirements.txt",
                tech="FastAPI",
                category=TechCategory.BACKEND,
                confidence=0.9,
            ),
        ]
        
        engine = InferenceEngine()
        architecture = engine.infer(detections)
        
        assert len(architecture.nodes) == 2
        assert len(architecture.edges) == 1
        assert architecture.edges[0].source == "frontend"
        assert architecture.edges[0].target == "backend"
    
    def test_full_stack_inference(self):
        """Test full stack architecture inference."""
        detections = [
            TechnologyDetection(
                source_file="package.json",
                tech="Next.js",
                category=TechCategory.FRONTEND,
                confidence=0.9,
            ),
            TechnologyDetection(
                source_file="requirements.txt",
                tech="FastAPI",
                category=TechCategory.BACKEND,
                confidence=0.9,
            ),
            TechnologyDetection(
                source_file="docker-compose.yml",
                tech="PostgreSQL",
                category=TechCategory.DATABASE,
                confidence=0.95,
            ),
            TechnologyDetection(
                source_file="docker-compose.yml",
                tech="Redis",
                category=TechCategory.CACHE,
                confidence=0.95,
            ),
        ]
        
        engine = InferenceEngine()
        architecture = engine.infer(detections)
        
        # Should have 4 nodes
        assert len(architecture.nodes) == 4
        
        # Check all roles are present
        roles = {node.role for node in architecture.nodes}
        assert ArchitectureRole.FRONTEND in roles
        assert ArchitectureRole.BACKEND in roles
        assert ArchitectureRole.DATABASE in roles
        assert ArchitectureRole.CACHE in roles
        
        # Should have edges: frontend->backend, backend->database, backend->cache
        assert len(architecture.edges) == 3
    
    def test_worker_inference(self):
        """Test worker node and edges."""
        detections = [
            TechnologyDetection(
                source_file="requirements.txt",
                tech="Celery",
                category=TechCategory.WORKER,
                confidence=0.9,
            ),
            TechnologyDetection(
                source_file="docker-compose.yml",
                tech="PostgreSQL",
                category=TechCategory.DATABASE,
                confidence=0.95,
            ),
            TechnologyDetection(
                source_file="docker-compose.yml",
                tech="Redis",
                category=TechCategory.CACHE,
                confidence=0.95,
            ),
        ]
        
        engine = InferenceEngine()
        architecture = engine.infer(detections)
        
        assert architecture.has_role(ArchitectureRole.WORKER)
        
        # Worker should connect to database and cache
        worker_edges = [e for e in architecture.edges if e.source == "worker"]
        assert len(worker_edges) >= 2
    
    def test_reverse_proxy_inference(self):
        """Test reverse proxy node and edges."""
        detections = [
            TechnologyDetection(
                source_file="docker-compose.yml",
                tech="Nginx",
                category=TechCategory.REVERSE_PROXY,
                confidence=0.95,
            ),
            TechnologyDetection(
                source_file="package.json",
                tech="React",
                category=TechCategory.FRONTEND,
                confidence=0.9,
            ),
            TechnologyDetection(
                source_file="requirements.txt",
                tech="Django",
                category=TechCategory.BACKEND,
                confidence=0.9,
            ),
        ]
        
        engine = InferenceEngine()
        architecture = engine.infer(detections)
        
        assert architecture.has_role(ArchitectureRole.REVERSE_PROXY)
        
        # Proxy should route to frontend and backend
        proxy_edges = [e for e in architecture.edges if e.source == "reverse_proxy"]
        assert len(proxy_edges) == 2
    
    def test_deduplicates_technologies(self):
        """Test that duplicate detections are handled."""
        detections = [
            TechnologyDetection(
                source_file="package.json",
                tech="PostgreSQL",
                category=TechCategory.DATABASE,
                confidence=0.9,
            ),
            TechnologyDetection(
                source_file="docker-compose.yml",
                tech="PostgreSQL",
                category=TechCategory.DATABASE,
                confidence=0.95,
            ),
        ]
        
        engine = InferenceEngine()
        architecture = engine.infer(detections)
        
        # Should only have one database node
        db_nodes = [n for n in architecture.nodes if n.role == ArchitectureRole.DATABASE]
        assert len(db_nodes) == 1
