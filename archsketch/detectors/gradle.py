"""Detector for Gradle build files (build.gradle, build.gradle.kts)."""

import re
from pathlib import Path

from ..models import TechCategory, TechnologyDetection

# Dependency patterns: plugin or implementation("group:name") or implementation("group:name:version")
TECH_PATTERNS = {
    # Spring Boot
    "spring-boot": ("Spring Boot", TechCategory.BACKEND),
    "org.springframework.boot": ("Spring Boot", TechCategory.BACKEND),
    "spring-boot-starter-web": ("Spring Boot", TechCategory.BACKEND),
    "spring-boot-starter-data-jpa": ("Spring Boot", TechCategory.BACKEND),
    "spring-boot-starter-data-redis": ("Spring Boot", TechCategory.BACKEND),
    "spring-boot-starter-data-mongodb": ("Spring Boot", TechCategory.BACKEND),
    
    # Database
    "postgresql": ("PostgreSQL", TechCategory.DATABASE),
    "mysql": ("MySQL", TechCategory.DATABASE),
    "mongodb": ("MongoDB", TechCategory.DATABASE),
    "redis": ("Redis", TechCategory.CACHE),
    "jedis": ("Redis", TechCategory.CACHE),
    
    # Other JVM backends
    "micronaut": ("Micronaut", TechCategory.BACKEND),
    "quarkus": ("Quarkus", TechCategory.BACKEND),
    "ktor": ("Ktor", TechCategory.BACKEND),
}


def detect_from_gradle(file_path: Path) -> list[TechnologyDetection]:
    """
    Detect technologies from build.gradle or build.gradle.kts.
    
    Args:
        file_path: Path to the Gradle build file
        
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
    
    content_lower = content.lower()
    detected_techs: set[str] = set()
    
    # Plugin block: id("org.springframework.boot") or plugins { id 'org.springframework.boot' }
    plugin_pattern = re.compile(
        r'id\s*\(\s*["\']([^"\']+)["\']\s*\)|id\s+["\']([^"\']+)["\']',
        re.IGNORECASE,
    )
    for match in plugin_pattern.finditer(content):
        for g in match.groups():
            if g:
                _check_pattern(g, content, source, detections, detected_techs)
                break
    
    # implementation("group:artifact") or implementation("group:artifact:version")
    impl_pattern = re.compile(
        r'(?:implementation|api|compile)\s*\(\s*["\']([^"\']+)["\']\s*\)',
        re.IGNORECASE,
    )
    for match in impl_pattern.finditer(content):
        dep = match.group(1).lower()
        _check_pattern(dep, content, source, detections, detected_techs)
    
    # Kotlin DSL: implementation("group:artifact")
    # Also match single-quoted
    impl_pattern2 = re.compile(
        r'(?:implementation|api)\s*\(\s*["\']([^"\']+)["\']\s*\)',
        re.IGNORECASE,
    )
    for match in impl_pattern2.finditer(content):
        dep = match.group(1).lower()
        _check_pattern(dep, content, source, detections, detected_techs)
    
    # Spring Boot plugin
    if "spring.boot" in content_lower or "spring-boot" in content_lower:
        if "Spring Boot" not in detected_techs:
            detected_techs.add("Spring Boot")
            detections.append(
                TechnologyDetection(
                    source_file=source,
                    tech="Spring Boot",
                    category=TechCategory.BACKEND,
                    confidence=0.85,
                    details="Spring Boot plugin or dependency in Gradle build",
                )
            )
    
    return detections


def _check_pattern(
    dep: str,
    content: str,
    source: str,
    detections: list[TechnologyDetection],
    detected_techs: set[str],
) -> None:
    dep_lower = dep.lower()
    for pattern, (tech_name, category) in TECH_PATTERNS.items():
        if pattern in dep_lower:
            if tech_name not in detected_techs:
                detected_techs.add(tech_name)
                detections.append(
                    TechnologyDetection(
                        source_file=source,
                        tech=tech_name,
                        category=category,
                        confidence=0.9,
                        details=f"Found '{dep}' in Gradle build",
                    )
                )
            break
