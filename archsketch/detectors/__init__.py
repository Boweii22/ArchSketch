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
from .cargo_toml import detect_from_cargo_toml
from .go_mod import detect_from_go_mod
from .csproj import detect_from_csproj
from .gemfile import detect_from_gemfile
from .composer_json import detect_from_composer_json
from .pubspec_yaml import detect_from_pubspec_yaml
from .mix_exs import detect_from_mix_exs
from .package_swift import detect_from_package_swift
from .cmake import detect_from_cmake
from .extension_scanner import detect_from_extensions

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
    "detect_from_cargo_toml",
    "detect_from_go_mod",
    "detect_from_csproj",
    "detect_from_gemfile",
    "detect_from_composer_json",
    "detect_from_pubspec_yaml",
    "detect_from_mix_exs",
    "detect_from_package_swift",
    "detect_from_cmake",
    "detect_from_extensions",
]
