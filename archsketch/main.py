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
    detect_from_nginx_conf,
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
    
    # Nginx config detection
    for nginx_file in scan_result.get_files("nginx.conf"):
        detections.extend(detect_from_nginx_conf(nginx_file))
    
    # Run inference
    engine = InferenceEngine()
    architecture = engine.infer(detections)
    
    return detections, architecture


def _build_json_output(detections: list, architecture) -> dict:
    """Build JSON output dictionary."""
    return {
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
                "details": d.details,
            }
            for d in detections
        ],
    }


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
        help="Output as JSON to stdout.",
    ),
    output_file: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Write JSON output to file.",
    ),
) -> None:
    """Analyze a project and display its architecture."""
    
    try:
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


@app.command()
def explain(
    path: Path = typer.Argument(
        ...,
        help="Path to the project directory to analyze.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
) -> None:
    """Explain how the architecture was inferred (show reasoning)."""
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    
    try:
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
            
            # Deduplicate by tech name
            seen = set()
            for det in sorted(dets, key=lambda d: -d.confidence):
                if det.tech in seen:
                    continue
                seen.add(det.tech)
                
                # Confidence display
                conf_pct = int(det.confidence * 100)
                if conf_pct >= 90:
                    conf_str = f"[green]{conf_pct}%[/green]"
                elif conf_pct >= 70:
                    conf_str = f"[yellow]{conf_pct}%[/yellow]"
                else:
                    conf_str = f"[red]{conf_pct}%[/red]"
                
                # Truncate source path
                source = det.source_file
                if len(source) > 30:
                    source = "..." + source[-27:]
                
                # Reasoning
                reasoning = det.details or "Pattern matched"
                
                table.add_row(det.tech, conf_str, source, reasoning)
            
            console.print(table)
            console.print()
        
        # Show inference summary
        console.print(Panel(
            "[bold]Inference Summary[/bold]",
            border_style="green",
        ))
        
        inference_table = Table(show_header=True, header_style="bold green")
        inference_table.add_column("Role", style="bold")
        inference_table.add_column("Assigned Technology")
        inference_table.add_column("Rule Applied", style="dim")
        
        for node in architecture.nodes:
            tech = node.technologies[0] if node.technologies else "Unknown"
            
            # Describe the rule
            rule = _get_inference_rule(node.role.value, tech)
            
            inference_table.add_row(
                node.role.value,
                tech,
                rule,
            )
        
        console.print(inference_table)
        console.print()
        
        # Show edges
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


if __name__ == "__main__":
    app()
