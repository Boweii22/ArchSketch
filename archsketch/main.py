"""CLI entry point for ArchSketch."""

import base64
import contextlib
import json as _json
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Generator, Optional

import typer
from rich.console import Console

from . import __version__
from .detectors import (
    detect_from_docker_compose,
    detect_from_dockerfile,
    detect_from_env_files,
    detect_from_gradle,
    detect_from_kubernetes,
    detect_from_nginx_conf,
    detect_from_package_json,
    detect_from_pom_xml,
    detect_from_procfile,
    detect_from_requirements,
    detect_from_terraform,
    detect_from_cargo_toml,
    detect_from_go_mod,
    detect_from_csproj,
    detect_from_gemfile,
    detect_from_composer_json,
    detect_from_pubspec_yaml,
    detect_from_mix_exs,
    detect_from_package_swift,
    detect_from_cmake,
    detect_from_extensions,
)
from .inference import InferenceEngine
from .models import TechnologyDetection
from .renderers import render_ascii, render_mermaid
from .renderers.mermaid_renderer import export_mermaid
from .scanner import scan_directory, KEY_KUBERNETES, KEY_TERRAFORM, KEY_CSPROJ

app = typer.Typer(
    name="archsketch",
    help="Infer system architecture from project files.",
    add_completion=False,
)
console = Console()

# ---------------------------------------------------------------------------
# GitHub remote target helpers
# ---------------------------------------------------------------------------

def _parse_github_target(target: str) -> tuple[str, str, str] | None:
    """Parse a GitHub URL or owner/repo shorthand.

    Returns (owner, repo, ref) or None if not a GitHub target.
    """
    # https://github.com/owner/repo  or  https://github.com/owner/repo/tree/branch
    m = re.match(
        r'(?:https?://)?github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/tree/([^\s]+))?/?$',
        target.strip(),
    )
    if m:
        return m.group(1), m.group(2), m.group(3) or ""
    # owner/repo shorthand — exactly two slash-separated parts, owner must start with alphanumeric
    m = re.match(r'^([a-zA-Z0-9][a-zA-Z0-9_.-]*)/([a-zA-Z0-9][a-zA-Z0-9_.-]*)$', target.strip())
    if m:
        return m.group(1), m.group(2), ""
    return None


def _github_api(url: str) -> object:
    """GET a GitHub API URL and return parsed JSON. Raises RuntimeError on failure."""
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                               "User-Agent": "archsketch"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return _json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 403:
            raise RuntimeError(
                "GitHub API rate limit reached (60 req/hr for unauthenticated requests). "
                "Try again later or use --clone."
            )
        if e.code == 404:
            raise RuntimeError("Repository not found or is private.")
        raise RuntimeError(f"GitHub API error {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error: {e.reason}")


# Files/patterns worth fetching from the GitHub tree
_FETCH_EXACT = {
    "package.json", "requirements.txt", "pyproject.toml", "Pipfile",
    "pom.xml", "build.gradle", "build.gradle.kts",
    "docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml",
    "Dockerfile", ".env", ".env.example", ".env.local",
    "nginx.conf", "Procfile", "Makefile",
    "Cargo.toml", "go.mod", "Gemfile", "composer.json",
    "pubspec.yaml", "mix.exs", "Package.swift", "CMakeLists.txt",
}

def _should_fetch(path: str) -> bool:
    """Return True if this tree path is an architecture-relevant file."""
    name = path.split("/")[-1]
    if name in _FETCH_EXACT:
        return True
    if name.startswith("Dockerfile"):
        return True
    if name.startswith("docker-compose") and name.endswith((".yml", ".yaml")):
        return True
    if name.startswith(".env"):
        return True
    if name.endswith(".tf"):
        return True
    if name.endswith((".csproj", ".fsproj", ".vbproj")):
        return True
    # Kubernetes manifests
    if name.endswith((".yaml", ".yml")):
        parts = path.lower().split("/")
        if any(p in ("k8s", "kubernetes", "deploy") for p in parts):
            return True
        if name.split(".")[0] in (
            "deployment", "service", "ingress", "daemonset",
            "statefulset", "cronjob", "job", "configmap", "secret",
        ):
            return True
    return False


def _fetch_github_to_tempdir(owner: str, repo: str, ref: str) -> Path:
    """Download only architecture-relevant files from a public GitHub repo."""
    # 1. Resolve default branch if ref not specified
    if not ref:
        repo_meta = _github_api(f"https://api.github.com/repos/{owner}/{repo}")
        ref = repo_meta["default_branch"]  # type: ignore[index]
        console.print(f"[dim]Default branch: {ref}[/dim]")

    # 2. Fetch the full file tree in one API call
    console.print(f"[dim]Fetching file tree for {owner}/{repo}@{ref}...[/dim]")
    tree_data = _github_api(
        f"https://api.github.com/repos/{owner}/{repo}/git/trees/{ref}?recursive=1"
    )
    all_paths = [
        item["path"]
        for item in tree_data["tree"]  # type: ignore[index]
        if item["type"] == "blob"
    ]

    relevant = [p for p in all_paths if _should_fetch(p)]
    if not relevant:
        console.print("[yellow]No architecture-related files found in repository.[/yellow]")
        return Path(tempfile.mkdtemp(prefix="archsketch_"))

    console.print(f"[dim]Fetching {len(relevant)} architecture file(s)...[/dim]")

    # 3. Fetch each file's content via raw.githubusercontent.com
    tmp = Path(tempfile.mkdtemp(prefix="archsketch_"))
    for path in relevant:
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}"
        req = urllib.request.Request(raw_url, headers={"User-Agent": "archsketch"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read()
        except urllib.error.URLError:
            continue  # skip files we can't fetch
        dest = tmp / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)

    return tmp


def _clone_github(owner: str, repo: str, ref: str) -> Path:
    """Shallow-clone a GitHub repo into a temp dir."""
    url = f"https://github.com/{owner}/{repo}.git"
    tmp = tempfile.mkdtemp(prefix="archsketch_")
    cmd = ["git", "clone", "--depth", "1"]
    if ref:
        cmd += ["--branch", ref]
    cmd += [url, tmp]
    console.print(f"[dim]Cloning {url}...[/dim]")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        shutil.rmtree(tmp, ignore_errors=True)
        raise RuntimeError(f"git clone failed:\n{result.stderr.strip()}")
    return Path(tmp)


@contextlib.contextmanager
def _resolve_target(target: str, clone: bool = False) -> Generator[Path, None, None]:
    """Yield a local Path for target, cloning/fetching if it's a GitHub reference."""
    parsed = _parse_github_target(target)
    if parsed:
        owner, repo, ref = parsed
        tmp: Path | None = None
        try:
            if clone:
                tmp = _clone_github(owner, repo, ref)
            else:
                tmp = _fetch_github_to_tempdir(owner, repo, ref)
            yield tmp
        finally:
            if tmp and tmp.exists():
                shutil.rmtree(tmp, ignore_errors=True)
    else:
        p = Path(target).resolve()
        if not p.exists():
            raise FileNotFoundError(f"Directory not found: {p}")
        if not p.is_dir():
            raise NotADirectoryError(f"Not a directory: {p}")
        yield p


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"ArchSketch v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """ArchSketch - Infer system architecture from project files."""
    pass


def run_detection(path: Path, silent: bool = False) -> tuple[list[TechnologyDetection], "Architecture"]:
    """Run detection and inference on a path."""
    from .models import Architecture
    
    # Scan the directory
    if not silent:
        console.print(f"[dim]Scanning {path}...[/dim]")
    scan_result = scan_directory(path)
    
    # Show what files were found
    file_summary = scan_result.summary()
    if file_summary:
        if not silent:
            console.print(f"[dim]Found: {', '.join(f'{k}({v})' for k, v in file_summary.items())}[/dim]")
    
    # Run detectors
    detections: list[TechnologyDetection] = []
    
    # Package.json detection
    for pkg_file in scan_result.get_files("package.json"):
        detections.extend(detect_from_package_json(pkg_file))
    
    # Requirements/Python detection
    for req_file in scan_result.get_files("requirements.txt"):
        detections.extend(detect_from_requirements(req_file))
    
    for pyproject_file in scan_result.get_files("pyproject.toml"):
        detections.extend(detect_from_requirements(pyproject_file))
    
    for pipfile in scan_result.get_files("Pipfile"):
        detections.extend(detect_from_requirements(pipfile))
    
    # Docker Compose detection
    for compose_file in scan_result.get_files("docker-compose.yml"):
        detections.extend(detect_from_docker_compose(compose_file))
    
    # Dockerfile detection
    for dockerfile in scan_result.get_files("Dockerfile"):
        detections.extend(detect_from_dockerfile(dockerfile))
    
    # Environment file detection
    for env_file in scan_result.get_files(".env"):
        detections.extend(detect_from_env_files(env_file))
    
    # Nginx config detection
    for nginx_file in scan_result.get_files("nginx.conf"):
        detections.extend(detect_from_nginx_conf(nginx_file))
    
    # Maven pom.xml detection (Java/Spring Boot)
    for pom_file in scan_result.get_files("pom.xml"):
        detections.extend(detect_from_pom_xml(pom_file))
    
    # Gradle detection
    for gradle_file in scan_result.get_files("build.gradle") + scan_result.get_files("build.gradle.kts"):
        detections.extend(detect_from_gradle(gradle_file))
    
    # Procfile detection (Heroku-style)
    for procfile in scan_result.get_files("Procfile"):
        detections.extend(detect_from_procfile(procfile))
    
    # Kubernetes manifests
    for k8s_file in scan_result.get_files(KEY_KUBERNETES):
        detections.extend(detect_from_kubernetes(k8s_file))
    
    # Terraform
    for tf_file in scan_result.get_files(KEY_TERRAFORM):
        detections.extend(detect_from_terraform(tf_file))

    # Rust
    for cargo_file in scan_result.get_files("Cargo.toml"):
        detections.extend(detect_from_cargo_toml(cargo_file))

    # Go
    for go_mod_file in scan_result.get_files("go.mod"):
        detections.extend(detect_from_go_mod(go_mod_file))

    # C# / .NET
    for csproj_file in scan_result.get_files(KEY_CSPROJ):
        detections.extend(detect_from_csproj(csproj_file))

    # Ruby
    for gemfile in scan_result.get_files("Gemfile"):
        detections.extend(detect_from_gemfile(gemfile))

    # PHP
    for composer_file in scan_result.get_files("composer.json"):
        detections.extend(detect_from_composer_json(composer_file))

    # Dart / Flutter
    for pubspec_file in scan_result.get_files("pubspec.yaml"):
        detections.extend(detect_from_pubspec_yaml(pubspec_file))

    # Elixir
    for mix_file in scan_result.get_files("mix.exs"):
        detections.extend(detect_from_mix_exs(mix_file))

    # Swift
    for swift_pkg in scan_result.get_files("Package.swift"):
        detections.extend(detect_from_package_swift(swift_pkg))

    # C / C++
    for cmake_file in scan_result.get_files("CMakeLists.txt") + scan_result.get_files("Makefile"):
        detections.extend(detect_from_cmake(cmake_file))

    # Fallback: if nothing detected yet, scan source file extensions
    if not detections:
        detections.extend(detect_from_extensions(path))

    # Run inference
    engine = InferenceEngine()
    architecture = engine.infer(detections)
    
    return detections, architecture


def _build_json_output(detections: list, architecture) -> dict:
    """Build JSON output dictionary (stable schema for CI/scripting)."""
    return {
        "$schema": "schema/architecture.json",
        "version": "1.0",
        "nodes": [
            {
                "id": n.id,
                "label": n.label,
                "role": n.role.value,
                "technologies": n.technologies,
                "sources": n.sources,
                "explanation": n.explanation(),
            }
            for n in architecture.nodes
        ],
        "edges": [
            {
                "source": e.source,
                "target": e.target,
                "relation": e.relation,
            }
            for e in architecture.edges
        ],
        "detections": [
            {
                "tech": d.tech,
                "category": d.category.value,
                "confidence": d.confidence,
                "source_file": d.source_file,
                "details": d.details,
            }
            for d in detections
        ],
    }


@app.command()
def analyze(
    target: str = typer.Argument(
        ...,
        help="Local project path, GitHub URL, or owner/repo (e.g. tiangolo/fastapi).",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output as JSON to stdout.",
    ),
    output_file: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Write JSON output to file.",
    ),
    compact: bool = typer.Option(
        False,
        "--compact",
        "-c",
        help="Show diagram only, no detections table.",
    ),
    no_table: bool = typer.Option(
        False,
        "--no-table",
        help="Same as --compact: diagram only.",
    ),
    show_sources: bool = typer.Option(
        False,
        "--show-sources",
        help="Show 'From: ...' source file in each diagram box.",
    ),
    clone: bool = typer.Option(
        False,
        "--clone",
        help="Clone the repository locally instead of fetching via API (GitHub targets only).",
    ),
) -> None:
    """Analyze a project and display its architecture.

    TARGET can be a local directory, a full GitHub URL, or an owner/repo shorthand:

    \b
      archsketch analyze .
      archsketch analyze https://github.com/tiangolo/fastapi
      archsketch analyze tiangolo/fastapi
      archsketch analyze tiangolo/fastapi --clone
    """
    show_table = not (compact or no_table)

    try:
        with _resolve_target(target, clone=clone) as path:
            detections, architecture = run_detection(path)

            if json_output or output_file:
                import json
                output = _build_json_output(detections, architecture)

                if output_file:
                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(output, f, indent=2)
                    console.print(f"[green]Wrote architecture to: {output_file}[/green]")
                else:
                    console.print_json(json.dumps(output))
            else:
                render_ascii(architecture, console, show_table=show_table, show_sources=show_sources)

    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def export(
    target: str = typer.Argument(
        ...,
        help="Local project path, GitHub URL, or owner/repo.",
    ),
    format: str = typer.Option(
        "mermaid",
        "--format",
        "-f",
        help="Export format: mermaid, graphviz (SVG), or dot.",
    ),
    output: Path = typer.Option(
        Path("architecture.mmd"),
        "--output",
        "-o",
        help="Output file path.",
    ),
    clone: bool = typer.Option(
        False,
        "--clone",
        help="Clone the repository instead of fetching via API (GitHub targets only).",
    ),
) -> None:
    """Export architecture diagram to a file."""

    fmt = format.lower()
    if fmt not in ("mermaid", "graphviz", "svg", "dot"):
        console.print(
            f"[red]Unsupported format: {format}. "
            "Use: mermaid, graphviz (or svg), or dot.[/red]"
        )
        raise typer.Exit(1)

    try:
        with _resolve_target(target, clone=clone) as path:
            _, architecture = run_detection(path)

            if not architecture.nodes:
                console.print("[yellow]No architecture to export.[/yellow]")
                raise typer.Exit(0)

            if fmt == "mermaid":
                output_path = export_mermaid(architecture, output)
                console.print(f"[green]Exported Mermaid diagram to: {output_path}[/green]")
                console.print()
                console.print("[dim]Content:[/dim]")
                console.print(render_mermaid(architecture))
            elif fmt in ("graphviz", "svg"):
                from .renderers.graphviz_renderer import export_svg
                output_path = export_svg(architecture, output)
                console.print(f"[green]Exported SVG to: {output_path}[/green]")
            else:  # dot
                from .renderers.graphviz_renderer import export_dot
                output_path = export_dot(architecture, output)
                console.print(f"[green]Exported DOT to: {output_path}[/green]")

    except RuntimeError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def show(
    target: str = typer.Argument(
        ...,
        help="Local project path, GitHub URL, or owner/repo.",
    ),
    clone: bool = typer.Option(
        False,
        "--clone",
        help="Clone the repository instead of fetching via API (GitHub targets only).",
    ),
) -> None:
    """Show Mermaid diagram in terminal (without exporting)."""

    try:
        with _resolve_target(target, clone=clone) as path:
            _, architecture = run_detection(path)

            if not architecture.nodes:
                console.print("[yellow]No architecture detected.[/yellow]")
                raise typer.Exit(0)

            mermaid_content = render_mermaid(architecture)
            console.print()
            console.print("[bold]Mermaid Diagram:[/bold]")
            console.print()
            console.print(mermaid_content)
            console.print()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def explain(
    target: str = typer.Argument(
        ...,
        help="Local project path, GitHub URL, or owner/repo.",
    ),
    clone: bool = typer.Option(
        False,
        "--clone",
        help="Clone the repository instead of fetching via API (GitHub targets only).",
    ),
) -> None:
    """Explain how the architecture was inferred (show reasoning)."""
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    
    try:
        with _resolve_target(target, clone=clone) as path:
            detections, architecture = run_detection(path)

            if not detections:
                console.print("[yellow]No technologies detected.[/yellow]")
                raise typer.Exit(0)

            console.print()

            # Group detections by category
            from collections import defaultdict
            by_category: dict[str, list] = defaultdict(list)
            for det in detections:
                by_category[det.category.value].append(det)

            # Print detection reasoning
            console.print(Panel(
                "[bold]Detection Reasoning[/bold]\n\n"
                "Below is how ArchSketch analyzed your project files\n"
                "and classified each detected technology.",
                border_style="blue",
            ))
            console.print()

            # Create table for each category
            for category, dets in sorted(by_category.items()):
                table = Table(
                    title=f"[bold]{category.replace('_', ' ').title()}[/bold]",
                    show_header=True,
                    header_style="bold cyan",
                    border_style="dim",
                )
                table.add_column("Technology", style="bold white")
                table.add_column("Confidence", justify="center")
                table.add_column("Source File", style="dim", max_width=30)
                table.add_column("Reasoning", style="yellow", max_width=40)

                seen = set()
                for det in sorted(dets, key=lambda d: -d.confidence):
                    if det.tech in seen:
                        continue
                    seen.add(det.tech)

                    conf_pct = int(det.confidence * 100)
                    if conf_pct >= 90:
                        conf_str = f"[green]{conf_pct}%[/green]"
                    elif conf_pct >= 70:
                        conf_str = f"[yellow]{conf_pct}%[/yellow]"
                    else:
                        conf_str = f"[red]{conf_pct}%[/red]"

                    source = det.source_file
                    if len(source) > 30:
                        source = "..." + source[-27:]

                    reasoning = det.details or "Pattern matched"
                    table.add_row(det.tech, conf_str, source, reasoning)

                console.print(table)
                console.print()

            # Show inference summary
            console.print(Panel("[bold]Inference Summary[/bold]", border_style="green"))

            inference_table = Table(show_header=True, header_style="bold green")
            inference_table.add_column("Role", style="bold")
            inference_table.add_column("Assigned Technology")
            inference_table.add_column("Rule Applied", style="dim")

            for node in architecture.nodes:
                tech = node.technologies[0] if node.technologies else "Unknown"
                rule = _get_inference_rule(node.role.value, tech)
                inference_table.add_row(node.role.value, tech, rule)

            console.print(inference_table)
            console.print()

            if architecture.edges:
                console.print("[bold]Inferred Connections:[/bold]")
                for edge in architecture.edges:
                    source_node = architecture.get_node(edge.source)
                    target_node = architecture.get_node(edge.target)
                    if source_node and target_node:
                        console.print(
                            f"  [cyan]{source_node.role.value}[/cyan] "
                            f"[dim]--{edge.relation}-->[/dim] "
                            f"[cyan]{target_node.role.value}[/cyan]"
                        )
                console.print()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


def _get_inference_rule(role: str, tech: str) -> str:
    """Get a human-readable inference rule description."""
    rules = {
        "Frontend": f"{tech} detected in dependencies -> Frontend role",
        "Backend": f"{tech} is a server framework -> Backend role",
        "Database": f"{tech} is a database system -> Database role",
        "Cache": f"{tech} is a caching system -> Cache role",
        "Reverse Proxy": f"{tech} is a web server/proxy -> Reverse Proxy role",
        "Worker": f"{tech} is a task queue -> Worker role",
        "Queue": f"{tech} is a message broker -> Queue role",
    }
    return rules.get(role, "Pattern matched -> Role assigned")


def _architecture_fingerprint(architecture) -> tuple[set[str], set[tuple[str, str]]]:
    """Return (set of node labels, set of (source,target) edges) for comparison."""
    nodes = set()
    for n in architecture.nodes:
        label = f"{n.role.value}:{n.technologies[0] if n.technologies else '?'}"
        nodes.add(label)
    edges = set()
    for e in architecture.edges:
        edges.add((e.source, e.target))
    return nodes, edges


@app.command()
def diff(
    ref_a: str = typer.Argument(..., help="Base ref (e.g. main, HEAD~1)."),
    ref_b: str = typer.Argument(..., help="Compare ref (e.g. feature-branch)."),
    path: Path = typer.Argument(
        Path("."),
        help="Path inside the git repo (default: current directory).",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
) -> None:
    """Compare architecture between two git refs (branches or commits)."""
    import shutil
    import tempfile
    from pathlib import Path as P
    
    try:
        import git
    except ImportError:
        console.print(
            "[red]GitPython is required for diff. Install with: pip install gitpython[/red]"
        )
        raise typer.Exit(1)
    
    try:
        repo = git.Repo(path, search_parent_directories=True)
    except Exception as e:
        console.print(f"[red]Not a git repository or invalid path: {e}[/red]")
        raise typer.Exit(1)
    
    root = P(repo.working_dir)
    
    def extract_ref(ref: str) -> P:
        try:
            tree = repo.tree(ref)
        except Exception as e:
            raise RuntimeError(f"Invalid ref '{ref}': {e}") from e
        tmp = P(tempfile.mkdtemp(prefix="archsketch_"))
        try:
            for item in tree.traverse():
                if item.type == "blob":
                    out_path = tmp / item.path
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    out_path.write_bytes(item.data_stream.read())
        except Exception:
            shutil.rmtree(tmp, ignore_errors=True)
            raise
        return tmp
    
    tmp_a = tmp_b = None
    try:
        console.print(f"[dim]Extracting {ref_a}...[/dim]")
        tmp_a = extract_ref(ref_a)
        console.print(f"[dim]Extracting {ref_b}...[/dim]")
        tmp_b = extract_ref(ref_b)
        
        _, arch_a = run_detection(tmp_a, silent=True)
        _, arch_b = run_detection(tmp_b, silent=True)
        
        nodes_a, edges_a = _architecture_fingerprint(arch_a)
        nodes_b, edges_b = _architecture_fingerprint(arch_b)
        
        added_nodes = nodes_b - nodes_a
        removed_nodes = nodes_a - nodes_b
        added_edges = edges_b - edges_a
        removed_edges = edges_a - edges_b
        
        # Print diff
        from rich.panel import Panel
        from rich.table import Table
        
        console.print()
        console.print(Panel(
            f"[bold]Architecture diff: {ref_a} vs {ref_b}[/bold]",
            border_style="blue",
        ))
        console.print()
        
        table = Table(show_header=True, header_style="bold")
        table.add_column("Change", style="bold")
        table.add_column("Detail")
        
        if added_nodes:
            for n in sorted(added_nodes):
                table.add_row("[green]+ Component[/green]", n)
        if removed_nodes:
            for n in sorted(removed_nodes):
                table.add_row("[red]- Component[/red]", n)
        if added_edges:
            for (s, t) in sorted(added_edges):
                table.add_row("[green]+ Edge[/green]", f"{s} -> {t}")
        if removed_edges:
            for (s, t) in sorted(removed_edges):
                table.add_row("[red]- Edge[/red]", f"{s} -> {t}")
        
        if not (added_nodes or removed_nodes or added_edges or removed_edges):
            console.print("[dim]No architecture changes between refs.[/dim]")
        else:
            console.print(table)
        console.print()
    
    except RuntimeError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    finally:
        if tmp_a and P(tmp_a).exists():
            shutil.rmtree(tmp_a, ignore_errors=True)
        if tmp_b and P(tmp_b).exists():
            shutil.rmtree(tmp_b, ignore_errors=True)


if __name__ == "__main__":
    app()
