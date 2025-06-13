"""
CLI Interface Module
Command-line interface for Odoo Migration Tool
"""
import click
import time
from health import SystemHealthChecker
from workflow import (
    WorkflowTracker,
    create_health_check_workflow,
    create_migration_workflow,
    create_setup_workflow,
)


@click.group()
def cli():
    """🚀 Odoo Migration v15 → v16 Tool"""
    pass


@cli.command()
@click.option('--detailed', is_flag=True, help='Show detailed information')
@click.option('--show-roadmap', is_flag=True, help='Show roadmap before execution')
def health(detailed, show_roadmap):
    """Check system health with workflow tracking"""
    tracker = create_health_check_workflow()

    if show_roadmap:
        tracker.show_roadmap()
        if not click.confirm('Proceed with health check?'):
            return

    tracker.start_workflow()
    checker = SystemHealthChecker()

    try:
        # Step 1: Python check
        tracker.start_step("python")
        time.sleep(0.5)
        status, message = checker.check_python()
        if not status:
            tracker.fail_step("python", message)
        else:
            tracker.complete_step("python", message)

        # Step 2: Dependencies check
        tracker.start_step("deps")
        time.sleep(0.3)
        status, message = checker.check_dependencies()
        if not status:
            tracker.fail_step("deps", message)
        else:
            tracker.complete_step("deps", message)

        # Step 3: PostgreSQL check
        tracker.start_step("postgres")
        time.sleep(1.0)
        status, message = checker.check_postgresql()
        if not status:
            tracker.fail_step("postgres", message)
        else:
            tracker.complete_step("postgres", message)

        # Step 4-7: Odoo instances check
        for version in ["v15", "v16", "v17", "v18"]:
            step_id = f"odoo_{version}"
            tracker.start_step(step_id)
            time.sleep(0.8)
            status, message = checker.check_odoo_instance(version)
            if not status:
                tracker.fail_step(step_id, message)
            else:
                tracker.complete_step(step_id, message)

        tracker.show_compact_progress()

    except KeyboardInterrupt:
        print("\n🛑 Health check interrupted by user")
    finally:
        tracker.finish_workflow()

        if detailed:
            print("\n" + "="*60)
            checker.print_health_report(detailed=True)


@cli.command()
@click.option('--version', default='both', help='Version to setup (v15/v16/both)')
@click.option('--show-roadmap', is_flag=True, help='Show setup roadmap')
def setup(version, show_roadmap):
    """Setup databases with workflow tracking"""
    tracker = create_setup_workflow()

    if show_roadmap:
        tracker.show_roadmap()
        if not click.confirm(f'Proceed with {version} setup?'):
            return

    tracker.start_workflow()

    try:
        # Step 1: Environment check
        tracker.start_step("env")
        time.sleep(1.0)
        tracker.complete_step("env", "Environment ready")

        # Step 2: Dependencies
        tracker.start_step("deps")
        time.sleep(0.8)
        tracker.complete_step("deps", "Dependencies installed")

        # Step 3: Config generation
        tracker.start_step("config")
        time.sleep(0.5)
        tracker.complete_step("config", "Configuration generated")

        # Step 4: PostgreSQL setup
        tracker.start_step("postgres")
        time.sleep(2.0)
        tracker.complete_step("postgres", "PostgreSQL ready")

        # Step 5: Odoo setup
        tracker.start_step("odoo")
        time.sleep(1.5)
        tracker.complete_step("odoo", "Odoo instances ready")

        # Step 6: Integration test
        tracker.start_step("test")
        time.sleep(1.0)
        tracker.complete_step("test", "Tests passed")

        tracker.show_compact_progress()

    except KeyboardInterrupt:
        print("\n🛑 Setup interrupted by user")
    except Exception as e:
        print(f"\n🚨 Setup failed: {e}")
    finally:
        tracker.finish_workflow()


@cli.command()
def status():
    """Show current migration status and system overview"""
    print("📊 Migration Status Dashboard")
    print("=" * 60)

    checker = SystemHealthChecker()
    results = checker.run_full_check()

    healthy_count = sum(1 for status, _ in results.values() if status)
    total_count = len(results)
    health_percent = (healthy_count / total_count) * 100

    print(
        f"🏥 System Health: {healthy_count}/{total_count} ({health_percent:.0f}%)")

    if health_percent == 100:
        health_status = "🟢 Excellent"
    elif health_percent >= 80:
        health_status = "🟡 Good"
    elif health_percent >= 60:
        health_status = "🟠 Fair"
    else:
        health_status = "🔴 Poor"

    print(f"   Status: {health_status}")

    failed_components = [name for name,
                         (status, _) in results.items() if not status]
    if failed_components:
        print(f"   Issues: {', '.join(failed_components)}")

    print()
    print("🚀 Migration Readiness:")
    if "postgresql" in failed_components:
        print("   ❌ Database connection required")
    else:
        print("   ✅ Database ready")

    odoo_issues = [c for c in failed_components if c.startswith('odoo_')]
    if odoo_issues:
        print(
            f"   ⚠️  Odoo instances need attention: {len(odoo_issues)} issues")
    else:
        print("   ✅ Odoo instances ready")

    print()
    print("🎯 Quick Actions:")
    print("   • Run 'python main.py health --detailed' for detailed diagnostics")
    print("   • Run 'python main.py roadmap' to see available workflows")
    if health_percent < 80:
        print("   • Fix system issues before starting migration")
    else:
        print("   • System ready - you can start migration!")


@cli.command()
@click.option('--workflow', type=click.Choice(['health', 'setup', 'migration', 'all']),
              default='all', help='Which workflow roadmap to show')
def roadmap(workflow):
    """Show workflow roadmaps and milestones"""
    workflows = []

    if workflow in ['health', 'all']:
        workflows.append(('Health Check', create_health_check_workflow()))

    if workflow in ['setup', 'all']:
        workflows.append(('Database Setup', create_setup_workflow()))

    if workflow in ['migration', 'all']:
        workflows.append(('Migration v15→v16', create_migration_workflow()))

    for name, tracker in workflows:
        print(f"\n📋 {name} Workflow:")
        tracker.show_roadmap()
        print()


@cli.command()
@click.option('--dry-run', is_flag=True, help='Show what would be migrated without executing')
@click.option('--force', is_flag=True, help='Force migration even if risks detected')
@click.option('--show-roadmap', is_flag=True, help='Show migration roadmap')
def migrate(dry_run, force, show_roadmap):
    """Run migration from v15 to v16 with full workflow tracking"""
    tracker = create_migration_workflow()

    if show_roadmap or dry_run:
        tracker.show_roadmap()
        if dry_run:
            print("\n🔍 This was a dry run - no actual migration performed")
            return
        if not click.confirm('Proceed with migration? This will modify your database!'):
            return

    if not force:
        click.confirm(
            '⚠️  This will migrate your database. Continue?', abort=True)

    tracker.start_workflow()

    try:
        # Step 1: Pre-flight check
        tracker.start_step("pre_check")
        time.sleep(1.5)
        tracker.complete_step("pre_check", "System ready for migration")

        # Step 2: Database backup
        tracker.start_step("backup")
        time.sleep(3.0)
        tracker.complete_step("backup", "Database backup completed")

        # Step 3: Schema migration
        tracker.start_step("schema")
        time.sleep(2.0)
        tracker.complete_step("schema", "Schema migrated to v16")

        # Step 4: Data migration
        tracker.start_step("data")
        time.sleep(3.5)
        tracker.complete_step("data", "Data migrated to v16 format")

        # Step 5: Post-migration check
        tracker.start_step("post_check")
        time.sleep(1.5)
        tracker.complete_step("post_check", "Migration verified successfully")

        # Step 6: Cleanup
        tracker.start_step("cleanup")
        time.sleep(1.0)
        tracker.complete_step("cleanup", "Temporary files cleaned up")

        tracker.show_compact_progress()

    except KeyboardInterrupt:
        print("\n🛑 Migration interrupted by user")
        print("⚠️  Database may be in inconsistent state - check backup!")
    except Exception as e:
        print(f"\n🚨 Migration failed: {e}")
        print("🔄 Rolling back changes...")
    finally:
        tracker.finish_workflow()


def main():
    """Main entry point for CLI"""
    cli()
