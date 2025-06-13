#!/usr/bin/env python3
"""
Main entry point for Odoo Migration v15 to v16

This script provides a CLI interface for managing the entire migration process
from Odoo v15 to v16, including health checks, database setup, analysis, and migration.
"""
from src.config_generator import OdooConfigGenerator
from src.health_check import OdooMigrationHealthChecker
from src.config import get_config
import os
import sys
import click
from pathlib import Path
from typing import Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


@click.group()
@click.option('--config', '-c', default='config.json', help='Configuration file path')
@click.pass_context
def cli(ctx, config):
    """
    🚀 Odoo Migration v15 → v16 Management Tool

    Complete toolset for migrating Odoo from version 15 to version 16.
    Follows Elon Musk principles: simple, fast, effective.
    """
    ctx.ensure_object(dict)
    ctx.obj['config_file'] = config

    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Load configuration
    try:
        if config != 'config.json':
            os.environ['CONFIG_FILE'] = config
        ctx.obj['config'] = get_config()
    except Exception as e:
        console = Console()
        console.print(f"❌ Failed to load configuration: {e}", style="bold red")
        sys.exit(1)


@cli.command()
@click.option('--detailed', '-d', is_flag=True, help='Show detailed information')
@click.option('--fix', '-f', is_flag=True, help='Attempt to fix common issues automatically')
@click.pass_context
def health_check(ctx, detailed, fix):
    """
    🔍 Check environment health

    Verifies that PostgreSQL, Odoo v15, and Odoo v16 are properly configured
    and running. Essential first step before migration.
    """
    console = Console()
    console.print(Panel(
        "Starting environment health check...\n"
        "This will verify all services are ready for migration.",
        title="🔍 Health Check",
        border_style="cyan"
    ))

    try:
        config = ctx.obj['config']
        checker = OdooMigrationHealthChecker(config, detailed, fix)
        results = checker.run_health_check()

        # Exit with appropriate code
        health_percentage = (checker.health_score / checker.max_score) * 100 if checker.max_score > 0 else 0
        if health_percentage < 80:
            console.print(
                "⚠️ Health check indicates issues. Please resolve before proceeding.",
                style="bold yellow"
            )
            sys.exit(1)
        else:
            console.print("✅ Environment is healthy and ready!", style="bold green")

    except Exception as e:
        console.print(f"❌ Health check failed: {e}", style="bold red")
        sys.exit(1)


@cli.command()
@click.option('--version', '-v', type=click.Choice(['v15', 'v16', 'both']), default='both',
              help='Which version to setup (default: both)')
@click.option('--force', '-f', is_flag=True, help='Force recreate existing databases')
@click.option('--modules-only', is_flag=True, help='Only install modules, skip database creation')
@click.pass_context
def setup_db(ctx, version, force, modules_only):
    """
    � Setup demo databases

    Creates demo databases for both v15 and v16 with full Odoo CE modules and sample data.
    This is essential for testing the migration process.
    """
    from src.database_setup import DatabaseSetup

    console = Console()
    config = ctx.obj['config']

    # Hiển thị thông tin
    console.print(Panel.fit(
        f"[bold blue]Database Setup[/bold blue]\n\n"
        f"Version: [cyan]{version}[/cyan]\n"
        f"Force recreate: [cyan]{force}[/cyan]\n"
        f"Modules only: [cyan]{modules_only}[/cyan]\n"
        f"V15 Database: [green]{config.migration.demo_database_v15}[/green]\n"
        f"V16 Database: [green]{config.migration.demo_database_v16}[/green]",
        title="📦 Setup Configuration"
    ))

    try:
        db_setup = DatabaseSetup(config)

        with console.status("[bold green]Setting up demo databases...") as status:
            results = db_setup.setup_demo_databases()

        # Hiển thị kết quả
        _display_setup_results(console, results)

        if results['summary']['failed'] > 0:
            console.print("❌ Some databases failed to setup. Check logs for details.", style="bold red")
            sys.exit(1)
        else:
            console.print("✅ All demo databases setup successfully!", style="bold green")

    except Exception as e:
        console.print(f"❌ Failed to setup databases: {e}", style="bold red")
        sys.exit(1)


@cli.command()
@click.pass_context
def analyze_db(ctx):
    """
    📊 Analyze database structures

    Compares database schemas between v15 and v16 to identify migration requirements.
    """
    console = Console()
    console.print("🚧 Database analysis - Coming soon!", style="bold yellow")
    console.print("This will analyze and compare database structures.")


@cli.command()
@click.pass_context
def plan_migration(ctx):
    """
    📋 Generate migration plan

    Creates a detailed migration blueprint based on database analysis.
    """
    console = Console()
    console.print("🚧 Migration planning - Coming soon!", style="bold yellow")
    console.print("This will generate a detailed migration plan.")


@cli.command()
@click.pass_context
def migrate(ctx):
    """
    🚀 Execute migration

    Runs the actual migration process from v15 to v16.
    """
    console = Console()
    console.print("🚧 Migration execution - Coming soon!", style="bold yellow")
    console.print("This will execute the migration process.")


@cli.command()
@click.pass_context
def validate(ctx):
    """
    ✅ Validate migration

    Verifies that migration completed successfully and data integrity is maintained.
    """
    console = Console()
    console.print("🚧 Migration validation - Coming soon!", style="bold yellow")
    console.print("This will validate the migration results.")


@cli.command()
@click.pass_context
def status(ctx):
    """
    📊 Show migration status

    Displays current status of migration process and environment.
    """
    console = Console()
    config = ctx.obj['config']

    console.print(Panel(
        f"Project: {config.project.name}\n"
        f"Version: {config.project.version}\n"
        f"Workspace: {config.workspace_path}\n"
        f"Network: {config.environment.docker_network}",
        title="📊 Migration Status",
        border_style="blue"
    ))

    # Quick health check
    console.print("\n🔍 Quick Health Check:")
    try:
        from src.utils import DockerManager
        docker = DockerManager()

        containers = [
            config.postgresql.container_name,
            config.odoo_v15.container_name,
            config.odoo_v16.container_name
        ]

        for container in containers:
            status = docker.get_container_status(container)
            if status == "running":
                console.print(f"✅ {container}: Running", style="green")
            elif status:
                console.print(f"⚠️ {container}: {status}", style="yellow")
            else:
                console.print(f"❌ {container}: Not found", style="red")

    except Exception as e:
        console.print(f"❌ Unable to check status: {e}", style="red")


@cli.command()
@click.pass_context
def info(ctx):
    """
    ℹ️ Show configuration information

    Displays detailed configuration and environment information.
    """
    console = Console()
    config = ctx.obj['config']

    # Project info
    console.print(Panel(
        f"Name: {config.project.name}\n"
        f"Version: {config.project.version}\n"
        f"Workspace: {config.workspace_path}",
        title="📦 Project Information",
        border_style="blue"
    ))

    # Service URLs
    console.print(Panel(
        f"Odoo v15: {config.odoo_v15.web_url}\n"
        f"Odoo v16: {config.odoo_v16.web_url}\n"
        f"PostgreSQL: {config.postgresql.host}:{config.postgresql.port}",
        title="🌐 Service URLs",
        border_style="green"
    ))

    # Migration phases
    phases_text = "\n".join([f"  {i + 1}. {phase}" for i, phase in enumerate(config.migration.migration_phases)])
    console.print(Panel(
        phases_text,
        title="📋 Migration Phases",
        border_style="yellow"
    ))


@cli.command()
@click.option('--validate', '-v', is_flag=True, help='Validate generated configurations')
@click.option('--backup', '-b', is_flag=True, default=True, help='Backup existing configs')
@click.pass_context
def config_generate(ctx, validate, backup):
    """
    🔧 Generate optimized Odoo configurations

    Generates clean, optimized odoo.conf files from config.json settings.
    Automatically backs up existing configurations.
    """
    console = Console()
    console.print(Panel(
        "Generating optimized Odoo configuration files...\n"
        "This will standardize configs based on config.json settings.",
        title="🔧 Config Generator",
        border_style="cyan"
    ))

    try:
        config = ctx.obj['config']
        generator = OdooConfigGenerator(config)
        generator.generate_all_configs()

        if validate:
            generator.validate_generated_configs()

        console.print("✅ Configuration generation completed!", style="bold green")

    except Exception as e:
        console.print(f"❌ Configuration generation failed: {e}", style="bold red")
        sys.exit(1)


@cli.command()
@click.pass_context
def check_db(ctx):
    """
    🔍 Check demo databases status

    Checks the status of demo databases and their accessibility.
    """
    from src.database_setup import DatabaseSetup

    console = Console()
    config = ctx.obj['config']

    console.print(Panel.fit(
        "[bold blue]Checking Demo Databases Status[/bold blue]",
        title="🔍 Database Check"
    ))

    try:
        db_setup = DatabaseSetup(config)

        with console.status("[bold green]Checking databases...") as status:
            results = db_setup.check_demo_databases()

        # Hiển thị kết quả
        _display_check_results(console, results)

    except Exception as e:
        console.print(f"❌ Failed to check databases: {e}", style="bold red")
        sys.exit(1)


@cli.command()
@click.option('--version', '-v', type=click.Choice(['v15', 'v16', 'both']), default='both',
              help='Which version to cleanup (default: both)')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def cleanup_db(ctx, version, yes):
    """
    🧹 Cleanup demo databases

    Removes demo databases to free up space or start fresh.
    """
    from src.database_setup import DatabaseSetup

    console = Console()
    config = ctx.obj['config']

    # Confirmation
    if not yes:
        databases = []
        if version in ['v15', 'both']:
            databases.append(config.migration.demo_database_v15)
        if version in ['v16', 'both']:
            databases.append(config.migration.demo_database_v16)

        if not click.confirm(f"Are you sure you want to delete databases: {', '.join(databases)}?"):
            console.print("❌ Operation cancelled.", style="bold yellow")
            return

    try:
        db_setup = DatabaseSetup(config)

        with console.status("[bold red]Cleaning up databases...") as status:
            results = db_setup.cleanup_demo_databases()

        # Hiển thị kết quả
        _display_cleanup_results(console, results)

    except Exception as e:
        console.print(f"❌ Failed to cleanup databases: {e}", style="bold red")
        sys.exit(1)


@cli.command()
@click.option('--version', '-v', type=click.Choice(['v15', 'v16']), required=True,
              help='Which Odoo version to create database for')
@click.option('--name', '-n', help='Database name (default: demo_v15 or demo_v16)')
@click.option('--force', '-f', is_flag=True, help='Force recreate if database exists')
@click.pass_context
def create_demo_db(ctx, version, name, force):
    """
    🏗️ Create demo database with sample data
    
    Creates a new Odoo database with demo data enabled for testing migration.
    This is essential for having realistic data to test the migration process.
    """
    from src.module_installer import OdooModuleInstaller
    
    console = Console()
    config = ctx.obj['config']

    # Determine database name
    if not name:
        name = f"demo_{version}"

    console.print(Panel.fit(
        f"[bold blue]Create Demo Database[/bold blue]\n\n"
        f"Version: [cyan]Odoo {version}[/cyan]\n"
        f"Database: [green]{name}[/green]\n"
        f"Force recreate: [cyan]{force}[/cyan]",
        title="🏗️ Database Creation"
    ))

    try:
        installer = OdooModuleInstaller(config)

        # Check if database exists
        if not force and installer._database_exists_in_postgresql(name):
            console.print(f"❌ Database {name} already exists. Use --force to recreate.", style="bold red")
            return

        # Delete existing database if force
        if force and installer._database_exists_in_postgresql(name):
            console.print(f"🗑️ Removing existing database {name}...")
            if installer._delete_database_from_postgresql(name):
                console.print(f"✅ Database {name} deleted successfully", style="green")
            else:
                console.print(f"⚠️ Failed to delete database {name}, continuing anyway...", style="yellow")

        with console.status(f"[bold green]Creating database {name}...") as status:
            result = installer.create_database_with_demo(version, name)

        # Display result
        if result['status'] == 'completed':
            console.print(f"✅ Database {name} created successfully!", style="bold green")
            
            # Show database info
            console.print(f"\n📊 Database Information:")
            console.print(f"  Name: {name}")
            console.print(f"  Version: Odoo {version}")
            console.print(f"  Demo Data: ✅ Enabled")
            console.print(f"  Admin Login: admin / admin")
            
            # Show access URL
            odoo_config = getattr(config, f'odoo_{version}')
            console.print(f"  URL: {odoo_config.web_url}")
            
        else:
            console.print(f"❌ Failed to create database {name}", style="bold red")
            if 'error' in result:
                console.print(f"Error: {result['error']}", style="red")
            sys.exit(1)

    except Exception as e:
        console.print(f"❌ Failed to create database: {e}", style="bold red")
        sys.exit(1)


@cli.command()
@click.option('--force', '-f', is_flag=True, help='Force recreate if databases exist')
@click.pass_context
def create_demo_pair(ctx, force):
    """
    🏗️ Create demo database pair (v15 + v16)
    
    Creates demo databases for both Odoo v15 and v16 with standardized names
    for easy migration testing.
    """
    from src.module_installer import OdooModuleInstaller
    
    console = Console()
    config = ctx.obj['config']

    demo_v15_name = "demo_v15"
    demo_v16_name = "demo_v16"

    console.print(Panel.fit(
        f"[bold blue]Create Demo Database Pair[/bold blue]\n\n"
        f"V15 Database: [green]{demo_v15_name}[/green]\n"
        f"V16 Database: [green]{demo_v16_name}[/green]\n"
        f"Force recreate: [cyan]{force}[/cyan]",
        title="🏗️ Database Pair Creation"
    ))

    try:
        installer = OdooModuleInstaller(config)

        success_count = 0
        failed_count = 0
        results = {}

        # Create both databases
        for version, db_name in [('v15', demo_v15_name), ('v16', demo_v16_name)]:
            console.print(f"\n🚀 Creating {version.upper()} database: {db_name}")
            
            # Check if database exists
            if not force and installer._database_exists_in_postgresql(db_name):
                console.print(f"⚠️ Database {db_name} already exists. Use --force to recreate.", style="yellow")
                results[version] = {'status': 'skipped', 'reason': 'already_exists'}
                continue

            # Delete existing database if force
            if force and installer._database_exists_in_postgresql(db_name):
                console.print(f"🗑️ Removing existing database {db_name}...")
                if installer._delete_database_from_postgresql(db_name):
                    console.print(f"✅ Database {db_name} deleted successfully", style="green")
                else:
                    console.print(f"⚠️ Failed to delete database {db_name}, continuing anyway...", style="yellow")

            with console.status(f"[bold green]Creating {version} database {db_name}..."):
                result = installer.create_database_with_demo(version, db_name)

            results[version] = result

            if result['status'] == 'completed':
                console.print(f"✅ {version.upper()} database {db_name} created successfully!", style="bold green")
                success_count += 1
            else:
                console.print(f"❌ Failed to create {version} database {db_name}", style="bold red")
                if 'error' in result:
                    console.print(f"Error: {result['error']}", style="red")
                failed_count += 1

        # Display summary
        console.print(f"\n📊 Creation Summary:", style="bold")
        console.print(f"  ✅ Successful: {success_count}", style="green")
        console.print(f"  ❌ Failed: {failed_count}", style="red")
        console.print(f"  ⏭️ Skipped: {len(results) - success_count - failed_count}", style="yellow")

        if success_count > 0:
            console.print(f"\n🌐 Access URLs:", style="bold")
            if 'v15' in results and results['v15']['status'] == 'completed':
                console.print(f"  Odoo v15: {config.odoo_v15.web_url} (admin/admin)", style="green")
            if 'v16' in results and results['v16']['status'] == 'completed':
                console.print(f"  Odoo v16: {config.odoo_v16.web_url} (admin/admin)", style="green")

        if failed_count > 0:
            console.print("⚠️ Some databases failed to create. Check logs for details.", style="yellow")
            sys.exit(1)
        else:
            console.print("🎉 Demo database pair ready for migration testing!", style="bold green")

    except Exception as e:
        console.print(f"❌ Failed to create database pair: {e}", style="bold red")
        sys.exit(1)


@cli.command()
@click.pass_context
def list_demo_db(ctx):
    """
    📋 List all demo databases
    
    Shows all existing demo databases across both Odoo v15 and v16.
    """
    from src.module_installer import OdooModuleInstaller
    
    console = Console()
    config = ctx.obj['config']

    console.print(Panel.fit(
        "[bold blue]Demo Databases List[/bold blue]",
        title="📋 Database Listing"
    ))

    try:
        installer = OdooModuleInstaller(config)
        
        # Get all databases from PostgreSQL
        import psycopg2
        
        host = 'localhost' if config.postgresql.host == 'postgresql' else config.postgresql.host
        
        conn = psycopg2.connect(
            host=host,
            port=config.postgresql.port,
            user=config.postgresql.user,
            password=config.postgresql.password,
            database='postgres'
        )
        
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT datname, pg_size_pretty(pg_database_size(datname)) as size
                FROM pg_database 
                WHERE datname NOT IN ('postgres', 'template0', 'template1')
                AND datname LIKE '%demo%'
                ORDER BY datname
            """)
            
            databases = cursor.fetchall()
        
        conn.close()
        
        if databases:
            from rich.table import Table
            
            table = Table(title="🗃️ Demo Databases")
            table.add_column("Database Name", style="cyan")
            table.add_column("Size", style="green")
            table.add_column("Odoo Version", style="blue")
            table.add_column("Access URL", style="magenta")
            
            for db_name, size in databases:
                # Determine version based on name pattern
                if 'v15' in db_name:
                    version = 'v15'
                    url = config.odoo_v15.web_url
                elif 'v16' in db_name:
                    version = 'v16'
                    url = config.odoo_v16.web_url
                else:
                    version = 'Unknown'
                    url = ''
                
                table.add_row(db_name, size, version, url)
            
            console.print(table)
            console.print(f"\n📊 Total demo databases: {len(databases)}", style="bold green")
        
        else:
            console.print("📝 No demo databases found.", style="yellow")
            console.print("Use 'create-demo-db' command to create demo databases.", style="dim")

    except Exception as e:
        console.print(f"❌ Failed to list databases: {e}", style="bold red")
        sys.exit(1)


def _display_setup_results(console: Console, results: Dict[str, Any]) -> None:
    """Hiển thị kết quả setup database"""
    from rich.table import Table

    # Tạo bảng tổng quan
    summary_table = Table(title="📊 Setup Summary")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")

    summary = results.get('summary', {})
    summary_table.add_row("Total Databases", str(summary.get('total_databases', 0)))
    summary_table.add_row("Successful", str(summary.get('successful', 0)))
    summary_table.add_row("Failed", str(summary.get('failed', 0)))

    console.print(summary_table)

    # Tạo bảng chi tiết
    detail_table = Table(title="📦 Database Details")
    detail_table.add_column("Version", style="cyan")
    detail_table.add_column("Database", style="blue")
    detail_table.add_column("Status", style="bold")
    detail_table.add_column("Steps", style="dim")
    detail_table.add_column("Modules", style="magenta")

    for version in ['v15', 'v16']:
        if version in results:
            result = results[version]
            status_style = "green" if result['status'] == 'completed' else "red"
            status_text = f"[{status_style}]{result['status']}[/{status_style}]"

            steps = ', '.join(result.get('steps', []))
            modules_count = len(result.get('installed_modules', []))

            detail_table.add_row(
                version.upper(),
                result.get('database', ''),
                status_text,
                steps,
                str(modules_count)
            )

    console.print(detail_table)

    # Hiển thị lỗi nếu có
    for version in ['v15', 'v16']:
        if version in results and 'error' in results[version]:
            console.print(f"❌ {version.upper()} Error: {results[version]['error']}", style="bold red")


def _display_check_results(console: Console, results: Dict[str, Any]) -> None:
    """Hiển thị kết quả kiểm tra database"""
    from rich.table import Table

    table = Table(title="🔍 Database Status Check")
    table.add_column("Version", style="cyan")
    table.add_column("Database", style="blue")
    table.add_column("PostgreSQL", style="bold")
    table.add_column("Odoo Access", style="bold")
    table.add_column("Modules", style="magenta")
    table.add_column("Issues", style="red")

    for version in ['v15', 'v16']:
        if version in results:
            result = results[version]

            pg_status = "✅" if result.get('postgresql_exists') else "❌"
            odoo_status = "✅" if result.get('odoo_accessible') else "❌"
            modules_count = result.get('modules_count', 0)
            issues = result.get('error', '')

            table.add_row(
                version.upper(),
                result.get('database', ''),
                pg_status,
                odoo_status,
                str(modules_count),
                issues
            )

    console.print(table)


def _display_cleanup_results(console: Console, results: Dict[str, Any]) -> None:
    """Hiển thị kết quả cleanup database"""
    from rich.table import Table

    table = Table(title="🧹 Cleanup Results")
    table.add_column("Version", style="cyan")
    table.add_column("Database", style="blue")
    table.add_column("Status", style="bold")
    table.add_column("Error", style="red")

    for version in ['v15', 'v16']:
        if version in results:
            result = results[version]
            status_style = "green" if result['status'] == 'completed' else "red"
            status_text = f"[{status_style}]{result['status']}[/{status_style}]"
            error = result.get('error', '')

            table.add_row(
                version.upper(),
                result.get('database', ''),
                status_text,
                error
            )

    console.print(table)


@cli.command()
@click.option('--name', '-n', help='Specific database name to delete')
@click.option('--version', '-v', type=click.Choice(['v15', 'v16']), help='Delete all demo databases for specific version')
@click.option('--all', 'delete_all', is_flag=True, help='Delete all demo databases')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def delete_demo_db(ctx, name, version, delete_all, yes):
    """
    🗑️ Delete demo databases
    
    Removes demo databases. Can delete specific database, all databases for a version,
    or all demo databases at once.
    """
    from src.module_installer import OdooModuleInstaller
    
    console = Console()
    config = ctx.obj['config']

    if not (name or version or delete_all):
        console.print("❌ Please specify --name, --version, or --all", style="bold red")
        return

    try:
        installer = OdooModuleInstaller(config)
        
        # Get list of databases to delete
        databases_to_delete = []
        
        if name:
            databases_to_delete.append(name)
        else:
            # Get all demo databases
            import psycopg2
            
            host = 'localhost' if config.postgresql.host == 'postgresql' else config.postgresql.host
            
            conn = psycopg2.connect(
                host=host,
                port=config.postgresql.port,
                user=config.postgresql.user,
                password=config.postgresql.password,
                database='postgres'
            )
            
            with conn.cursor() as cursor:
                if delete_all:
                    cursor.execute("""
                        SELECT datname FROM pg_database 
                        WHERE datname NOT IN ('postgres', 'template0', 'template1')
                        AND datname LIKE '%demo%'
                        ORDER BY datname
                    """)
                elif version:
                    cursor.execute("""
                        SELECT datname FROM pg_database 
                        WHERE datname NOT IN ('postgres', 'template0', 'template1')
                        AND datname LIKE %s
                        ORDER BY datname
                    """, (f'%demo%{version}%',))
                
                results = cursor.fetchall()
                databases_to_delete = [row[0] for row in results]
            
            conn.close()
        
        if not databases_to_delete:
            console.print("📝 No databases found to delete.", style="yellow")
            return
        
        # Confirmation
        if not yes:
            console.print(f"\n🗑️ Databases to delete:", style="bold red")
            for db in databases_to_delete:
                console.print(f"  • {db}", style="red")
            
            if not click.confirm(f"\nAre you sure you want to delete {len(databases_to_delete)} database(s)?"):
                console.print("❌ Operation cancelled.", style="bold yellow")
                return
        
        # Delete databases
        console.print(Panel.fit(
            f"[bold red]Deleting {len(databases_to_delete)} Database(s)[/bold red]",
            title="🗑️ Database Deletion"
        ))
        
        success_count = 0
        failed_count = 0
        
        for db_name in databases_to_delete:
            with console.status(f"[bold red]Deleting {db_name}..."):
                if installer._delete_database_from_postgresql(db_name):
                    console.print(f"✅ {db_name} deleted successfully", style="green")
                    success_count += 1
                else:
                    console.print(f"❌ Failed to delete {db_name}", style="red")
                    failed_count += 1
        
        # Summary
        console.print(f"\n📊 Deletion Summary:", style="bold")
        console.print(f"  ✅ Successful: {success_count}", style="green")
        console.print(f"  ❌ Failed: {failed_count}", style="red")
        
        if failed_count == 0:
            console.print("🎉 All databases deleted successfully!", style="bold green")
        else:
            console.print("⚠️ Some databases failed to delete. Check logs for details.", style="yellow")

    except Exception as e:
        console.print(f"❌ Failed to delete databases: {e}", style="bold red")
        sys.exit(1)


if __name__ == '__main__':
    cli()
