"""Tests for pom.xml (Maven) detector."""

import tempfile
from pathlib import Path

import pytest

from archsketch.detectors.pom_xml import detect_from_pom_xml
from archsketch.models import TechCategory


class TestPomXmlDetector:
    """Tests for pom.xml detector."""
    
    def test_detect_spring_boot(self):
        """Test Spring Boot detection."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write("""
<project>
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
    </dependencies>
</project>
""")
            f.flush()
            
            detections = detect_from_pom_xml(Path(f.name))
            
            assert any(d.tech == "Spring Boot" for d in detections)
            assert any(d.category == TechCategory.BACKEND for d in detections)
    
    def test_detect_postgresql(self):
        """Test PostgreSQL detection from pom.xml."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write("""
<project>
    <dependencies>
        <dependency>
            <groupId>org.postgresql</groupId>
            <artifactId>postgresql</artifactId>
        </dependency>
    </dependencies>
</project>
""")
            f.flush()
            
            detections = detect_from_pom_xml(Path(f.name))
            
            assert any(d.tech == "PostgreSQL" for d in detections)
    
    def test_detect_redis(self):
        """Test Redis detection from pom.xml."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write("""
<project>
    <dependencies>
        <dependency>
            <groupId>redis.clients</groupId>
            <artifactId>jedis</artifactId>
        </dependency>
    </dependencies>
</project>
""")
            f.flush()
            
            detections = detect_from_pom_xml(Path(f.name))
            
            assert any(d.tech == "Redis" for d in detections)
