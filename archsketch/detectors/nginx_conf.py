"""Detector for nginx.conf files."""

import re
from pathlib import Path

from ..models import TechCategory, TechnologyDetection


def detect_from_nginx_conf(file_path: Path) -> list[TechnologyDetection]:
    """
    Detect architecture information from nginx.conf files.
    
    Nginx configs reveal:
    - Upstream servers (backends)
    - Proxy pass targets
    - Static file serving (frontend)
    - Load balancing
    - SSL/TLS configuration
    
    Args:
        file_path: Path to the nginx.conf file
        
    Returns:
        List of detected technologies
    """
    detections: list[TechnologyDetection] = []
    source = str(file_path)
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return detections
    
    # Always detect Nginx itself
    detections.append(
        TechnologyDetection(
            source_file=source,
            tech="Nginx",
            category=TechCategory.REVERSE_PROXY,
            confidence=1.0,
            details="nginx.conf file present",
        )
    )
    
    content_lower = content.lower()
    
    # Detect upstream blocks (backend servers)
    upstream_pattern = re.compile(r"upstream\s+(\w+)\s*\{([^}]+)\}", re.IGNORECASE)
    for match in upstream_pattern.finditer(content):
        upstream_name = match.group(1)
        upstream_content = match.group(2)
        
        # Check for common backend patterns
        if any(kw in upstream_name.lower() for kw in ["api", "backend", "app", "server"]):
            detections.append(
                TechnologyDetection(
                    source_file=source,
                    tech=f"{upstream_name} (upstream)",
                    category=TechCategory.BACKEND,
                    confidence=0.7,
                    details=f"Nginx upstream block '{upstream_name}' suggests backend service",
                )
            )
    
    # Detect proxy_pass directives
    proxy_pass_pattern = re.compile(r"proxy_pass\s+(\S+);", re.IGNORECASE)
    for match in proxy_pass_pattern.finditer(content):
        target = match.group(1)
        
        # Check for common service patterns
        if "redis" in target.lower():
            detections.append(
                TechnologyDetection(
                    source_file=source,
                    tech="Redis",
                    category=TechCategory.CACHE,
                    confidence=0.6,
                    details=f"proxy_pass to Redis: {target}",
                )
            )
        elif "postgres" in target.lower() or ":5432" in target:
            detections.append(
                TechnologyDetection(
                    source_file=source,
                    tech="PostgreSQL",
                    category=TechCategory.DATABASE,
                    confidence=0.6,
                    details=f"proxy_pass suggests PostgreSQL: {target}",
                )
            )
        elif any(port in target for port in [":3000", ":8080", ":8000", ":4000", ":5000"]):
            detections.append(
                TechnologyDetection(
                    source_file=source,
                    tech="Backend Service",
                    category=TechCategory.BACKEND,
                    confidence=0.5,
                    details=f"proxy_pass to backend: {target}",
                )
            )
    
    # Detect static file serving (likely frontend)
    if re.search(r"root\s+[^;]*(?:dist|build|public|static|html)", content_lower):
        detections.append(
            TechnologyDetection(
                source_file=source,
                tech="Static Frontend",
                category=TechCategory.FRONTEND,
                confidence=0.6,
                details="Nginx serves static files (dist/build/public)",
            )
        )
    
    # Detect SSL/TLS
    if "ssl_certificate" in content_lower:
        detections.append(
            TechnologyDetection(
                source_file=source,
                tech="SSL/TLS",
                category=TechCategory.REVERSE_PROXY,
                confidence=0.9,
                details="SSL certificate configuration found",
            )
        )
    
    # Detect load balancing
    if any(lb in content_lower for lb in ["least_conn", "ip_hash", "weight="]):
        detections.append(
            TechnologyDetection(
                source_file=source,
                tech="Load Balancer",
                category=TechCategory.REVERSE_PROXY,
                confidence=0.85,
                details="Load balancing configuration detected",
            )
        )
    
    # Detect WebSocket support
    if "upgrade" in content_lower and "websocket" in content_lower:
        detections.append(
            TechnologyDetection(
                source_file=source,
                tech="WebSocket",
                category=TechCategory.BACKEND,
                confidence=0.8,
                details="WebSocket proxy configuration found",
            )
        )
    
    return detections
