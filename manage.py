#!/usr/bin/env python3
import os
import subprocess
import typer
from rich.console import Console

app = typer.Typer(help="Management script for the FastAPI project.")
console = Console()

@app.command()
def run(
    env: str = typer.Option("dev", help="Environment to run in (dev/prod)"),
    reload: bool = typer.Option(True, help="Enable auto-reload (dev only)"),
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
):
    """Run the application server."""
    if env == "prod":
        cmd = ["uvicorn", "app.main:app", "--host", host, "--port", str(port)]
    else:
        cmd = ["uvicorn", "app.main:app", "--host", host, "--port", str(port)]
        if reload:
            cmd.append("--reload")
    
    console.print(f"[green]Starting server in {env} mode...[/green]")
    subprocess.run(cmd)

@app.command()
def test(
    docker: bool = typer.Option(True, help="Run tests in Docker container"),
    watch: bool = typer.Option(False, help="Watch for changes (requires pytest-watch)"),
):
    """Run the test suite."""
    if docker:
        console.print("[green]Running tests in Docker...[/green]")
        cmd = [
            "docker-compose", "-f", "docker-compose.dev.yml", 
            "run", "--rm", 
            "-e", "PYTHONPATH=.", 
            "-e", "POSTGRES_SERVER=db", 
            "web", "pytest"
        ]
    else:
        console.print("[green]Running tests locally...[/green]")
        cmd = ["pytest"]
        if watch:
            cmd = ["ptw"]
            
    subprocess.run(cmd)

@app.command()
def migrate(
    message: str = typer.Option(None, "--message", "-m", help="Migration message"),
    autogenerate: bool = typer.Option(True, help="Autogenerate migration from models"),
    docker: bool = typer.Option(True, help="Run in Docker container"),
):
    """Create a new migration."""
    if docker:
        console.print("[green]Creating migration in Docker...[/green]")
        cmd = ["docker-compose", "-f", "docker-compose.dev.yml", "run", "--rm", "web", "alembic", "revision"]
    else:
        console.print("[green]Creating migration locally...[/green]")
        cmd = ["alembic", "revision"]
        
    if autogenerate:
        cmd.append("--autogenerate")
    if message:
        cmd.extend(["-m", message])
        
    subprocess.run(cmd)

@app.command()
def upgrade(
    revision: str = typer.Option("head", help="Revision to upgrade to"),
    docker: bool = typer.Option(True, help="Run in Docker container"),
):
    """Apply database migrations."""
    if docker:
        console.print(f"[green]Upgrading database to {revision} in Docker...[/green]")
        cmd = ["docker-compose", "-f", "docker-compose.dev.yml", "run", "--rm", "web", "alembic", "upgrade", revision]
    else:
        console.print(f"[green]Upgrading database to {revision} locally...[/green]")
        cmd = ["alembic", "upgrade", revision]
        
    subprocess.run(cmd)

@app.command()
def downgrade(
    revision: str = typer.Option("-1", help="Revision to downgrade to"),
    docker: bool = typer.Option(True, help="Run in Docker container"),
):
    """Revert database migrations."""
    if docker:
        console.print(f"[green]Downgrading database to {revision} in Docker...[/green]")
        cmd = ["docker-compose", "-f", "docker-compose.dev.yml", "run", "--rm", "web", "alembic", "downgrade", revision]
    else:
        console.print(f"[green]Downgrading database to {revision} locally...[/green]")
        cmd = ["alembic", "downgrade", revision]
        
    subprocess.run(cmd)

@app.command()
def docker(
    action: str = typer.Argument(..., help="Action to perform (up/down/build/logs)"),
    env: str = typer.Option("dev", help="Environment (dev/prod)"),
    detach: bool = typer.Option(False, "--detach", "-d", help="Run in background"),
):
    """Manage Docker containers."""
    compose_file = "docker-compose.yml" if env == "prod" else "docker-compose.dev.yml"
    cmd = ["docker-compose", "-f", compose_file, action]
    
    if action == "up":
        cmd.append("--build")
        if detach:
            cmd.append("-d")
            
    console.print(f"[green]Running docker-compose {action} for {env}...[/green]")
    subprocess.run(cmd)

if __name__ == "__main__":
    app()
