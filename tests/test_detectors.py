"""Tests for detector modules."""

import json
import tempfile
from pathlib import Path

import pytest

from archsketch.detectors import (
    detect_from_docker_compose,
    detect_from_dockerfile,
    detect_from_env_files,
    detect_from_package_json,
    detect_from_requirements,
)
from archsketch.models import TechCategory


class TestPackageJsonDetector:
    """Tests for package.json detector."""
    
    def test_detect_react(self):
        """Test React detection."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({
                "dependencies": {
                    "react": "^18.0.0",
                    "react-dom": "^18.0.0"
                }
            }, f)
            f.flush()
            
            detections = detect_from_package_json(Path(f.name))
            
            assert any(d.tech == "React" for d in detections)
            assert any(d.category == TechCategory.FRONTEND for d in detections)
    
    def test_detect_nextjs(self):
        """Test Next.js detection."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({
                "dependencies": {
                    "next": "^14.0.0",
                    "react": "^18.0.0"
                }
            }, f)
            f.flush()
            
            detections = detect_from_package_json(Path(f.name))
            
            assert any(d.tech == "Next.js" for d in detections)
    
    def test_detect_express(self):
        """Test Express detection."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({
                "dependencies": {
                    "express": "^4.18.0"
                }
            }, f)
            f.flush()
            
            detections = detect_from_package_json(Path(f.name))
            
            assert any(d.tech == "Express" for d in detections)
            assert any(d.category == TechCategory.BACKEND for d in detections)
    
    def test_detect_redis(self):
        """Test Redis detection from ioredis."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({
                "dependencies": {
                    "ioredis": "^5.0.0"
                }
            }, f)
            f.flush()
            
            detections = detect_from_package_json(Path(f.name))
            
            assert any(d.tech == "Redis" for d in detections)
            assert any(d.category == TechCategory.CACHE for d in detections)
    
    def test_detect_postgres(self):
        """Test PostgreSQL detection from pg."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({
                "dependencies": {
                    "pg": "^8.0.0"
                }
            }, f)
            f.flush()
            
            detections = detect_from_package_json(Path(f.name))
            
            assert any(d.tech == "PostgreSQL" for d in detections)
            assert any(d.category == TechCategory.DATABASE for d in detections)


class TestRequirementsDetector:
    """Tests for requirements.txt detector."""
    
    def test_detect_fastapi(self):
        """Test FastAPI detection."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("fastapi>=0.100.0\nuvicorn[standard]\n")
            f.flush()
            
            detections = detect_from_requirements(Path(f.name))
            
            assert any(d.tech == "FastAPI" for d in detections)
            assert any(d.category == TechCategory.BACKEND for d in detections)
    
    def test_detect_django(self):
        """Test Django detection."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("django>=4.0\ndjango-rest-framework\n")
            f.flush()
            
            detections = detect_from_requirements(Path(f.name))
            
            assert any(d.tech == "Django" for d in detections)
    
    def test_detect_celery(self):
        """Test Celery detection."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("celery>=5.0\nredis\n")
            f.flush()
            
            detections = detect_from_requirements(Path(f.name))
            
            assert any(d.tech == "Celery" for d in detections)
            assert any(d.category == TechCategory.WORKER for d in detections)
    
    def test_detect_psycopg2(self):
        """Test PostgreSQL detection from psycopg2."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("psycopg2-binary>=2.9\n")
            f.flush()
            
            detections = detect_from_requirements(Path(f.name))
            
            assert any(d.tech == "PostgreSQL" for d in detections)


class TestDockerComposeDetector:
    """Tests for docker-compose detector."""
    
    def test_detect_postgres_service(self):
        """Test PostgreSQL detection from docker-compose."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("""
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: app
""")
            f.flush()
            
            detections = detect_from_docker_compose(Path(f.name))
            
            assert any(d.tech == "PostgreSQL" for d in detections)
    
    def test_detect_redis_service(self):
        """Test Redis detection from docker-compose."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("""
version: '3.8'
services:
  cache:
    image: redis:7-alpine
""")
            f.flush()
            
            detections = detect_from_docker_compose(Path(f.name))
            
            assert any(d.tech == "Redis" for d in detections)
    
    def test_detect_nginx_service(self):
        """Test Nginx detection from docker-compose."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("""
version: '3.8'
services:
  proxy:
    image: nginx:latest
""")
            f.flush()
            
            detections = detect_from_docker_compose(Path(f.name))
            
            assert any(d.tech == "Nginx" for d in detections)


class TestDockerfileDetector:
    """Tests for Dockerfile detector."""
    
    def test_detect_python_base(self):
        """Test Python detection from base image."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("FROM python:3.11-slim\nWORKDIR /app\n")
            f.flush()
            
            detections = detect_from_dockerfile(Path(f.name))
            
            assert any(d.tech == "Python" for d in detections)
    
    def test_detect_node_base(self):
        """Test Node.js detection from base image."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("FROM node:20-alpine\nWORKDIR /app\n")
            f.flush()
            
            detections = detect_from_dockerfile(Path(f.name))
            
            assert any(d.tech == "Node.js" for d in detections)
    
    def test_docker_detected(self):
        """Test that Docker itself is detected."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("FROM ubuntu:22.04\n")
            f.flush()
            
            detections = detect_from_dockerfile(Path(f.name))
            
            assert any(d.tech == "Docker" for d in detections)


class TestEnvFilesDetector:
    """Tests for .env files detector."""
    
    def test_detect_postgres_url(self):
        """Test PostgreSQL detection from DATABASE_URL."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("DATABASE_URL=postgresql://user:pass@localhost/db\n")
            f.flush()
            
            detections = detect_from_env_files(Path(f.name))
            
            assert any(d.tech == "PostgreSQL" for d in detections)
    
    def test_detect_redis_url(self):
        """Test Redis detection from REDIS_URL."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("REDIS_URL=redis://localhost:6379\n")
            f.flush()
            
            detections = detect_from_env_files(Path(f.name))
            
            assert any(d.tech == "Redis" for d in detections)
