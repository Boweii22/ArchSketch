"""Detector for Package.swift files (Swift projects)."""

import re
from pathlib import Path

from ..models import TechCategory, TechnologyDetection

# Match against GitHub URL fragments and package names
TECH_PATTERNS = {
    # Web frameworks
    "vapor/vapor": ("Vapor", TechCategory.BACKEND),
    "hummingbird": ("Hummingbird", TechCategory.BACKEND),
    "swift-nio": ("SwiftNIO", TechCategory.BACKEND),
    "perfect-": ("Perfect", TechCategory.BACKEND),
    "kitura": ("Kitura", TechCategory.BACKEND),

    # Database / ORM
    "vapor/fluent": ("Fluent ORM", TechCategory.DATABASE),
    "fluent-postgres-driver": ("PostgreSQL", TechCategory.DATABASE),
    "fluent-mysql-driver": ("MySQL", TechCategory.DATABASE),
    "fluent-sqlite-driver": ("SQLite", TechCategory.DATABASE),
    "fluent-mongo-driver": ("MongoDB", TechCategory.DATABASE),
    "mongo-swift-driver": ("MongoDB", TechCategory.DATABASE),
    "swift-postgres": ("PostgreSQL", TechCategory.DATABASE),

    # Cache
    "redistack": ("Redis", TechCategory.CACHE),
    "redistack": ("Redis", TechCategory.CACHE),
    "vapor/redis": ("Redis", TechCategory.CACHE),

    # Queue
    "vapor/queues": ("Vapor Queues", TechCategory.QUEUE),
}


def detect_from_package_swift(file_path: Path) -> list[TechnologyDetection]:
    """Detect technologies from a Package.swift file."""
    detections: list[TechnologyDetection] = []
    source = str(file_path)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return detections

    detections.append(TechnologyDetection(
        source_file=source,
        tech="Swift",
        category=TechCategory.BACKEND,
        confidence=0.95,
        details="Package.swift found — Swift project",
    ))

    detected_techs: set[str] = {"Swift"}

    # Look for .package(url: "...", ...) entries
    for match in re.finditer(r'\.package\s*\(.*?url\s*:\s*"([^"]+)"', content, re.DOTALL):
        url = match.group(1).lower()
        for pattern, (tech_name, category) in TECH_PATTERNS.items():
            if pattern in url:
                if tech_name not in detected_techs:
                    detected_techs.add(tech_name)
                    detections.append(TechnologyDetection(
                        source_file=source,
                        tech=tech_name,
                        category=category,
                        confidence=0.9,
                        details=f"Found '{pattern}' in Package.swift",
                    ))

    return detections
