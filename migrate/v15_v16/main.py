#!/usr/bin/env python3
"""
Main entry point for Odoo Migration v15 to v16

This script provides a CLI interface for managing the entire migration process
from Odoo v15 to v16, including health checks, database setup, analysis, and migration.
"""
from src.config import get_config
from src.health import OdooMigrationHealthChecker
from src.config_generator import OdooConfigGenerator
import sys
import os
import click
from pathlib import Path
from typing import Dict, Any, List, Tuple
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
        health_percentage = (
            checker.health_score / checker.max_score) * 100 if checker.max_score > 0 else 0
        if health_percentage < 80:
            console.print(
                "⚠️ Health check indicates issues. Please resolve before proceeding.",
                style="bold yellow"
            )
            sys.exit(1)
        else:
            console.print("✅ Environment is healthy and ready!",
                          style="bold green")

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
        f"V15 Database: [green]{config['migration']['demo_database_v15']}[/green]\n"
        f"V16 Database: [green]{config['migration']['demo_database_v16']}[/green]",
        title="📦 Setup Configuration"
    ))

    try:
        db_setup = DatabaseSetup(config)

        with console.status("[bold green]Setting up demo databases...") as status:
            results = db_setup.setup_demo_databases()

        # Hiển thị kết quả
        _display_setup_results(console, results)

        if results['summary']['failed'] > 0:
            console.print(
                "❌ Some databases failed to setup. Check logs for details.", style="bold red")
            sys.exit(1)
        else:
            console.print(
                "✅ All demo databases setup successfully!", style="bold green")

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
        f"Project: {config['project']['name']}\n"
        f"Version: {config['project']['version']}\n"
        f"Workspace: {config.get('workspace_path', config['project'].get('workspace_root', '../../'))}\n"
        f"Network: {config['environment']['docker_network']}",
        title="📊 Migration Status",
        border_style="blue"
    ))

    # Quick health check
    console.print("\n🔍 Quick Health Check:")
    try:
        from src.utils import DockerManager
        docker = DockerManager()

        containers = [
            config['postgresql']['container_name'],
            config['odoo_v15']['container_name'],
            config['odoo_v16']['container_name']
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
    config = ctx.obj['config']    # Project info
    console.print(Panel(
        f"Name: {config['project']['name']}\n"
        f"Version: {config['project']['version']}\n"
        f"Workspace: {config.get('workspace_path', config['project'].get('workspace_root', '../../'))}",
        title="📦 Project Information",
        border_style="blue"
    ))

    # Service URLs
    console.print(Panel(
        f"Odoo v15: {config['odoo_v15']['web_url']}\n"
        f"Odoo v16: {config['odoo_v16']['web_url']}\n"
        f"PostgreSQL: {config['postgresql']['host']}:{config['postgresql']['port']}",
        title="🌐 Service URLs",
        border_style="green"
    ))

    # Migration phases
    phases_text = "\n".join(
        [f"  {i + 1}. {phase}" for i, phase in enumerate(config['migration']['migration_phases'])])
    console.print(Panel(
        phases_text,
        title="📋 Migration Phases",
        border_style="yellow"
    ))


@cli.command()
@click.option('--validate', '-v', is_flag=True, help='Validate generated configurations')
@click.option('--backup', '-b', is_flag=True, default=True, help='Backup existing configs')
@click.option('--sync', '-s', is_flag=True, help='Full synchronization mode (recommended)')
@click.pass_context
def config_generate(ctx, validate, backup, sync):
    """
    🔧 Generate optimized Odoo configurations

    Generates clean, optimized odoo.conf files from config.json settings.
    Automatically backs up existing configurations.
    Use --sync for full synchronization mode with detailed reporting.
    """
    console = Console()

    if sync:
        console.print(Panel(
            "[bold blue]🔄 Synchronizing Odoo configurations from config.json[/bold blue]\n\n"
            "This will generate fresh odoo.conf files based on your config.json settings.\n"
            "Existing configurations will be backed up automatically.",
            title="Configuration Synchronization",
            border_style="cyan"
        ))
    else:
        console.print(Panel(
            "Generating optimized Odoo configuration files...\n"
            "This will standardize configs based on config.json settings.",
            title="🔧 Config Generator",
            border_style="cyan"
        ))

    try:
        config = ctx.obj['config']
        generator = OdooConfigGenerator(config)

        if sync:
            # Full synchronization mode with detailed reporting
            results = generator.sync_all_configs()

            # Auto-validate in sync mode
            if any(r['status'] == 'success' for r in results.values()):
                generator.validate_generated_configs()
        else:
            # Legacy mode for backward compatibility
            generator.generate_all_configs()

            # Validate if requested
            if validate:
                generator.validate_generated_configs()

        console.print("✅ Configuration generation completed!",
                      style="bold green")

    except Exception as e:
        console.print(
            f"❌ Configuration generation failed: {e}", style="bold red")
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
            databases.append(config['migration']['demo_database_v15'])
        if version in ['v16', 'both']:
            databases.append(config['migration']['demo_database_v16'])

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
            console.print(
                f"❌ Database {name} already exists. Use --force to recreate.", style="bold red")
            return

        # Delete existing database if force
        if force and installer._database_exists_in_postgresql(name):
            console.print(f"🗑️ Removing existing database {name}...")
            if installer._delete_database_from_postgresql(name):
                console.print(
                    f"✅ Database {name} deleted successfully", style="green")
            else:
                console.print(
                    f"⚠️ Failed to delete database {name}, continuing anyway...", style="yellow")

        with console.status(f"[bold green]Creating database {name}...") as status:
            result = installer.create_database_with_demo(version, name)

        # Display result
        if result['status'] == 'completed':
            console.print(
                f"✅ Database {name} created successfully!", style="bold green")

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
            console.print(
                f"❌ Failed to create database {name}", style="bold red")
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
            console.print(
                f"\n🚀 Creating {version.upper()} database: {db_name}")

            # Check if database exists
            if not force and installer._database_exists_in_postgresql(db_name):
                console.print(
                    f"⚠️ Database {db_name} already exists. Use --force to recreate.", style="yellow")
                results[version] = {'status': 'skipped',
                                    'reason': 'already_exists'}
                continue

            # Delete existing database if force
            if force and installer._database_exists_in_postgresql(db_name):
                console.print(f"🗑️ Removing existing database {db_name}...")
                if installer._delete_database_from_postgresql(db_name):
                    console.print(
                        f"✅ Database {db_name} deleted successfully", style="green")
                else:
                    console.print(
                        f"⚠️ Failed to delete database {db_name}, continuing anyway...", style="yellow")

            with console.status(f"[bold green]Creating {version} database {db_name}..."):
                result = installer.create_database_with_demo(version, db_name)

            results[version] = result

            if result['status'] == 'completed':
                console.print(
                    f"✅ {version.upper()} database {db_name} created successfully!", style="bold green")
                success_count += 1
            else:
                console.print(
                    f"❌ Failed to create {version} database {db_name}", style="bold red")
                if 'error' in result:
                    console.print(f"Error: {result['error']}", style="red")
                failed_count += 1

        # Display summary
        console.print(f"\n📊 Creation Summary:", style="bold")
        console.print(f"  ✅ Successful: {success_count}", style="green")
        console.print(f"  ❌ Failed: {failed_count}", style="red")
        console.print(
            f"  ⏭️ Skipped: {len(results) - success_count - failed_count}", style="yellow")

        if success_count > 0:
            console.print(f"\n🌐 Access URLs:", style="bold")
            if 'v15' in results and results['v15']['status'] == 'completed':
                console.print(
                    f"  Odoo v15: {config['odoo_v15']['web_url']} (admin/admin)", style="green")
            if 'v16' in results and results['v16']['status'] == 'completed':
                console.print(
                    f"  Odoo v16: {config['odoo_v16']['web_url']} (admin/admin)", style="green")

        if failed_count > 0:
            console.print(
                "⚠️ Some databases failed to create. Check logs for details.", style="yellow")
            sys.exit(1)
        else:
            console.print(
                "🎉 Demo database pair ready for migration testing!", style="bold green")

    except Exception as e:
        console.print(
            f"❌ Failed to create database pair: {e}", style="bold red")
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

        host = 'localhost' if config['postgresql']['host'] == 'postgresql' else config['postgresql']['host']

        conn = psycopg2.connect(
            host=host,
            port=config['postgresql']['port'],
            user=config['postgresql']['user'],
            password=config['postgresql']['password'],
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
                    url = config['odoo_v15']['web_url']
                elif 'v16' in db_name:
                    version = 'v16'
                    url = config['odoo_v16']['web_url']
                else:
                    version = 'Unknown'
                    url = ''

                table.add_row(db_name, size, version, url)

            console.print(table)
            console.print(
                f"\n📊 Total demo databases: {len(databases)}", style="bold green")

        else:
            console.print("📝 No demo databases found.", style="yellow")
            console.print(
                "Use 'create-demo-db' command to create demo databases.", style="dim")

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
    summary_table.add_row("Total Databases", str(
        summary.get('total_databases', 0)))
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
            console.print(
                f"❌ {version.upper()} Error: {results[version]['error']}", style="bold red")


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


def _display_delete_results(console: Console, results: Dict[str, Any], databases: List[Tuple[str, str]]) -> None:
    """Display database deletion results"""
    from rich.table import Table

    # Create summary table
    summary_table = Table(title="🗑️ Deletion Summary")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")

    total_requested = len(databases)
    successful = sum(1 for db_version, _ in databases if results.get(
        db_version, {}).get('deleted', False))
    failed = total_requested - successful

    summary_table.add_row("Total Requested", str(total_requested))
    summary_table.add_row("Successfully Deleted", str(successful))
    summary_table.add_row("Failed", str(failed))

    console.print(summary_table)

    # Create detailed table
    detail_table = Table(title="📦 Database Deletion Details")
    detail_table.add_column("Version", style="cyan")
    detail_table.add_column("Database", style="blue")
    detail_table.add_column("Status", style="bold")
    detail_table.add_column("Error", style="red")

    for db_version, db_name in databases:
        result = results.get(db_version, {})

        if result.get('deleted', False):
            status_text = "[green]✅ Deleted[/green]"
            error_text = ""
        elif result.get('error'):
            status_text = "[red]❌ Failed[/red]"
            error_text = result['error']
        else:
            status_text = "[yellow]⚠️ Not Found[/yellow]"
            error_text = "Database did not exist"

        detail_table.add_row(
            db_version.upper(),
            db_name,
            status_text,
            error_text
        )

    console.print(detail_table)


def _display_demo_creation_results(console: Console, results: Dict[str, Any], databases: List[Tuple[str, str]]) -> None:
    """Display demo database creation results"""
    from rich.table import Table

    # Create summary table
    summary_table = Table(title="🏗️ Creation Summary")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")

    total_requested = len(databases)
    successful = sum(1 for db_version, _ in databases if results.get(
        db_version, {}).get('status') == 'completed')
    failed = total_requested - successful

    summary_table.add_row("Total Requested", str(total_requested))
    summary_table.add_row("Successfully Created", str(successful))
    summary_table.add_row("Failed", str(failed))

    console.print(summary_table)

    # Create detailed table
    detail_table = Table(title="📦 Database Creation Details")
    detail_table.add_column("Version", style="cyan")
    detail_table.add_column("Database", style="blue")
    detail_table.add_column("Status", style="bold")
    detail_table.add_column("Modules", style="magenta")

    for db_version, db_name in databases:
        result = results.get(db_version, {})

        if result.get('status') == 'completed':
            status_text = "[green]✅ Created[/green]"
            modules_text = "✅" if result.get(
                'modules_installed') else "Not installed"
        else:
            status_text = "[red]❌ Failed[/red]"
            modules_text = "N/A"

        detail_table.add_row(
            db_version.upper(),
            db_name,
            status_text,
            modules_text
        )

    console.print(detail_table)


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
        console.print(
            "❌ Please specify --name, --version, or --all", style="bold red")
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

            host = 'localhost' if config['postgresql']['host'] == 'postgresql' else config['postgresql']['host']

            conn = psycopg2.connect(
                host=host,
                port=config['postgresql']['port'],
                user=config['postgresql']['user'],
                password=config['postgresql']['password'],
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
                    console.print(
                        f"✅ {db_name} deleted successfully", style="green")
                    success_count += 1
                else:
                    console.print(f"❌ Failed to delete {db_name}", style="red")
                    failed_count += 1

        # Summary
        console.print(f"\n📊 Deletion Summary:", style="bold")
        console.print(f"  ✅ Successful: {success_count}", style="green")
        console.print(f"  ❌ Failed: {failed_count}", style="red")

        if failed_count == 0:
            console.print("🎉 All databases deleted successfully!",
                          style="bold green")
        else:
            console.print(
                "⚠️ Some databases failed to delete. Check logs for details.", style="yellow")

    except Exception as e:
        console.print(f"❌ Failed to delete databases: {e}", style="bold red")
        sys.exit(1)


@cli.command('delete-db')
@click.option('--version', '-v', type=click.Choice(['v15', 'v16', 'both']), default='both',
              help='Which version database to delete (default: both)')
@click.option('--force', '-f', is_flag=True, help='Skip confirmation prompt')
@click.option('--yes', '-y', is_flag=True, help='Automatically answer yes to prompts')
@click.pass_context
def delete_db(ctx, version, force, yes):
    """
    🗑️ Delete demo databases

    Safely removes demo databases for v15 and/or v16 with confirmation.
    Use with caution - this action cannot be undone!
    """
    from src.database_setup import DatabaseSetup

    console = Console()
    config = ctx.obj['config']

    # Determine which databases to delete
    databases = []
    if version in ['v15', 'both']:
        databases.append(('v15', config['migration']['demo_database_v15']))
    if version in ['v16', 'both']:
        databases.append(('v16', config['migration']['demo_database_v16']))

    # Display warning and confirmation
    console.print(Panel(
        f"[bold red]⚠️ WARNING: DATABASE DELETION[/bold red]\n\n"
        f"This will permanently delete the following databases:\n" +
        "\n".join([f"• {db[0].upper()}: [yellow]{db[1]}[/yellow]" for db in databases]) +
        f"\n\n[bold red]This action cannot be undone![/bold red]",
        title="🗑️ Database Deletion",
        border_style="red"
    ))

    # Confirmation unless forced or yes flag
    if not force and not yes:
        confirm = click.confirm(
            f"Are you sure you want to delete {len(databases)} database(s)?",
            default=False
        )
        if not confirm:
            console.print("Operation cancelled.", style="yellow")
            return

    try:
        db_setup = DatabaseSetup(config)

        with console.status("[bold red]Deleting demo databases...") as status:
            # Use the existing cleanup method with force=True
            results = db_setup.cleanup_demo_databases(force=True)

        # Display results
        _display_delete_results(console, results, databases)

        # Check if any deletions failed
        failed = []
        for db_version, db_name in databases:
            if results.get(db_version, {}).get('error'):
                failed.append(f"{db_version} ({db_name})")

        if failed:
            console.print(
                f"❌ Failed to delete: {', '.join(failed)}. Check logs for details.",
                style="bold red"
            )
            sys.exit(1)
        else:
            console.print(
                "✅ All requested databases deleted successfully!",
                style="bold green"
            )

            # Validate deletion using MCP PostgreSQL
            console.print("\n🔍 Validating deletion using MCP PostgreSQL...")
            from src.utils import validate_database_deletion_mcp

            deleted_db_names = [db_name for _, db_name in databases]
            validation = validate_database_deletion_mcp(deleted_db_names)

            if validation['status'] == 'success':
                console.print(
                    f"✅ MCP Validation: {validation['successfully_deleted']}/{validation['total_checked']} databases confirmed deleted",
                    style="bold green"
                )
                console.print(
                    f"📊 Current database count: {validation['database_count']}",
                    style="dim"
                )
            elif validation['status'] == 'partial_failure':
                console.print(
                    f"⚠️ MCP Validation: {len(validation['still_exists'])} databases still exist: {', '.join(validation['still_exists'])}",
                    style="bold yellow"
                )
            else:
                console.print(
                    f"❌ MCP Validation failed: {validation.get('error', 'Unknown error')}",
                    style="bold red"
                )

    except Exception as e:
        console.print(f"❌ Failed to delete databases: {e}", style="bold red")
        sys.exit(1)


@cli.command()
@click.pass_context
def check(ctx):
    """
    🔍 Quick health check (simplified command)

    Runs a detailed health check with all features enabled.
    Equivalent to: python main.py health-check --detailed --fix
    """
    # Call health_check with detailed=True and fix=True
    ctx.invoke(health_check, detailed=True, fix=True)


def delete_db_entry():
    """Entry point for delete-db command"""
    try:
        from pathlib import Path
        import sys

        # Add src to Python path
        project_root = Path(__file__).parent
        src_path = project_root / 'src'
        sys.path.insert(0, str(src_path))

        # Change to script directory
        os.chdir(str(project_root))

        console = Console()
        console.print(Panel(
            "🗑️ Database Deletion Tool\n"
            "Delete Odoo v15/v16 demo databases safely with confirmation.",
            title="Database Deletion",
            border_style="red"
        ))

        # Parse command line arguments manually
        args = sys.argv[1:]  # Skip script name

        # Create a context for the CLI
        ctx = click.Context(cli)
        ctx.obj = {'config_file': 'config.json'}

        # Load configuration
        try:
            ctx.obj['config'] = get_config()
        except Exception as e:
            console.print(
                f"❌ Failed to load configuration: {e}", style="bold red")
            sys.exit(1)

        # Parse the arguments for delete_db command
        version = 'both'
        force = False
        yes = False

        i = 0
        while i < len(args):
            if args[i] in ['-v', '--version'] and i + 1 < len(args):
                version = args[i + 1]
                i += 2
            elif args[i] in ['-f', '--force']:
                force = True
                i += 1
            elif args[i] in ['-y', '--yes']:
                yes = True
                i += 1
            elif args[i] == '--help':
                # Show help for delete-db command
                console.print("Usage: delete-db [OPTIONS]")
                console.print("  🗑️ Delete demo databases")
                console.print(
                    "  Safely removes demo databases for v15 and/or v16 with confirmation.")
                console.print(
                    "  Use with caution - this action cannot be undone!")
                console.print("\nOptions:")
                console.print(
                    "  -v, --version [v15|v16|both]  Which version database to delete (default: both)")
                console.print(
                    "  -f, --force                   Skip confirmation prompt")
                console.print(
                    "  -y, --yes                     Automatically answer yes to prompts")
                console.print(
                    "  --help                        Show this message and exit.")
                return
            else:
                i += 1

        from src.database_setup import DatabaseSetup

        config = ctx.obj['config']

        # Determine which databases to delete
        databases = []
        if version in ['v15', 'both']:
            databases.append(('v15', config['migration']['demo_database_v15']))
        if version in ['v16', 'both']:
            databases.append(('v16', config['migration']['demo_database_v16']))

        # Display warning and confirmation
        console.print(Panel(
            f"[bold red]⚠️ WARNING: DATABASE DELETION[/bold red]\n\n"
            f"This will permanently delete the following databases:\n" +
            "\n".join([f"• {db[0].upper()}: [yellow]{db[1]}[/yellow]" for db in databases]) +
            f"\n\n[bold red]This action cannot be undone![/bold red]",
            title="🗑️ Database Deletion",
            border_style="red"
        ))        # Confirmation unless forced or yes flag
        if not force and not yes:
            confirm = input(
                f"Are you sure you want to delete {len(databases)} database(s)? [y/N]: ").lower().strip()
            if confirm not in ['y', 'yes']:
                console.print("Operation cancelled.", style="yellow")
                return

        db_setup = DatabaseSetup(config)

        with console.status("[bold red]Deleting demo databases...") as status:
            # Use the existing cleanup method with force=True
            results = db_setup.cleanup_demo_databases(force=True)

        # Display results
        _display_delete_results(console, results, databases)

        # Check if any deletions failed
        failed = []
        for db_version, db_name in databases:
            if results.get(db_version, {}).get('error'):
                failed.append(f"{db_version} ({db_name})")

        if failed:
            console.print(
                f"❌ Failed to delete: {', '.join(failed)}. Check logs for details.",
                style="bold red"
            )
            sys.exit(1)
        else:
            console.print(
                "✅ All requested databases deleted successfully!",
                style="bold green"
            )

    except Exception as e:
        console.print(f"❌ Failed to delete databases: {e}", style="bold red")
        sys.exit(1)


def health_check_entry():
    """Entry point for health-check command"""
    import os
    import sys
    from pathlib import Path

    # Add src to Python path
    project_root = Path(__file__).parent
    src_path = project_root / 'src'
    sys.path.insert(0, str(src_path))

    # Change to script directory
    os.chdir(str(project_root))

    # Run health check with detailed and fix enabled
    try:
        from src.health import OdooMigrationHealthChecker
        from src.config import get_config
        from rich.console import Console
        from rich.panel import Panel

        console = Console()
        console.print(Panel(
            "🔍 Quick Health Check\n"
            "Checking all Odoo migration environment components...",
            title="Health Check",
            border_style="cyan"
        ))

        config = get_config()
        checker = OdooMigrationHealthChecker(config, detailed=True, fix=True)
        results = checker.run_health_check()

        # Exit with appropriate code
        health_percentage = (
            checker.health_score / checker.max_score) * 100 if checker.max_score > 0 else 0
        if health_percentage < 80:
            console.print(
                "⚠️ Health check indicates issues. Please resolve before proceeding.", style="bold yellow")
            sys.exit(1)
        else:
            console.print("✅ Environment is healthy and ready!",
                          style="bold green")

    except Exception as e:
        console = Console()
        console.print(f"❌ Health check failed: {e}", style="bold red")
        sys.exit(1)


def check_entry():
    """Entry point for quick check command"""
    health_check_entry()


def create_demo_entry():
    """Entry point for create-demo command"""
    from pathlib import Path
    from src.config import get_config
    from src.module_installer import OdooModuleInstaller

    # Add src to Python path
    project_root = Path(__file__).parent
    src_path = project_root / 'src'
    sys.path.insert(0, str(src_path))

    # Change to script directory
    os.chdir(str(project_root))

    console = Console()
    console.print(Panel(
        "🏗️ Demo Database Creation Tool\n"
        "Create standardized Odoo v15/v16 demo databases for migration testing.",
        title="Demo Database Creation",
        border_style="blue"
    ))

    # Parse command line arguments manually
    args = sys.argv[1:]  # Skip script name

    # Load configuration
    try:
        config = get_config()
        console.print(f"✅ Configuration loaded")
    except Exception as e:
        console.print(f"❌ Failed to load configuration: {e}", style="bold red")
        sys.exit(1)

    # Parse the arguments for create_demo command
    version = 'both'
    force = False
    with_modules = False

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ['-v', '--version'] and i + 1 < len(args):
            version = args[i + 1]
            i += 2
        elif arg in ['-f', '--force']:
            force = True
            i += 1
        elif arg == '--with-modules':
            with_modules = True
            i += 1
        else:
            i += 1

    # Run demo database creation
    try:
        demo_v15_name = "demo_v15"
        demo_v16_name = "demo_v16"

        console.print(Panel.fit(
            f"[bold blue]Create Demo Database Pair[/bold blue]\n\n"
            f"V15 Database: [green]{demo_v15_name}[/green]\n"
            f"V16 Database: [green]{demo_v16_name}[/green]\n"
            f"Force recreate: [cyan]{force}[/cyan]\n"
            f"With modules: [cyan]{with_modules}[/cyan]",
            title="🏗️ Database Pair Creation"
        ))

        installer = OdooModuleInstaller(config)

        databases = []
        if version in ['v15', 'both']:
            databases.append(('v15', demo_v15_name))
        if version in ['v16', 'both']:
            databases.append(('v16', demo_v16_name))

        results = {}
        for db_version, db_name in databases:
            console.print(
                f"\n🏗️ Creating {db_version.upper()} database: {db_name}")
            try:
                result = installer.create_demo_database(
                    db_version, db_name, force_recreate=force)
                results[db_version] = result

                if result.get('status') == 'completed':
                    console.print(
                        f"✅ Successfully created {db_version.upper()} database: {db_name}")

                    if with_modules:
                        console.print(
                            f"📦 Installing demo modules for {db_name}...")
                        module_result = installer.install_demo_modules(
                            db_version, db_name)
                        if module_result.get('success'):
                            console.print(
                                f"✅ Demo modules installed successfully")
                        else:
                            console.print(f"⚠️ Some modules failed to install")
                else:
                    console.print(
                        f"❌ Failed to create {db_version.upper()} database: {result.get('error', 'Unknown error')}")

            except Exception as e:
                console.print(
                    f"❌ Error creating {db_version.upper()} database: {e}")
                results[db_version] = {'status': 'failed', 'error': str(e)}

        # Display results
        _display_demo_creation_results(console, results, databases)

    except Exception as e:
        console.print(f"❌ Demo creation failed: {e}", style="bold red")
        sys.exit(1)


def config_generate_entry():
    """Entry point for config generation script"""
    from pathlib import Path
    from src.config_generator import OdooConfigGenerator
    from src.config import get_config

    # Change to the script directory to find config.json
    script_dir = Path(__file__).parent
    original_cwd = os.getcwd()

    try:
        os.chdir(str(script_dir))

        console = Console()
        console.print(Panel(
            "🔄 Configuration Generator\n"
            "Generate and synchronize Odoo configuration files from config.json",
            title="Config Generator",
            border_style="cyan"
        ))

        # Load configuration
        config = get_config()

        # Create generator and run sync
        generator = OdooConfigGenerator(config)
        generator.sync_all_configs()
        console.print("✅ Configuration generation completed successfully!")

    except Exception as e:
        console = Console()
        console.print(
            f"❌ Configuration generation failed: {e}", style="bold red")
        sys.exit(1)
    finally:
        os.chdir(original_cwd)


def setup_db_entry():
    """Entry point for setup-db command"""
    from pathlib import Path
    from src.config import get_config
    from src.database_setup import DatabaseSetup

    script_dir = Path(__file__).parent
    original_cwd = os.getcwd()

    try:
        os.chdir(str(script_dir))
        console = Console()
        config = get_config()

        console.print(Panel(
            "📦 Database Setup Tool\n"
            "Setup demo databases for both v15 and v16 with full Odoo CE modules and sample data.",
            title="Database Setup",
            border_style="blue"
        ))

        # Parse arguments
        args = sys.argv[1:]
        version = 'both'
        force = False
        modules_only = False

        i = 0
        while i < len(args):
            arg = args[i]
            if arg in ['-v', '--version'] and i + 1 < len(args):
                version = args[i + 1]
                i += 2
            elif arg in ['-f', '--force']:
                force = True
                i += 1
            elif arg == '--modules-only':
                modules_only = True
                i += 1
            else:
                i += 1

        # Run setup
        setup = DatabaseSetup(config)
        result = setup.setup_databases(
            version, force_recreate=force, modules_only=modules_only)
        _display_setup_results(console, result)

    except Exception as e:
        console = Console()
        console.print(f"❌ Database setup failed: {e}", style="bold red")
        sys.exit(1)
    finally:
        os.chdir(original_cwd)


def check_db_entry():
    """Entry point for check-db command"""
    from pathlib import Path
    from src.config import get_config
    from src.database_setup import DatabaseSetup

    script_dir = Path(__file__).parent
    original_cwd = os.getcwd()

    try:
        os.chdir(str(script_dir))
        console = Console()
        config = get_config()

        console.print(Panel.fit(
            "[bold blue]Checking Demo Databases Status[/bold blue]",
            title="🔍 Database Check"
        ))

        setup = DatabaseSetup(config)
        result = setup.check_databases()
        _display_check_results(console, result)

    except Exception as e:
        console = Console()
        console.print(f"❌ Database check failed: {e}", style="bold red")
        sys.exit(1)
    finally:
        os.chdir(original_cwd)


def cleanup_db_entry():
    """Entry point for cleanup-db command"""
    from pathlib import Path
    from src.config import get_config
    from src.database_setup import DatabaseSetup

    script_dir = Path(__file__).parent
    original_cwd = os.getcwd()

    try:
        os.chdir(str(script_dir))
        console = Console()
        config = get_config()

        # Parse arguments
        args = sys.argv[1:]
        version = 'both'
        yes = False

        i = 0
        while i < len(args):
            arg = args[i]
            if arg in ['-v', '--version'] and i + 1 < len(args):
                version = args[i + 1]
                i += 2
            elif arg in ['-y', '--yes']:
                yes = True
                i += 1
            else:
                i += 1

        console.print(Panel(
            f"🧹 Cleanup Demo Databases\n"
            f"Version: {version}",
            title="Database Cleanup",
            border_style="yellow"
        ))

        if not yes:
            confirm = input(
                "Are you sure you want to cleanup databases? (y/N): ")
            if confirm.lower() != 'y':
                console.print("❌ Cleanup cancelled")
                return

        setup = DatabaseSetup(config)
        result = setup.cleanup_databases(version)
        _display_cleanup_results(console, result)

    except Exception as e:
        console = Console()
        console.print(f"❌ Database cleanup failed: {e}", style="bold red")
        sys.exit(1)
    finally:
        os.chdir(original_cwd)


def create_demo_db_entry():
    """Entry point for create-demo-db command"""
    from pathlib import Path
    from src.config import get_config
    from src.module_installer import OdooModuleInstaller

    script_dir = Path(__file__).parent
    original_cwd = os.getcwd()

    try:
        os.chdir(str(script_dir))
        console = Console()
        config = get_config()

        # Parse arguments
        args = sys.argv[1:]
        version = None
        name = None
        force = False

        i = 0
        while i < len(args):
            arg = args[i]
            if arg in ['-v', '--version'] and i + 1 < len(args):
                version = args[i + 1]
                i += 2
            elif arg in ['-n', '--name'] and i + 1 < len(args):
                name = args[i + 1]
                i += 2
            elif arg in ['-f', '--force']:
                force = True
                i += 1
            else:
                i += 1

        if not version:
            console.print(
                "❌ Version is required. Use -v v15 or -v v16", style="bold red")
            sys.exit(1)

        if not name:
            name = f"demo_{version}"

        console.print(Panel.fit(
            f"[bold blue]Create Demo Database[/bold blue]\n\n"
            f"Version: [cyan]Odoo {version}[/cyan]\n"
            f"Database: [green]{name}[/green]\n"
            f"Force recreate: [cyan]{force}[/cyan]",
            title="🏗️ Database Creation"
        ))

        installer = OdooModuleInstaller(config)
        result = installer.create_demo_database(
            version, name, force_recreate=force)

        if result.get('status') == 'completed':
            console.print(
                f"✅ Successfully created {version.upper()} database: {name}")
        else:
            console.print(
                f"❌ Failed to create database: {result.get('error', 'Unknown error')}")
            sys.exit(1)

    except Exception as e:
        console = Console()
        console.print(
            f"❌ Demo database creation failed: {e}", style="bold red")
        sys.exit(1)
    finally:
        os.chdir(original_cwd)


def create_demo_pair_entry():
    """Entry point for create-demo-pair command"""
    from pathlib import Path
    from src.config import get_config
    from src.module_installer import OdooModuleInstaller

    script_dir = Path(__file__).parent
    original_cwd = os.getcwd()

    try:
        os.chdir(str(script_dir))
        console = Console()
        config = get_config()

        # Parse arguments
        args = sys.argv[1:]
        force = False

        i = 0
        while i < len(args):
            arg = args[i]
            if arg in ['-f', '--force']:
                force = True
                i += 1
            else:
                i += 1

        demo_v15_name = "demo_v15"
        demo_v16_name = "demo_v16"

        console.print(Panel.fit(
            f"[bold blue]Create Demo Database Pair[/bold blue]\n\n"
            f"V15 Database: [green]{demo_v15_name}[/green]\n"
            f"V16 Database: [green]{demo_v16_name}[/green]\n"
            f"Force recreate: [cyan]{force}[/cyan]",
            title="🏗️ Database Pair Creation"
        ))

        installer = OdooModuleInstaller(config)
        databases = [('v15', demo_v15_name), ('v16', demo_v16_name)]
        results = {}

        for db_version, db_name in databases:
            console.print(
                f"\n🏗️ Creating {db_version.upper()} database: {db_name}")
            result = installer.create_demo_database(
                db_version, db_name, force_recreate=force)
            results[db_version] = result

            if result.get('status') == 'completed':
                console.print(
                    f"✅ Successfully created {db_version.upper()} database: {db_name}")
            else:
                console.print(
                    f"❌ Failed to create {db_version.upper()} database: {result.get('error', 'Unknown error')}")

        _display_demo_creation_results(console, results, databases)

    except Exception as e:
        console = Console()
        console.print(f"❌ Demo pair creation failed: {e}", style="bold red")
        sys.exit(1)
    finally:
        os.chdir(original_cwd)


def list_demo_db_entry():
    """Entry point for list-demo-db command"""
    from pathlib import Path
    from src.config import get_config
    from src.module_installer import OdooModuleInstaller

    script_dir = Path(__file__).parent
    original_cwd = os.getcwd()

    try:
        os.chdir(str(script_dir))
        console = Console()
        config = get_config()

        console.print(Panel.fit(
            "[bold blue]Demo Databases List[/bold blue]",
            title="📋 Database Listing"
        ))

        installer = OdooModuleInstaller(config)

        # List v15 databases
        console.print("\n📦 Odoo v15 Databases:")
        v15_dbs = installer.list_demo_databases('v15')
        if v15_dbs:
            for db in v15_dbs:
                console.print(f"  • {db}")
        else:
            console.print("  No v15 demo databases found")

        # List v16 databases
        console.print("\n📦 Odoo v16 Databases:")
        v16_dbs = installer.list_demo_databases('v16')
        if v16_dbs:
            for db in v16_dbs:
                console.print(f"  • {db}")
        else:
            console.print("  No v16 demo databases found")

    except Exception as e:
        console = Console()
        console.print(f"❌ Database listing failed: {e}", style="bold red")
        sys.exit(1)
    finally:
        os.chdir(original_cwd)


def delete_demo_db_entry():
    """Entry point for delete-demo-db command"""
    from pathlib import Path
    from src.config import get_config
    from src.module_installer import OdooModuleInstaller

    script_dir = Path(__file__).parent
    original_cwd = os.getcwd()

    try:
        os.chdir(str(script_dir))
        console = Console()
        config = get_config()

        # Parse arguments
        args = sys.argv[1:]
        name = None
        version = None
        delete_all = False
        yes = False

        i = 0
        while i < len(args):
            arg = args[i]
            if arg in ['-n', '--name'] and i + 1 < len(args):
                name = args[i + 1]
                i += 2
            elif arg in ['-v', '--version'] and i + 1 < len(args):
                version = args[i + 1]
                i += 2
            elif arg == '--all':
                delete_all = True
                i += 1
            elif arg in ['-y', '--yes']:
                yes = True
                i += 1
            else:
                i += 1

        if not (name or version or delete_all):
            console.print(
                "❌ Must specify --name, --version, or --all", style="bold red")
            sys.exit(1)

        console.print(Panel(
            "🗑️ Delete Demo Databases\n"
            "Removes demo databases. Use with caution!",
            title="Database Deletion",
            border_style="red"
        ))

        installer = OdooModuleInstaller(config)

        # Determine databases to delete
        databases = []
        if name:
            # Need to determine version for specific name
            if 'v15' in name or version == 'v15':
                databases.append(('v15', name))
            elif 'v16' in name or version == 'v16':
                databases.append(('v16', name))
            else:
                console.print(
                    "❌ Cannot determine version for database. Use --version", style="bold red")
                sys.exit(1)
        elif version:
            # Delete all for specific version
            demo_dbs = installer.list_demo_databases(version)
            for db in demo_dbs:
                databases.append((version, db))
        elif delete_all:
            # Delete all demo databases
            for v in ['v15', 'v16']:
                demo_dbs = installer.list_demo_databases(v)
                for db in demo_dbs:
                    databases.append((v, db))

        if not databases:
            console.print("❌ No databases found to delete",
                          style="bold yellow")
            return

        # Confirmation
        if not yes:
            console.print(f"\nDatabases to delete:")
            for db_version, db_name in databases:
                console.print(f"  • {db_version.upper()}: {db_name}")

            confirm = input(
                "\nAre you sure you want to delete these databases? (y/N): ")
            if confirm.lower() != 'y':
                console.print("❌ Deletion cancelled")
                return

        # Delete databases
        results = {}
        for db_version, db_name in databases:
            console.print(
                f"🗑️ Deleting {db_version.upper()} database: {db_name}")
            try:
                success = installer.delete_database(db_version, db_name)
                results[f"{db_version}_{db_name}"] = {'deleted': success}
                if success:
                    console.print(
                        f"✅ Deleted {db_version.upper()} database: {db_name}")
                else:
                    console.print(
                        f"❌ Failed to delete {db_version.upper()} database: {db_name}")
            except Exception as e:
                results[f"{db_version}_{db_name}"] = {
                    'deleted': False, 'error': str(e)}
                console.print(
                    f"❌ Error deleting {db_version.upper()} database {db_name}: {e}")

    except Exception as e:
        console = Console()
        console.print(
            f"❌ Demo database deletion failed: {e}", style="bold red")
        sys.exit(1)
    finally:
        os.chdir(original_cwd)


def analyze_db_entry():
    """Entry point for analyze-db command"""
    from pathlib import Path
    from src.config import get_config

    script_dir = Path(__file__).parent
    original_cwd = os.getcwd()

    try:
        os.chdir(str(script_dir))
        console = Console()
        config = get_config()

        console.print(Panel(
            "📊 Database Analysis\n"
            "Compares database schemas between v15 and v16 to identify migration requirements.",
            title="Database Analysis",
            border_style="cyan"
        ))

        console.print("🚧 Database analysis - Coming soon!",
                      style="bold yellow")
        console.print("This will analyze and compare database structures.")

    except Exception as e:
        console = Console()
        console.print(f"❌ Database analysis failed: {e}", style="bold red")
        sys.exit(1)
    finally:
        os.chdir(original_cwd)


def plan_migration_entry():
    """Entry point for plan-migration command"""
    from pathlib import Path
    from src.config import get_config

    script_dir = Path(__file__).parent
    original_cwd = os.getcwd()

    try:
        os.chdir(str(script_dir))
        console = Console()
        config = get_config()

        console.print(Panel(
            "📋 Migration Planning\n"
            "Creates a detailed migration blueprint based on database analysis.",
            title="Migration Planning",
            border_style="cyan"
        ))

        console.print("🚧 Migration planning - Coming soon!",
                      style="bold yellow")
        console.print("This will generate a detailed migration plan.")

    except Exception as e:
        console = Console()
        console.print(f"❌ Migration planning failed: {e}", style="bold red")
        sys.exit(1)
    finally:
        os.chdir(original_cwd)


def validate_entry():
    """Entry point for validate command"""
    from pathlib import Path
    from src.config import get_config

    script_dir = Path(__file__).parent
    original_cwd = os.getcwd()

    try:
        os.chdir(str(script_dir))
        console = Console()
        config = get_config()

        console.print(Panel(
            "✅ Migration Validation\n"
            "Verifies that migration completed successfully and data integrity is maintained.",
            title="Migration Validation",
            border_style="green"
        ))

        console.print("🚧 Migration validation - Coming soon!",
                      style="bold yellow")
        console.print("This will validate the migration results.")

    except Exception as e:
        console = Console()
        console.print(f"❌ Migration validation failed: {e}", style="bold red")
        sys.exit(1)
    finally:
        os.chdir(original_cwd)


def status_entry():
    """Entry point for status command"""
    from pathlib import Path
    from src.config import get_config
    from src.health import OdooMigrationHealthChecker

    script_dir = Path(__file__).parent
    original_cwd = os.getcwd()

    try:
        os.chdir(str(script_dir))
        console = Console()
        config = get_config()

        console.print(Panel(
            f"Project: {config['project']['name']}\n"
            f"Version: {config['project']['version']}\n"
            f"Workspace: {config.get('workspace_path', '../../')}\n"
            f"Network: {config['environment']['docker_network']}",
            title="📊 Migration Status",
            border_style="blue"
        ))

        # Quick health check
        console.print("\n🔍 Quick Health Check:")
        try:
            health_checker = OdooMigrationHealthChecker(config)
            health_results = health_checker.check_all_services()

            for service, status in health_results.items():
                if status.get('healthy', False):
                    console.print(f"  ✅ {service}: OK")
                else:
                    console.print(
                        f"  ❌ {service}: {status.get('error', 'Failed')}")
        except Exception as e:
            console.print(f"  ❌ Health check failed: {e}")

    except Exception as e:
        console = Console()
        console.print(f"❌ Status check failed: {e}", style="bold red")
        sys.exit(1)
    finally:
        os.chdir(original_cwd)


def info_entry():
    """Entry point for info command"""
    from pathlib import Path
    from src.config import get_config

    script_dir = Path(__file__).parent
    original_cwd = os.getcwd()

    try:
        os.chdir(str(script_dir))
        console = Console()
        config = get_config()

        # Project info
        console.print(Panel(
            f"Name: {config['project']['name']}\n"
            f"Version: {config['project']['version']}\n"
            f"Workspace: {config.get('workspace_path', '../../')}",
            title="📦 Project Information",
            border_style="blue"
        ))

        # Service URLs
        console.print(Panel(
            f"Odoo v15: {config['odoo_v15']['web_url']}\n"
            f"Odoo v16: {config['odoo_v16']['web_url']}\n"
            f"PostgreSQL: {config['postgresql']['host']}:{config['postgresql']['port']}",
            title="🌐 Service URLs",
            border_style="green"
        ))

        # Migration phases
        phases_text = "\n".join(
            [f"  {i + 1}. {phase}" for i, phase in enumerate(config['migration']['migration_phases'])])
        console.print(Panel(
            phases_text,
            title="📋 Migration Phases",
            border_style="yellow"
        ))

    except Exception as e:
        console = Console()
        console.print(f"❌ Info display failed: {e}", style="bold red")
        sys.exit(1)
    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    cli()
