"""Tests for nginx.conf detector."""

import tempfile
from pathlib import Path

import pytest

from archsketch.detectors.nginx_conf import detect_from_nginx_conf
from archsketch.models import TechCategory


class TestNginxConfDetector:
    """Tests for nginx.conf detector."""
    
    def test_detect_nginx_basic(self):
        """Test basic Nginx detection."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
            f.write("""
server {
    listen 80;
    server_name localhost;
}
""")
            f.flush()
            
            detections = detect_from_nginx_conf(Path(f.name))
            
            assert any(d.tech == "Nginx" for d in detections)
            assert any(d.category == TechCategory.REVERSE_PROXY for d in detections)
    
    def test_detect_upstream_backend(self):
        """Test upstream block detection."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
            f.write("""
upstream api {
    server backend:8000;
}

server {
    location /api {
        proxy_pass http://api;
    }
}
""")
            f.flush()
            
            detections = detect_from_nginx_conf(Path(f.name))
            
            assert any("api" in d.tech.lower() and d.category == TechCategory.BACKEND 
                      for d in detections)
    
    def test_detect_proxy_pass_backend(self):
        """Test proxy_pass detection for backend ports."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
            f.write("""
server {
    location / {
        proxy_pass http://localhost:8000;
    }
}
""")
            f.flush()
            
            detections = detect_from_nginx_conf(Path(f.name))
            
            assert any(d.category == TechCategory.BACKEND for d in detections)
    
    def test_detect_static_frontend(self):
        """Test static file serving detection."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
            f.write("""
server {
    location / {
        root /var/www/html/dist;
        index index.html;
    }
}
""")
            f.flush()
            
            detections = detect_from_nginx_conf(Path(f.name))
            
            assert any(d.category == TechCategory.FRONTEND for d in detections)
    
    def test_detect_ssl(self):
        """Test SSL/TLS detection."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
            f.write("""
server {
    listen 443 ssl;
    ssl_certificate /etc/ssl/cert.pem;
    ssl_certificate_key /etc/ssl/key.pem;
}
""")
            f.flush()
            
            detections = detect_from_nginx_conf(Path(f.name))
            
            assert any(d.tech == "SSL/TLS" for d in detections)
    
    def test_detect_load_balancing(self):
        """Test load balancing detection."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
            f.write("""
upstream backend {
    least_conn;
    server backend1:8000 weight=3;
    server backend2:8000 weight=2;
}
""")
            f.flush()
            
            detections = detect_from_nginx_conf(Path(f.name))
            
            assert any(d.tech == "Load Balancer" for d in detections)
    
    def test_detect_websocket(self):
        """Test WebSocket support detection."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
            f.write("""
# WebSocket proxy configuration
server {
    location /ws {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
""")
            f.flush()
            
            detections = detect_from_nginx_conf(Path(f.name))
            
            assert any(d.tech == "WebSocket" for d in detections)
