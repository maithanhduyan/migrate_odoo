"""
Odoo Configuration Generator
Generates optimized odoo.conf files from config.json settings
Supports full synchronization and automatic backup
"""
from .utils import setup_logging
from .config import get_config
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import shutil
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.dirname(__file__))


class OdooConfigGenerator:
    """Generator for Odoo configuration files with full synchronization support"""

    def __init__(self, config):
        self.config = config
        self.console = Console()
        self.logger = setup_logging(config['environment']['log_level'])
        self.workspace_root = Path(config.get('workspace_path', '../../'))

    def _format_config_value(self, value) -> str:
        """Format config value based on its type"""
        if isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, dict):
            return "{}"
        elif isinstance(value, list):
            return ",".join(str(item) for item in value)
        elif value is None or value == "":
            return ""
        else:
            return str(value)

    def _generate_config_section(self, config_dict: Dict[str, Any], service_name: str) -> str:
        """Generate configuration section from config dictionary"""
        lines = []
        lines.append(f"# ========================================")
        lines.append(f"# {service_name} Configuration (Auto-generated)")
        lines.append(
            f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"# Synchronized from config.json")
        lines.append(f"# ========================================")
        lines.append("")

        # Group configurations by category for better organization
        sections = {
            "Addons": ["addons_path"],
            "Database": ["db_host", "db_port", "db_user", "db_password", "db_name", "db_maxconn", "db_sslmode", "db_template"],
            "Server": ["http_enable", "http_interface", "http_port", "longpolling_port", "proxy_mode"],
            "Admin Security": ["admin_passwd"],
            "Performance": ["workers", "max_cron_threads", "limit_memory_hard", "limit_memory_soft", "limit_request", "limit_time_cpu", "limit_time_real", "limit_time_real_cron"],
            "Logging": ["log_level", "log_handler", "logfile", "log_db", "log_db_level"],
            "Data": ["data_dir", "csv_internal_sep"],
            "Database Management": ["list_db", "dbfilter"],
            "Security": ["session_cookie_secure", "session_cookie_httponly"],
            "Modules": ["server_wide_modules"],
            "Email": ["email_from", "from_filter", "smtp_server", "smtp_port", "smtp_ssl", "smtp_password", "smtp_user", "smtp_ssl_certificate_filename", "smtp_ssl_private_key_filename"],
            "Testing": ["test_enable", "test_file", "test_tags", "screenshots"],
            "Miscellaneous": ["demo", "import_partial", "osv_memory_age_limit", "osv_memory_count_limit", "reportgz", "screencasts", "syslog", "transient_age_limit", "translate_modules", "unaccent", "upgrade_path", "without_demo", "geoip_database", "pg_path", "pidfile"]
        }

        for section_name, section_keys in sections.items():
            section_content = []

            for key in section_keys:
                if key in config_dict:
                    value = self._format_config_value(config_dict[key])
                    section_content.append(f"{key} = {value}")

            if section_content:
                lines.append(f"# {section_name} Configuration")
                lines.extend(section_content)
                lines.append("")

        return "\n".join(lines)

    def generate_odoo_v15_config(self) -> str:
        """Generate optimized Odoo v15 configuration from config.json"""
        v15_config = self.config['odoo_v15']['config'].copy()
        db_config = self.config['postgresql']

        # Use db_host from odoo config if available, otherwise use postgresql for Docker
        db_host = v15_config.get('db_host', 'postgresql')
        if db_host == 'localhost':
            db_host = 'postgresql'  # Container hostname for Docker environment

        # Merge database configuration
        merged_config = {
            **v15_config,
            'db_host': db_host,
            'db_port': db_config['port'],
            'db_user': db_config['user'],
            'db_password': db_config['password'],
            'db_maxconn': 64,
            'db_template': 'template0'
        }

        config_content = "[options]\n"
        config_content += self._generate_config_section(
            merged_config, "Odoo v15")

        return config_content.strip()

    def generate_odoo_v16_config(self) -> str:
        """Generate optimized Odoo v16 configuration from config.json"""
        v16_config = self.config['odoo_v16']['config'].copy()
        db_config = self.config['postgresql']

        # Use db_host from odoo config if available, otherwise use postgresql for Docker
        db_host = v16_config.get('db_host', 'postgresql')
        if db_host == 'localhost':
            db_host = 'postgresql'  # Container hostname for Docker environment

        # Merge database configuration
        merged_config = {
            **v16_config,
            'db_host': db_host,
            'db_port': db_config['port'],
            'db_user': db_config['user'],
            'db_password': db_config['password'],
            'db_maxconn': 64,
            'db_template': 'template0'
        }

        config_content = "[options]\n"
        config_content += self._generate_config_section(
            merged_config, "Odoo v16")

        return config_content.strip()

    def get_config_path(self, service: str) -> Path:
        """Get configuration file path for service"""
        if service == 'odoo_v15':
            return self.workspace_root / self.config['odoo_v15']['config_path']
        elif service == 'odoo_v16':
            return self.workspace_root / self.config['odoo_v16']['config_path']
        else:
            raise ValueError(f"Unknown service: {service}")

    def backup_existing_config(self, config_path: Path) -> Optional[Path]:
        """Backup existing configuration file with timestamp"""
        if config_path.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = config_path.with_suffix(f'.conf.backup_{timestamp}')

            try:
                shutil.copy2(config_path, backup_path)
                self.logger.info(
                    f"Backed up existing config to: {backup_path}")
                self.console.print(
                    f"📂 Backup created: {backup_path.name}", style="dim blue")
                return backup_path
            except Exception as e:
                self.logger.error(f"Failed to backup config: {e}")
                self.console.print(f"⚠️ Failed to backup: {e}", style="yellow")
                return None
        return None

    def write_config_file(self, config_content: str, config_path: Path, service_name: str):
        """Write configuration content to file with proper formatting"""
        try:
            # Ensure directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)

            # Backup existing file
            backup_path = self.backup_existing_config(config_path)

            # Write new configuration
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(config_content)

            # Set file permissions (if on Unix-like system)
            try:
                config_path.chmod(0o644)
            except:
                pass  # Windows doesn't support chmod

            self.console.print(
                f"✅ Generated {service_name} config: {config_path}", style="green")
            self.logger.info(
                f"Generated {service_name} configuration at {config_path}")

            # Show file size
            file_size = config_path.stat().st_size
            self.console.print(f"   📊 Size: {file_size} bytes", style="dim")

        except Exception as e:
            self.console.print(
                f"❌ Failed to write {service_name} config: {e}", style="red")
            self.logger.error(f"Failed to write {service_name} config: {e}")
            raise

    def sync_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """Synchronize all Odoo configuration files from config.json"""
        self.console.print(Panel(
            "[bold blue]🔄 Synchronizing Odoo configurations from config.json[/bold blue]\n\n"
            "This will generate fresh odoo.conf files based on your config.json settings.\n"
            "Existing configurations will be backed up automatically.",
            title="Configuration Synchronization",
            border_style="cyan"
        ))

        results = {
            'v15': {'status': 'pending', 'path': None, 'backup': None, 'error': None},
            'v16': {'status': 'pending', 'path': None, 'backup': None, 'error': None}
        }

        # Generate Odoo v15 config
        try:
            self.console.print("\n🚀 Generating Odoo v15 configuration...")
            v15_content = self.generate_odoo_v15_config()
            v15_path = self.get_config_path('odoo_v15')
            results['v15']['path'] = v15_path

            backup_path = self.backup_existing_config(v15_path)
            results['v15']['backup'] = backup_path

            self.write_config_file(v15_content, v15_path, "Odoo v15")
            results['v15']['status'] = 'success'

        except Exception as e:
            results['v15']['status'] = 'failed'
            results['v15']['error'] = str(e)
            self.console.print(
                f"❌ Failed to generate v15 config: {e}", style="red")

        # Generate Odoo v16 config
        try:
            self.console.print("\n🚀 Generating Odoo v16 configuration...")
            v16_content = self.generate_odoo_v16_config()
            v16_path = self.get_config_path('odoo_v16')
            results['v16']['path'] = v16_path

            backup_path = self.backup_existing_config(v16_path)
            results['v16']['backup'] = backup_path

            self.write_config_file(v16_content, v16_path, "Odoo v16")
            results['v16']['status'] = 'success'

        except Exception as e:
            results['v16']['status'] = 'failed'
            results['v16']['error'] = str(e)
            self.console.print(
                f"❌ Failed to generate v16 config: {e}", style="red")

        # Show summary
        self.show_sync_summary(results)
        return results

    def show_sync_summary(self, results: Dict[str, Dict]):
        """Show synchronization summary"""
        # Create summary table
        table = Table(title="🔄 Synchronization Summary")
        table.add_column("Version", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Config Path", style="blue")
        table.add_column("Backup", style="green")
        table.add_column("Error", style="red")

        for version, result in results.items():
            status_icon = "✅" if result['status'] == 'success' else "❌" if result['status'] == 'failed' else "⏳"
            status_text = f"{status_icon} {result['status'].title()}"

            config_path = str(result['path']) if result['path'] else "N/A"
            backup_info = result['backup'].name if result['backup'] else "No backup needed"
            error_info = result['error'] if result['error'] else ""

            table.add_row(
                f"Odoo {version.upper()}",
                status_text,
                config_path,
                backup_info,
                error_info
            )

        self.console.print(table)

        # Show next steps
        success_count = sum(1 for r in results.values()
                            if r['status'] == 'success')
        if success_count > 0:
            self.console.print("\n💡 Next Steps:", style="bold blue")
            self.console.print(
                "  1. Review generated configurations", style="dim")
            self.console.print(
                "  2. Restart Docker containers to apply changes:", style="dim")
            self.console.print(
                "     docker compose -f odoo_v15/compose.yml restart", style="cyan")
            self.console.print(
                "     docker compose -f odoo_v16/compose.yml restart", style="cyan")
            self.console.print(
                "  3. Test Odoo instances accessibility", style="dim")

    def validate_generated_configs(self):
        """Validate generated configuration files"""
        self.console.print(
            "\n🔍 Validating generated configurations...", style="cyan")

        configs_to_check = [
            ("Odoo v15", self.get_config_path('odoo_v15')),
            ("Odoo v16", self.get_config_path('odoo_v16'))
        ]

        validation_results = []

        for name, path in configs_to_check:
            result = {
                'name': name,
                'path': path,
                'exists': False,
                'valid': False,
                'issues': []
            }

            if path.exists():
                result['exists'] = True
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Basic validation
                    required_sections = ['[options]']
                    required_keys = ['db_host', 'db_user',
                                     'addons_path', 'data_dir', 'http_port']

                    for section in required_sections:
                        if section not in content:
                            result['issues'].append(
                                f"Missing section: {section}")

                    for key in required_keys:
                        if f"{key} =" not in content:
                            result['issues'].append(f"Missing key: {key}")

                    # Check for empty values that shouldn't be empty
                    critical_keys = ['db_host', 'db_user',
                                     'addons_path', 'data_dir']
                    for key in critical_keys:
                        if f"{key} = \n" in content or f"{key} =\n" in content:
                            result['issues'].append(
                                f"Empty critical value: {key}")

                    result['valid'] = len(result['issues']) == 0

                except Exception as e:
                    result['issues'].append(f"File read error: {e}")

            else:
                result['issues'].append("File does not exist")

            validation_results.append(result)

        # Display validation results
        validation_table = Table(title="🔍 Validation Results")
        validation_table.add_column("Service", style="cyan")
        validation_table.add_column("File Exists", style="bold")
        validation_table.add_column("Valid", style="bold")
        validation_table.add_column("Issues", style="red")

        for result in validation_results:
            exists_icon = "✅" if result['exists'] else "❌"
            valid_icon = "✅" if result['valid'] else "❌"
            issues_text = "; ".join(
                result['issues']) if result['issues'] else "None"

            validation_table.add_row(
                result['name'],
                exists_icon,
                valid_icon,
                issues_text
            )

        self.console.print(validation_table)

        # Summary
        valid_count = sum(1 for r in validation_results if r['valid'])
        total_count = len(validation_results)

        if valid_count == total_count:
            self.console.print(
                f"\n✅ All {total_count} configurations are valid!", style="bold green")
        else:
            self.console.print(
                f"\n⚠️ {valid_count}/{total_count} configurations are valid", style="yellow")

        return validation_results

    def compare_configs(self):
        """Compare generated configurations with current ones"""
        self.console.print("\n🔍 Comparing configurations...", style="cyan")

        # Compare v15 and v16 configurations
        v15_config = self.config['odoo_v15']['config']
        v16_config = self.config['odoo_v16']['config']

        differences = []

        # Compare all keys
        all_keys = set(v15_config.keys()) | set(v16_config.keys())

        for key in sorted(all_keys):
            v15_val = v15_config.get(key, "N/A")
            v16_val = v16_config.get(key, "N/A")

            if v15_val != v16_val:
                differences.append({
                    'key': key,
                    'v15': self._format_config_value(v15_val),
                    'v16': self._format_config_value(v16_val)
                })

        if differences:
            diff_table = Table(
                title="🔍 Configuration Differences (v15 vs v16)")
            diff_table.add_column("Configuration Key", style="cyan")
            diff_table.add_column("Odoo v15", style="green")
            diff_table.add_column("Odoo v16", style="blue")

            for diff in differences:
                diff_table.add_row(diff['key'], diff['v15'], diff['v16'])

            self.console.print(diff_table)
        else:
            self.console.print(
                "✅ No differences found between v15 and v16 configurations", style="green")

    # Alias for backward compatibility
    def generate_all_configs(self):
        """Generate all Odoo configuration files (alias for sync_all_configs)"""
        return self.sync_all_configs()

    def show_config_summary(self):
        """Show configuration generation summary (kept for compatibility)"""
        self.compare_configs()

    def write_config_file(self, config_content: str, config_path: Path, service_name: str):
        """Write configuration content to file"""
        try:
            # Ensure directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)

            # Backup existing file
            self.backup_existing_config(config_path)

            # Write new configuration
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(config_content)

            self.console.print(
                f"✅ Generated {service_name} config: {config_path}", style="green")
            self.logger.info(
                f"Generated {service_name} configuration at {config_path}")

        except Exception as e:
            self.console.print(
                f"❌ Failed to write {service_name} config: {e}", style="red")
            self.logger.error(f"Failed to write {service_name} config: {e}")
            raise

    def show_config_summary(self):
        """Show configuration generation summary"""
        v15_config = self.config['odoo_v15']['config']
        v16_config = self.config['odoo_v16']['config']

        self.console.print("\n📊 Configuration Summary:",
                           style="bold cyan")        # Key differences
        differences = []
        if v15_config['limit_time_real_cron'] != v16_config['limit_time_real_cron']:
            differences.append(
                f"Cron timeout: v15={v15_config['limit_time_real_cron']}, v16={v16_config['limit_time_real_cron']}")

        if 'session_cookie_secure' in v16_config:
            differences.append(
                "v16 includes enhanced security settings (session cookies)")

        if differences:
            self.console.print("🔍 Key differences between v15 and v16:")
            for diff in differences:
                self.console.print(f"  • {diff}", style="yellow")

        self.console.print(
            "\n✅ Configuration files generated successfully!", style="bold green")
        self.console.print(
            "💡 Restart containers to apply new configurations", style="blue")


@click.command()
@click.option('--validate', '-v', is_flag=True, help='Validate generated configurations')
@click.option('--backup', '-b', is_flag=True, default=True, help='Backup existing configs (default: True)')
@click.option('--sync', '-s', is_flag=True, help='Full synchronization mode (recommended)')
def main(validate: bool, backup: bool, sync: bool) -> None:
    """
    🔄 Generate and synchronize Odoo configuration files from config.json

    This command:
    - Reads all settings from config.json
    - Generates clean, optimized odoo.conf files for both v15 and v16
    - Automatically backs up existing configurations with timestamps
    - Validates generated files for correctness
    - Shows configuration differences between versions
    """
    try:
        # Load configuration
        config = get_config()

        # Create generator
        generator = OdooConfigGenerator(config)

        if sync:
            # Full synchronization mode (recommended)
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

    except Exception as e:
        console = Console()
        console.print(
            f"❌ Configuration generation failed: {e}", style="bold red")
        sys.exit(1)


if __name__ == "__main__":
    main()
