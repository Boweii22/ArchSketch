"""CLI entry point for ArchSketch."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from . import __version__
from .detectors import (
    detect_from_docker_compose,
    detect_from_dockerfile,
    detect_from_env_files,
    detect_from_package_json,
    detect_from_requirements,
)
from .inference import InferenceEngine
from .models import TechnologyDetection
from .renderers import render_ascii, render_mermaid
from .renderers.mermaid_renderer import export_mermaid
from .scanner import scan_directory

app = typer.Typer(
    name="archsketch",
    help="Infer system architecture from project files.",
    add_completion=False,
)
console = Console()


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


def run_detection(path: Path) -> tuple[list[TechnologyDetection], "Architecture"]:
    """Run detection and inference on a path."""
    from .models import Architecture
    
    # Scan the directory
    console.print(f"[dim]Scanning {path}...[/dim]")
    scan_result = scan_directory(path)
    
    # Show what files were found
    file_summary = scan_result.summary()
    if file_summary:
        console.print(f"[dim]Found: {', '.join(f'{k}({v})' for k, v in file_summary.items())}[/dim]")
    else:
        console.print("[yellow]No architecture-related files found.[/yellow]")
        return [], Architecture()
    
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
    
    # Run inference
    engine = InferenceEngine()
    architecture = engine.infer(detections)
    
    return detections, architecture


@app.command()
def analyze(
    path: Path = typer.Argument(
        ...,
        help="Path to the project directory to analyze.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output as JSON.",
    ),
) -> None:
    """Analyze a project and display its architecture."""
    
    try:
        detections, architecture = run_detection(path)
        
        if json_output:
            import json
            output = {
                "nodes": [
                    {
                        "id": n.id,
                        "label": n.label,
                        "role": n.role.value,
                        "technologies": n.technologies,
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
                    }
                    for d in detections
                ],
            }
            console.print_json(json.dumps(output))
        else:
            render_ascii(architecture, console)
            
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def export(
    path: Path = typer.Argument(
        ...,
        help="Path to the project directory to analyze.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    format: str = typer.Option(
        "mermaid",
        "--format",
        "-f",
        help="Export format (mermaid).",
    ),
    output: Path = typer.Option(
        Path("architecture.mmd"),
        "--output",
        "-o",
        help="Output file path.",
    ),
) -> None:
    """Export architecture diagram to a file."""
    
    if format.lower() != "mermaid":
        console.print(f"[red]Unsupported format: {format}. Use 'mermaid'.[/red]")
        raise typer.Exit(1)
    
    try:
        _, architecture = run_detection(path)
        
        if not architecture.nodes:
            console.print("[yellow]No architecture to export.[/yellow]")
            raise typer.Exit(0)
        
        output_path = export_mermaid(architecture, output)
        console.print(f"[green]Exported Mermaid diagram to: {output_path}[/green]")
        
        # Also show the content
        console.print()
        console.print("[dim]Content:[/dim]")
        mermaid_content = render_mermaid(architecture)
        console.print(mermaid_content)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def show(
    path: Path = typer.Argument(
        ...,
        help="Path to the project directory to analyze.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
) -> None:
    """Show Mermaid diagram in terminal (without exporting)."""
    
    try:
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


if __name__ == "__main__":
    app()
