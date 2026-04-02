"""Detector for CMakeLists.txt and Makefile files (C/C++ projects)."""

import re
from pathlib import Path

from ..models import TechCategory, TechnologyDetection

# Patterns to look for in CMakeLists.txt / Makefile
CMAKE_PATTERNS = {
    # GUI / Frontend
    "qt": ("Qt", TechCategory.FRONTEND),
    "wxwidgets": ("wxWidgets", TechCategory.FRONTEND),
    "gtkmm": ("GTK", TechCategory.FRONTEND),
    "sfml": ("SFML", TechCategory.FRONTEND),
    "sdl": ("SDL", TechCategory.FRONTEND),
    "imgui": ("ImGui", TechCategory.FRONTEND),

    # Web / networking (server-side)
    "crow": ("Crow", TechCategory.BACKEND),
    "cpprestsdk": ("C++ REST SDK", TechCategory.BACKEND),
    "pistache": ("Pistache", TechCategory.BACKEND),
    "drogon": ("Drogon", TechCategory.BACKEND),
    "beast": ("Boost.Beast", TechCategory.BACKEND),
    "poco": ("POCO", TechCategory.BACKEND),

    # Database
    "libpq": ("PostgreSQL", TechCategory.DATABASE),
    "pqxx": ("PostgreSQL", TechCategory.DATABASE),
    "sqlite": ("SQLite", TechCategory.DATABASE),
    "sqlite3": ("SQLite", TechCategory.DATABASE),
    "mysql": ("MySQL", TechCategory.DATABASE),
    "mongocxx": ("MongoDB", TechCategory.DATABASE),
    "mongo-cxx": ("MongoDB", TechCategory.DATABASE),
    "leveldb": ("LevelDB", TechCategory.DATABASE),
    "rocksdb": ("RocksDB", TechCategory.DATABASE),

    # Cache
    "hiredis": ("Redis", TechCategory.CACHE),
    "redis": ("Redis", TechCategory.CACHE),

    # Queue
    "rabbitmq": ("RabbitMQ", TechCategory.QUEUE),
    "rdkafka": ("Kafka", TechCategory.QUEUE),
    "nats": ("NATS", TechCategory.QUEUE),
}


def _detect_language(content: str, file_path: Path) -> str:
    """Heuristically determine if this is C or C++."""
    name = file_path.name.lower()
    content_lower = content.lower()
    if "cxx" in content_lower or "c++" in content_lower or "cpp" in content_lower or "std::" in content_lower:
        return "C++"
    if name == "cmakelists.txt":
        return "C++"
    return "C"


def detect_from_cmake(file_path: Path) -> list[TechnologyDetection]:
    """Detect technologies from a CMakeLists.txt or Makefile."""
    detections: list[TechnologyDetection] = []
    source = str(file_path)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return detections

    lang = _detect_language(content, file_path)
    detections.append(TechnologyDetection(
        source_file=source,
        tech=lang,
        category=TechCategory.BACKEND,
        confidence=0.85,
        details=f"{file_path.name} found — {lang} project",
    ))

    detected_techs: set[str] = {lang}
    content_lower = content.lower()

    for pattern, (tech_name, category) in CMAKE_PATTERNS.items():
        if pattern in content_lower:
            if tech_name not in detected_techs:
                detected_techs.add(tech_name)
                detections.append(TechnologyDetection(
                    source_file=source,
                    tech=tech_name,
                    category=category,
                    confidence=0.75,
                    details=f"Found '{pattern}' in {file_path.name}",
                ))

    return detections
