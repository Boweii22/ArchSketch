"""Detector for pubspec.yaml files (Dart / Flutter projects)."""

from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from ..models import TechCategory, TechnologyDetection

TECH_PATTERNS = {
    # Flutter UI
    "flutter": ("Flutter", TechCategory.FRONTEND),
    "get": ("GetX", TechCategory.FRONTEND),
    "provider": ("Provider", TechCategory.FRONTEND),
    "riverpod": ("Riverpod", TechCategory.FRONTEND),
    "flutter_riverpod": ("Riverpod", TechCategory.FRONTEND),
    "bloc": ("BLoC", TechCategory.FRONTEND),
    "flutter_bloc": ("BLoC", TechCategory.FRONTEND),
    "mobx": ("MobX", TechCategory.FRONTEND),

    # Server-side Dart
    "shelf": ("Shelf", TechCategory.BACKEND),
    "dart_frog": ("Dart Frog", TechCategory.BACKEND),
    "conduit": ("Conduit", TechCategory.BACKEND),
    "serverpod": ("Serverpod", TechCategory.BACKEND),

    # Database
    "sqflite": ("SQLite", TechCategory.DATABASE),
    "drift": ("Drift", TechCategory.DATABASE),
    "isar": ("Isar", TechCategory.DATABASE),
    "hive": ("Hive", TechCategory.DATABASE),
    "firebase_core": ("Firebase", TechCategory.DATABASE),
    "cloud_firestore": ("Firestore", TechCategory.DATABASE),
    "firebase_database": ("Firebase Realtime DB", TechCategory.DATABASE),
    "supabase_flutter": ("Supabase", TechCategory.DATABASE),
    "mongo_dart": ("MongoDB", TechCategory.DATABASE),

    # Cache / Network
    "redis": ("Redis", TechCategory.CACHE),
}


def detect_from_pubspec_yaml(file_path: Path) -> list[TechnologyDetection]:
    """Detect technologies from a pubspec.yaml file."""
    detections: list[TechnologyDetection] = []
    source = str(file_path)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return detections

    detections.append(TechnologyDetection(
        source_file=source,
        tech="Dart",
        category=TechCategory.BACKEND,
        confidence=0.95,
        details="pubspec.yaml found — Dart project",
    ))

    detected_techs: set[str] = {"Dart"}

    # Parse YAML if available, otherwise fallback to line scanning
    packages: set[str] = set()

    if HAS_YAML:
        try:
            data = yaml.safe_load(content)
            if isinstance(data, dict):
                for key in ("dependencies", "dev_dependencies"):
                    deps = data.get(key, {})
                    if isinstance(deps, dict):
                        packages.update(deps.keys())
        except yaml.YAMLError:
            pass

    if not packages:
        # Fallback: grab anything that looks like a package name at the start of a line
        import re
        for match in re.finditer(r'^\s{2,4}([a-zA-Z0-9_]+)\s*:', content, re.MULTILINE):
            packages.add(match.group(1))

    for pkg in packages:
        pkg_lower = pkg.lower()
        for pattern, (tech_name, category) in TECH_PATTERNS.items():
            if pkg_lower == pattern or pkg_lower.startswith(pattern):
                if tech_name not in detected_techs:
                    detected_techs.add(tech_name)
                    detections.append(TechnologyDetection(
                        source_file=source,
                        tech=tech_name,
                        category=category,
                        confidence=0.9,
                        details=f"Found '{pkg}' in pubspec.yaml",
                    ))

    return detections
