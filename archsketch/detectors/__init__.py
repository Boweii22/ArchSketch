"""Technology detectors for various file types."""

from .package_json import detect_from_package_json
from .requirements_txt import detect_from_requirements
from .docker_compose import detect_from_docker_compose
from .dockerfile import detect_from_dockerfile
from .env_files import detect_from_env_files

__all__ = [
    "detect_from_package_json",
    "detect_from_requirements",
    "detect_from_docker_compose",
    "detect_from_dockerfile",
    "detect_from_env_files",
]
