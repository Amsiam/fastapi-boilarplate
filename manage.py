#!/usr/bin/env python3
"""
Management CLI for FastAPI project.
Commands run locally by default. Use --docker to run in Docker container.
"""
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
    """Run the application server locally."""
    cmd = ["uvicorn", "app.main:app", "--host", host, "--port", str(port)]
    if env == "dev" and reload:
        cmd.append("--reload")
    
    console.print(f"[green]Starting server in {env} mode...[/green]")
    subprocess.run(cmd)


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def test(
    ctx: typer.Context,
    docker: bool = typer.Option(False, "--docker", "-d", help="Run tests in Docker container"),
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
            "-e", "TESTING=1",  # Disable rate limiting
            "web", "pytest"
        ]
        cmd.extend(ctx.args)
    else:
        console.print("[green]Running tests locally...[/green]")
        cmd = ["pytest"]
        if watch:
            cmd = ["ptw"]
        
        cmd.extend(ctx.args)
        
        # Set PYTHONPATH to current directory to resolve 'app' module
        env = os.environ.copy()
        env["PYTHONPATH"] = "."
        subprocess.run(cmd, env=env)


@app.command()
def migrate(
    message: str = typer.Option(None, "--message", "-m", help="Migration message"),
    autogenerate: bool = typer.Option(True, help="Autogenerate migration from models"),
    docker: bool = typer.Option(False, "--docker", "-d", help="Run in Docker container"),
):
    """Create a new database migration."""
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
    docker: bool = typer.Option(False, "--docker", "-d", help="Run in Docker container"),
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
    docker: bool = typer.Option(False, "--docker", "-d", help="Run in Docker container"),
):
    """Revert database migrations."""
    if docker:
        console.print(f"[green]Downgrading database to {revision} in Docker...[/green]")
        cmd = ["docker-compose", "-f", "docker-compose.dev.yml", "run", "--rm", "web", "alembic", "downgrade", revision]
    else:
        console.print(f"[green]Downgrading database to {revision} locally...[/green]")
        cmd = ["alembic", "downgrade", revision]
        
    subprocess.run(cmd)


@app.command("docker")
def docker_cmd(
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


# ==================== SEEDER COMMANDS ====================

@app.command("make:seeder")
def make_seeder(
    name: str = typer.Argument(..., help="Name of the seeder (e.g., 'users' creates UsersSeeder)"),
):
    """Create a new seeder file from template."""
    # Convert name to class name (e.g., "users" -> "UsersSeeder", "oauth_providers" -> "OAuthProvidersSeeder")
    class_name = "".join(word.capitalize() for word in name.split("_")) + "Seeder"
    file_name = f"{name.lower()}_seeder.py"
    file_path = os.path.join("seeders", file_name)
    
    if os.path.exists(file_path):
        console.print(f"[red]Seeder already exists: {file_path}[/red]")
        raise typer.Exit(1)
    
    # Generate seeder content
    display_name = name.replace("_", " ").title()
    content = f'''"""
{display_name} Seeder
"""
from sqlmodel import select
from seeders.base import BaseSeeder


class {class_name}(BaseSeeder):
    """Seed {display_name.lower()} data."""
    
    order = 100  # Adjust order as needed (lower runs first)
    
    async def should_run(self) -> bool:
        """Check if this seeder should run."""
        # TODO: Implement check - return True if data needs to be seeded
        # Example: Check if a table is empty
        return True
    
    async def run(self) -> None:
        """Run the seeder."""
        # TODO: Implement seeding logic
        # Example:
        # item = MyModel(name="test")
        # self.session.add(item)
        # await self.session.commit()
        pass
'''
    
    # Write seeder file
    with open(file_path, "w") as f:
        f.write(content)
    
    console.print(f"[green]Created seeder: {file_path}[/green]")
    console.print(f"[dim]Class: {class_name}[/dim]")


@app.command("db:seed")
def db_seed(
    seeder: str = typer.Argument(None, help="Specific seeder to run (e.g., 'permissions', 'roles')"),
    force: bool = typer.Option(False, "--force", "-f", help="Force run even if already seeded"),
    docker: bool = typer.Option(False, "--docker", "-d", help="Run in Docker container"),
):
    """Run database seeders."""
    if docker:
        console.print("[green]Running seeders in Docker...[/green]")
        
        # Build the Python command to run
        if seeder:
            python_cmd = f"""
import asyncio
from app.core.database import engine
from sqlmodel.ext.asyncio.session import AsyncSession
from seeders.runner import run_seeder

async def main():
    async with AsyncSession(engine) as session:
        await run_seeder(session, '{seeder}', force={force})

asyncio.run(main())
"""
        else:
            python_cmd = f"""
import asyncio
from app.core.database import engine
from sqlmodel.ext.asyncio.session import AsyncSession
from seeders.runner import run_all_seeders

async def main():
    async with AsyncSession(engine) as session:
        await run_all_seeders(session, force={force})

asyncio.run(main())
"""
        
        cmd = [
            "docker-compose", "-f", "docker-compose.dev.yml",
            "run", "--rm", "web",
            "python", "-c", python_cmd
        ]
        subprocess.run(cmd)
    else:
        console.print("[green]Running seeders locally...[/green]")
        import asyncio
        from app.core.database import engine
        from sqlmodel.ext.asyncio.session import AsyncSession
        from seeders.runner import run_all_seeders, run_seeder as run_seeder_func
        
        async def run():
            async with AsyncSession(engine) as session:
                if seeder:
                    await run_seeder_func(session, seeder, force=force)
                else:
                    await run_all_seeders(session, force=force)
        
        asyncio.run(run())


@app.command("db:seed:list")
def db_seed_list():
    """List all available seeders."""
    from seeders.runner import discover_seeders
    
    seeders = discover_seeders()
    
    if not seeders:
        console.print("[yellow]No seeders found.[/yellow]")
        return
    
    console.print(f"\n[bold]Available Seeders ({len(seeders)}):[/bold]\n")
    for seeder_class in seeders:
        console.print(f"  [cyan]{seeder_class.__name__}[/cyan] (order: {seeder_class.order})")
    console.print()


if __name__ == "__main__":
    app()
