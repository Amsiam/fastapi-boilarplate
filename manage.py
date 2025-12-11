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



@app.command("make:module")
def make_module(
    name: str = typer.Argument(..., help="Name of the module (e.g., 'products')"),
    with_test: bool = typer.Option(False, "--with-test", "-t", help="Generate a test file for the module"),
    colocated_test: bool = typer.Option(False, "--colocated-test", "-c", help="Generate test file within the module directory"),
):
    """Create a new module with standard structure."""
    module_name = name.lower()
    base_dir = os.path.join("app", "modules", module_name)
    
    if os.path.exists(base_dir):
        console.print(f"[red]Module already exists: {base_dir}[/red]")
        raise typer.Exit(1)
        
    os.makedirs(base_dir)
    console.print(f"[green]Created directory: {base_dir}[/green]")
    
    # Define class names
    class_prefix = "".join(word.capitalize() for word in module_name.split("_"))
    display_name = name.replace("_", " ").title()
    
    # 1. __init__.py
    with open(os.path.join(base_dir, "__init__.py"), "w") as f:
        f.write("")
        
    # 2. models.py
    models_content = f'''from typing import Optional
from sqlmodel import Field
from datetime import datetime
from app.core.base_model import BaseUUIDModel

class {class_prefix}(BaseUUIDModel, table=True):
    """{class_prefix} model."""
    name: str
    description: Optional[str] = None
    # Add your fields here
'''
    with open(os.path.join(base_dir, "models.py"), "w") as f:
        f.write(models_content)
        
    # 3. schemas.py
    schemas_content = f'''from typing import Optional
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class {class_prefix}Base(BaseModel):
    name: str
    description: Optional[str] = None

class {class_prefix}Create({class_prefix}Base):
    pass

class {class_prefix}Update({class_prefix}Base):
    name: Optional[str] = None

class {class_prefix}Response({class_prefix}Base):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
'''
    with open(os.path.join(base_dir, "schemas.py"), "w") as f:
        f.write(schemas_content)
        
    # 4. repository.py
    repo_content = f'''from app.modules.{module_name}.models import {class_prefix}
from app.core.base_repository import BaseRepository
from sqlmodel.ext.asyncio.session import AsyncSession

class {class_prefix}Repository(BaseRepository[{class_prefix}]):
    def __init__(self, session: AsyncSession):
        super().__init__(model={class_prefix}, db=session)
'''
    with open(os.path.join(base_dir, "repository.py"), "w") as f:
        f.write(repo_content)
        
    # 5. service.py
    service_content = f'''from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from app.modules.{module_name}.repository import {class_prefix}Repository
from app.modules.{module_name}.models import {class_prefix}
from app.modules.{module_name}.schemas import {class_prefix}Create, {class_prefix}Update

class {class_prefix}Service:
    def __init__(self, session: AsyncSession):
        self.repository = {class_prefix}Repository(session)

    async def create(self, data: {class_prefix}Create) -> {class_prefix}:
        instance = {class_prefix}(**data.model_dump())
        return await self.repository.create(instance)

    async def get_list(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        search_query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get paginated list with filtering and sorting.
        """
        skip = (page - 1) * per_page
        items, total = await self.repository.get_list(
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
            search_query=search_query,
            search_fields=["name", "description"],
            skip=skip,
            limit=per_page
        )
        
        return {{
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 0
        }}

    async def get_by_id(self, id: UUID) -> {class_prefix}:
        instance = await self.repository.get(id)
        if not instance:
            raise HTTPException(status_code=404, detail="{class_prefix} not found")
        return instance

    async def update(self, id: UUID, data: {class_prefix}Update) -> {class_prefix}:
        instance = await self.get_by_id(id)
        update_data = data.model_dump(exclude_unset=True)
        return await self.repository.update(instance, update_data)

    async def delete(self, id: UUID) -> None:
        await self.repository.delete(id)
'''
    with open(os.path.join(base_dir, "service.py"), "w") as f:
        f.write(service_content)

    # 6. endpoints.py
    endpoints_content = f'''from typing import List, Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query, Request
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_db
from app.core.schemas.response import SuccessResponse, PaginatedResponse
from app.core.docs import doc_responses
from app.modules.{module_name}.service import {class_prefix}Service
from app.modules.{module_name}.schemas import {class_prefix}Response, {class_prefix}Create, {class_prefix}Update

router = APIRouter()

@router.post(
    "/",
    response_model=SuccessResponse[{class_prefix}Response],
    status_code=status.HTTP_201_CREATED,
    summary="Create {display_name}",
    responses=doc_responses(
        success_message="{display_name} created successfully",
        success_status_code=status.HTTP_201_CREATED,
        errors=(400, 422)
    )
)
async def create_{module_name}(
    data: {class_prefix}Create,
    session: AsyncSession = Depends(get_db)
):
    service = {class_prefix}Service(session)
    result = await service.create(data)
    return SuccessResponse(message="{display_name} created successfully", data=result)

@router.get(
    "/",
    response_model=PaginatedResponse[{class_prefix}Response],
    summary="List {display_name}s",
    responses=doc_responses(
        success_message="{display_name}s retrieved successfully",
        errors=(401, 403)
    )
)
async def list_{module_name}s(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    q: Optional[str] = Query(None, description="Search query"),
    sort: str = Query("created_at", description="Sort field"),
    order: str = Query("desc", description="Sort order (asc/desc)"),
    session: AsyncSession = Depends(get_db)
):
    """
    List {display_name}s with filtering, sorting, and search.
    """
    # Construct filters from query params
    filters = {{}}
    for key, value in request.query_params.items():
        if key not in ["page", "per_page", "q", "sort", "order"]:
            filters[key] = value

    service = {class_prefix}Service(session)
    result = await service.get_list(
        page=page,
        per_page=per_page,
        filters=filters,
        sort_by=sort,
        sort_order=order,
        search_query=q
    )
    
    return SuccessResponse(
        message="{display_name}s retrieved successfully", 
        data=result
    )

@router.get(
    "/{{id}}",
    response_model=SuccessResponse[{class_prefix}Response],
    summary="Get {display_name}",
    responses=doc_responses(
        success_message="{display_name} retrieved successfully",
        errors=(401, 403, 404)
    )
)
async def get_{module_name}(
    id: UUID,
    session: AsyncSession = Depends(get_db)
):
    service = {class_prefix}Service(session)
    result = await service.get_by_id(id)
    return SuccessResponse(message="{display_name} retrieved successfully", data=result)

@router.put(
    "/{{id}}",
    response_model=SuccessResponse[{class_prefix}Response],
    summary="Update {display_name}",
    responses=doc_responses(
        success_message="{display_name} updated successfully",
        errors=(401, 403, 404, 422)
    )
)
async def update_{module_name}(
    id: UUID,
    data: {class_prefix}Update,
    session: AsyncSession = Depends(get_db)
):
    service = {class_prefix}Service(session)
    result = await service.update(id, data)
    return SuccessResponse(message="{display_name} updated successfully", data=result)

@router.delete(
    "/{{id}}",
    status_code=status.HTTP_200_OK,
    response_model=SuccessResponse[None],
    summary="Delete {display_name}",
    responses=doc_responses(
        success_message="{display_name} deleted successfully",
        errors=(401, 403, 404)
    )
)
async def delete_{module_name}(
    id: UUID,
    session: AsyncSession = Depends(get_db)
):
    service = {class_prefix}Service(session)
    await service.delete(id)
    return SuccessResponse(message="{display_name} deleted successfully", data=None)
'''
    with open(os.path.join(base_dir, "endpoints.py"), "w") as f:
        f.write(endpoints_content)

    console.print(f"[green]Successfully created module '{module_name}' structure in {base_dir}[/green]")

    # 7. Create tests if requested
    if with_test or colocated_test:
        if colocated_test:
            test_dir = os.path.join(base_dir, "tests")
            # Create __init__.py for test discovery in module
            os.makedirs(test_dir, exist_ok=True)
            with open(os.path.join(test_dir, "__init__.py"), "w") as f:
                f.write("")
        else:
            test_dir = os.path.join("tests", "modules")
            os.makedirs(test_dir, exist_ok=True)
            
        test_file_path = os.path.join(test_dir, f"test_{module_name}.py")
        
        test_content = f'''import pytest
from httpx import AsyncClient
from app.modules.{module_name}.models import {class_prefix}

@pytest.mark.asyncio
async def test_create_{module_name}(client: AsyncClient):
    payload = {{"name": "Test {display_name}"}} 
    response = await client.post("/api/v1/{module_name}/", json=payload)
    if response.status_code != 201:
        print(response.json())
    assert response.status_code == 201
    assert response.json()["success"] is True
    assert response.json()["data"]["name"] == "Test {display_name}"

@pytest.mark.asyncio
async def test_list_{module_name}s_filtering(client: AsyncClient):
    # Create two items
    await client.post("/api/v1/{module_name}/", json={{"name": "Alpha"}})
    await client.post("/api/v1/{module_name}/", json={{"name": "Beta"}})
    
    # Test Search
    response = await client.get("/api/v1/{module_name}/?q=Alpha")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Alpha"

    # Test Sorting
    response = await client.get("/api/v1/{module_name}/?sort=name&order=desc")
    assert response.status_code == 200
    data = response.json()["data"]
    names = [item["name"] for item in data["items"]]
    # Ensure Beta comes before Alpha (Desc: Beta > Alpha)
    try:
        beta_idx = names.index("Beta")
        alpha_idx = names.index("Alpha")
        assert beta_idx < alpha_idx
    except ValueError:
        pytest.fail("Alpha or Beta not found in response")
'''
        with open(test_file_path, "w") as f:
            f.write(test_content)
        console.print(f"[green]Created test file: {test_file_path}[/green]")

    # 8. Register in router.py
    router_file = os.path.join("app", "api", "v1", "router.py")
    if os.path.exists(router_file):
        try:
            with open(router_file, "r") as f:
                content = f.read()
            
            # Prepare lines to add
            import_line = f"from app.modules.{module_name} import endpoints as {module_name}"
            include_line = f'api_router.include_router({module_name}.router, prefix="/{module_name}", tags=["{display_name}"])'
            
            if import_line not in content:
                lines = content.splitlines()
                last_import_idx = 0
                for i, line in enumerate(lines):
                    if line.startswith("from ") or line.startswith("import "):
                        last_import_idx = i
                
                # Insert import after last import
                lines.insert(last_import_idx + 1, import_line)
                
                # Append include_router at the end
                lines.append(include_line)
                
                new_content = "\n".join(lines) + "\n"
                
                with open(router_file, "w") as f:
                    f.write(new_content)
                    
                console.print(f"[green]Registered module in router: {router_file}[/green]")
            else:
                console.print(f"[yellow]Module seems already registered in router.[/yellow]")
        except Exception as e:
            console.print(f"[red]Failed to register in router: {str(e)}[/red]")


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
