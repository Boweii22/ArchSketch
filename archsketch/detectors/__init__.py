"""Technology detectors for various file types."""

from .package_json import detect_from_package_json
from .requirements_txt import detect_from_requirements
from .docker_compose import detect_from_docker_compose
from .dockerfile import detect_from_dockerfile
from .env_files import detect_from_env_files
from .nginx_conf import detect_from_nginx_conf
from .pom_xml import detect_from_pom_xml
from .gradle import detect_from_gradle
from .procfile import detect_from_procfile
from .kubernetes import detect_from_kubernetes
from .terraform import detect_from_terraform

__all__ = [
    "detect_from_package_json",
    "detect_from_requirements",
    "detect_from_docker_compose",
    "detect_from_dockerfile",
    "detect_from_env_files",
    "detect_from_nginx_conf",
    "detect_from_pom_xml",
    "detect_from_gradle",
    "detect_from_procfile",
    "detect_from_kubernetes",
    "detect_from_terraform",
]
