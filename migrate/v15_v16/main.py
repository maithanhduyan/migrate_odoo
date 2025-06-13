#!/usr/bin/env python3
"""
Main entry point for Odoo Migration v15 to v16

This script provides a CLI interface for managing the entire migration process
from Odoo v15 to v16, including health checks, database setup, analysis, and migration.
"""
import os
import sys
import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import get_config
from src.health_check import OdooMigrationHealthChecker
from src.config_generator import OdooConfigGenerator


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
@click.pass_context
def setup_db(ctx):
    """
    🗄️ Setup demo databases
    
    Creates demo databases for both Odoo v15 and v16 to test migration process.
    """
    console = Console()
    console.print("🚧 Database setup - Coming soon!", style="bold yellow")
    console.print("This will create demo databases for testing migration.")


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
    phases_text = "\n".join([f"  {i+1}. {phase}" for i, phase in enumerate(config.migration.migration_phases)])
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


if __name__ == '__main__':
    cli()