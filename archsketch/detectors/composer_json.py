"""Detector for composer.json files (PHP projects)."""

import json
from pathlib import Path

from ..models import TechCategory, TechnologyDetection

TECH_PATTERNS = {
    # Web frameworks
    "laravel/framework": ("Laravel", TechCategory.BACKEND),
    "laravel/lumen": ("Lumen", TechCategory.BACKEND),
    "symfony/symfony": ("Symfony", TechCategory.BACKEND),
    "symfony/framework-bundle": ("Symfony", TechCategory.BACKEND),
    "slim/slim": ("Slim", TechCategory.BACKEND),
    "codeigniter4/codeigniter4": ("CodeIgniter", TechCategory.BACKEND),
    "yiisoft/yii2": ("Yii2", TechCategory.BACKEND),
    "cakephp/cakephp": ("CakePHP", TechCategory.BACKEND),
    "zendframework/zendframework": ("Zend Framework", TechCategory.BACKEND),
    "laminas/laminas-mvc": ("Laminas", TechCategory.BACKEND),
    "api-platform/core": ("API Platform", TechCategory.BACKEND),
    "wordpress/wordpress": ("WordPress", TechCategory.BACKEND),

    # Database / ORM
    "doctrine/orm": ("Doctrine ORM", TechCategory.DATABASE),
    "doctrine/dbal": ("Doctrine DBAL", TechCategory.DATABASE),
    "illuminate/database": ("Eloquent ORM", TechCategory.DATABASE),
    "cycle/orm": ("Cycle ORM", TechCategory.DATABASE),
    "atlas/orm": ("Atlas ORM", TechCategory.DATABASE),

    # Cache
    "predis/predis": ("Redis", TechCategory.CACHE),
    "phpredis": ("Redis", TechCategory.CACHE),

    # Queue / Worker
    "php-amqplib/php-amqplib": ("RabbitMQ", TechCategory.QUEUE),
    "enqueue/enqueue-bundle": ("Enqueue", TechCategory.QUEUE),
    "laravel/horizon": ("Laravel Horizon", TechCategory.WORKER),
}


def detect_from_composer_json(file_path: Path) -> list[TechnologyDetection]:
    """Detect technologies from a composer.json file."""
    detections: list[TechnologyDetection] = []
    source = str(file_path)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return detections

    detections.append(TechnologyDetection(
        source_file=source,
        tech="PHP",
        category=TechCategory.BACKEND,
        confidence=0.95,
        details="composer.json found — PHP project",
    ))

    detected_techs: set[str] = {"PHP"}

    all_deps: set[str] = set()
    for key in ("require", "require-dev"):
        if key in data and isinstance(data[key], dict):
            all_deps.update(data[key].keys())

    for dep in all_deps:
        dep_lower = dep.lower()
        for pattern, (tech_name, category) in TECH_PATTERNS.items():
            if pattern in dep_lower:
                if tech_name not in detected_techs:
                    detected_techs.add(tech_name)
                    detections.append(TechnologyDetection(
                        source_file=source,
                        tech=tech_name,
                        category=category,
                        confidence=0.9,
                        details=f"Found '{dep}' in composer.json",
                    ))

    return detections
