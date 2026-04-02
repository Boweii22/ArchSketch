"""Fallback detector: infer language from source file extensions when no config is found."""

import os
from pathlib import Path

from ..models import TechCategory, TechnologyDetection

# Map extension -> (language, category)
EXTENSION_MAP: dict[str, tuple[str, TechCategory]] = {
    ".rs": ("Rust", TechCategory.BACKEND),
    ".go": ("Go", TechCategory.BACKEND),
    ".cs": ("C#", TechCategory.BACKEND),
    ".fs": ("F#", TechCategory.BACKEND),
    ".vb": ("VB.NET", TechCategory.BACKEND),
    ".rb": ("Ruby", TechCategory.BACKEND),
    ".php": ("PHP", TechCategory.BACKEND),
    ".dart": ("Dart", TechCategory.FRONTEND),
    ".ex": ("Elixir", TechCategory.BACKEND),
    ".exs": ("Elixir", TechCategory.BACKEND),
    ".swift": ("Swift", TechCategory.BACKEND),
    ".c": ("C", TechCategory.BACKEND),
    ".cpp": ("C++", TechCategory.BACKEND),
    ".cc": ("C++", TechCategory.BACKEND),
    ".cxx": ("C++", TechCategory.BACKEND),
    ".h": ("C/C++", TechCategory.BACKEND),
    ".hpp": ("C++", TechCategory.BACKEND),
    ".java": ("Java", TechCategory.BACKEND),
    ".kt": ("Kotlin", TechCategory.BACKEND),
    ".kts": ("Kotlin", TechCategory.BACKEND),
    ".scala": ("Scala", TechCategory.BACKEND),
    ".clj": ("Clojure", TechCategory.BACKEND),
    ".cljs": ("ClojureScript", TechCategory.FRONTEND),
    ".hs": ("Haskell", TechCategory.BACKEND),
    ".lhs": ("Haskell", TechCategory.BACKEND),
    ".erl": ("Erlang", TechCategory.BACKEND),
    ".lua": ("Lua", TechCategory.BACKEND),
    ".r": ("R", TechCategory.BACKEND),
    ".jl": ("Julia", TechCategory.BACKEND),
    ".nim": ("Nim", TechCategory.BACKEND),
    ".zig": ("Zig", TechCategory.BACKEND),
    ".ml": ("OCaml", TechCategory.BACKEND),
    ".mli": ("OCaml", TechCategory.BACKEND),
    ".ts": ("TypeScript", TechCategory.BACKEND),
    ".tsx": ("TypeScript/React", TechCategory.FRONTEND),
    ".js": ("JavaScript", TechCategory.BACKEND),
    ".jsx": ("JavaScript/React", TechCategory.FRONTEND),
    ".py": ("Python", TechCategory.BACKEND),
}

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", "env",
    "dist", "build", ".next", ".nuxt", "coverage", ".pytest_cache",
    ".mypy_cache", "target", "bin", "obj", ".gradle",
}

# Minimum number of source files to confidently claim a language
MIN_FILES = 2


def detect_from_extensions(root: Path) -> list[TechnologyDetection]:
    """
    Walk the directory and count source file extensions.
    Returns detections for any language with >= MIN_FILES source files.
    Used as a fallback when no config files were recognised.
    """
    counts: dict[str, int] = {}

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if d not in SKIP_DIRS and not d.startswith(".")
        ]
        for filename in filenames:
            ext = Path(filename).suffix.lower()
            if ext in EXTENSION_MAP:
                counts[ext] = counts.get(ext, 0) + 1

    if not counts:
        return []

    # Group counts by language (prefer the most-specific ext winner)
    lang_counts: dict[str, tuple[int, TechCategory]] = {}
    for ext, count in counts.items():
        lang, category = EXTENSION_MAP[ext]
        # Normalise aliased names (C and C/C++ both count towards C)
        base_lang = lang.split("/")[0]
        prev_count, _ = lang_counts.get(base_lang, (0, category))
        lang_counts[base_lang] = (prev_count + count, category)

    detections: list[TechnologyDetection] = []
    for lang, (count, category) in sorted(lang_counts.items(), key=lambda x: -x[1][0]):
        if count >= MIN_FILES:
            confidence = min(0.5 + (count / 100) * 0.3, 0.75)
            detections.append(TechnologyDetection(
                source_file=str(root),
                tech=lang,
                category=category,
                confidence=round(confidence, 2),
                details=f"Found {count} {lang} source file(s) — no config file detected",
            ))

    return detections
