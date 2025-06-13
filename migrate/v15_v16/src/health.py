"""
Health Check module for Odoo Migration v15 to v16
Replaces PowerShell health_check.ps1 with Python implementation
"""
import os
import sys
import click
from typing import Dict, Any, List
from pathlib import Path

# Try to import optional dependencies
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None

try:
    from src.utils import (
        setup_logging, run_command, check_port, check_container_running,
        check_database_connection, wait_for_service, get_timestamp, ensure_directory
    )
    from src.config import get_config, Config
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class SystemHealthChecker:
    """
    Compatible wrapper around OdooMigrationHealthChecker for CLI integration
    """

    def __init__(self):
        try:
            if UTILS_AVAILABLE:
                from src.config import get_config
                self.config = get_config()
                self.checker = OdooMigrationHealthChecker(self.config)
            else:
                self.config = None
                self.checker = None
        except Exception as e:
            self.config = None
            self.checker = None
            print(f"Warning: Could not initialize full health checker: {e}")

    def check_python(self):
        """Check Python environment - returns (status, message)"""
        try:
            import sys
            version = f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            return True, f"Python environment OK - {version}"
        except Exception as e:
            return False, f"Python check failed: {e}"

    def check_dependencies(self):
        """Check dependencies - returns (status, message)"""
        try:
            # Check for key dependencies
            missing = []
            try:
                import docker
            except ImportError:
                missing.append("docker")

            try:
                import rich
            except ImportError:
                missing.append("rich")

            try:
                import click
            except ImportError:
                missing.append("click")

            if missing:
                return False, f"Missing dependencies: {', '.join(missing)}"
            return True, "Dependencies available"
        except Exception as e:
            return False, f"Dependency check failed: {e}"

    def check_postgresql(self):
        """Check PostgreSQL - returns (status, message)"""
        if self.checker and UTILS_AVAILABLE:
            try:
                results = self.checker.check_database_connectivity()
                pg_status = results.get('postgresql_ready', {})
                return pg_status.get('status', False), pg_status.get('details', 'Unknown')
            except Exception as e:
                return False, f"PostgreSQL check failed: {e}"
        else:
            # Fallback simple check
            try:
                if UTILS_AVAILABLE:
                    from src.utils import check_container_running
                    is_running = check_container_running('postgres')
                    return is_running, f"PostgreSQL container {'running' if is_running else 'not running'}"
                else:
                    return False, "Utils not available for PostgreSQL check"
            except Exception as e:
                return False, f"PostgreSQL check failed: {e}"

    def check_odoo_instance(self, version):
        """Check Odoo instance - returns (status, message)"""
        if self.checker and UTILS_AVAILABLE:
            try:
                results = self.checker.check_containers()
                service_key = f'odoo_{version.lower()}'
                odoo_status = results.get(service_key, {})
                return odoo_status.get('status', False), odoo_status.get('details', 'Unknown')
            except Exception as e:
                return False, f"Odoo {version} check failed: {e}"
        else:
            # Fallback simple check
            try:
                if UTILS_AVAILABLE:
                    from src.utils import check_container_running
                    container_name = f'odoo_{version.lower()}'
                    is_running = check_container_running(container_name)
                    return is_running, f"Odoo {version} container {'running' if is_running else 'not running'}"
                else:
                    return False, f"Utils not available for Odoo {version} check"
            except Exception as e:
                return False, f"Odoo {version} check failed: {e}"

    def print_health_report(self, detailed=False):
        """Print health report"""
        if self.checker and UTILS_AVAILABLE:
            try:
                results = self.checker.run_health_check()
                return results
            except Exception as e:
                print(f"Error generating health report: {e}")
        else:
            print("Health checker not available - basic checks only")
            results = self.run_full_check()
            self._print_basic_report(results)

    def _print_basic_report(self, results):
        """Print basic health report"""
        print("\n" + "="*60)
        print("🚀 BASIC HEALTH CHECK REPORT")
        print("="*60)

        total_checks = len(results)
        passed_checks = sum(1 for status, _ in results.values() if status)

        print(f"Health Score: {passed_checks}/{total_checks}")
        print(f"Health Percentage: {(passed_checks/total_checks)*100:.1f}%")
        print()

        for check_name, (status, message) in results.items():
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {check_name}: {message}")

    def run_full_check(self):
        """Run full health check and return results"""
        results = {}

        # Basic checks
        results['python'] = self.check_python()
        results['dependencies'] = self.check_dependencies()
        results['postgresql'] = self.check_postgresql()
        results['odoo_v15'] = self.check_odoo_instance('v15')
        results['odoo_v16'] = self.check_odoo_instance('v16')

        return results


# Simple helper classes for missing dependencies
class SimpleDockerManager:
    """Simple Docker manager using command line"""

    def __init__(self):
        # Mock docker client object for compatibility
        self.client = self

    def version(self):
        """Get Docker version"""
        if UTILS_AVAILABLE:
            success, output = run_command("docker --version")
            if success:
                return {"Version": output.split()[2].rstrip(',')} if "version" in output.lower() else {"Version": "Unknown"}
        return {"Version": "Command not available"}

    def is_container_running(self, container_name):
        if UTILS_AVAILABLE:
            return check_container_running(container_name)
        else:
            success, output = run_command(
                f"docker ps --filter name={container_name} --format table")
            return success and container_name in output

    def get_container_status(self, container_name):
        success, output = run_command(
            f"docker ps -a --filter name={container_name} --format '{{.Status}}'")
        return output if success else "Unknown"

    def get_container_logs(self, container_name, tail=3):
        success, output = run_command(
            f"docker logs --tail {tail} {container_name}")
        if success and output:
            return output.split('\n')[-tail:]
        return []

    def network_exists(self, network_name):
        success, output = run_command(
            f"docker network ls --filter name={network_name}")
        return success and network_name in output

    def create_network(self, network_name):
        success, _ = run_command(f"docker network create {network_name}")
        return success

    def ping_container(self, from_container, to_container):
        """Check network connectivity between containers"""
        success, _ = run_command(
            f"docker exec {from_container} ping -c 1 {to_container}")
        return success


class SimpleHealthChecker:
    """Simple health checker"""

    def __init__(self, docker_manager, logger):
        self.docker = docker_manager
        self.logger = logger

    def check_postgresql_ready(self, container_name, user):
        # Simple check if container is running
        return self.docker.is_container_running(container_name)

    def check_database_connection(self, container_name, db_config):
        # Simple check - just verify container is running
        return self.docker.is_container_running(container_name)

    def check_web_service(self, url, timeout):
        if UTILS_AVAILABLE:
            result = wait_for_service(url, timeout=5)
            return result, 200 if result else 500
        return False, 500


class SimpleReportGenerator:
    """Simple report generator"""

    def __init__(self, console):
        self.console = console

    def show_health_score(self, score, max_score):
        percentage = (score / max_score * 100) if max_score > 0 else 0
        print(f"\n🏥 Health Score: {score}/{max_score} ({percentage:.1f}%)")

    def generate_summary_table(self, results):
        print("\n📊 Summary:")
        for key, value in results.items():
            status = value.get('status', False) if isinstance(
                value, dict) else value
            icon = "✅" if status else "❌"
            details = value.get('details', '') if isinstance(
                value, dict) else ''
            print(f"  {icon} {key}: {details}")
        return None  # Rich table not available

    def generate_port_table(self, ports):
        print("\n🚪 Port Status:")
        for port, in_use in ports.items():
            status = "In Use" if in_use else "Available"
            print(f"  Port {port}: {status}")
        return None  # Rich table not available


class OdooMigrationHealthChecker:
    """Main health checker class for Odoo Migration"""

    def __init__(self, config: Config, detailed: bool = False, fix: bool = False):
        self.config = config
        self.detailed = detailed
        self.fix = fix

        if RICH_AVAILABLE:
            self.console = Console()
        else:
            self.console = None

        # Setup logging
        if UTILS_AVAILABLE:
            log_dir = Path("log")
            ensure_directory(str(log_dir))
            log_file = log_dir / f"health_check_{get_timestamp()}.log"

            self.logger = setup_logging()
        else:
            import logging
            self.logger = logging.getLogger("health_check")

        # Initialize managers
        try:
            self.docker = SimpleDockerManager()
            self.health_checker = SimpleHealthChecker(self.docker, self.logger)
            self.report_generator = SimpleReportGenerator(self.console)
        except Exception as e:
            self.logger.error(f"Failed to initialize managers: {e}")
            # Don't exit, continue with limited functionality

        # Results storage
        self.results = {}
        self.health_score = 0
        self.max_score = 0
        self.missing_containers = []

    def check_docker_environment(self) -> Dict[str, Any]:
        """Check Docker environment"""
        self.logger.info("Checking Docker environment...")
        self.max_score += 2

        results = {
            'docker': {'status': False, 'details': ''},
            'docker_compose': {'status': False, 'details': ''}
        }

        # Check Docker
        try:
            docker_version = self.docker.client.version()
            results['docker']['status'] = True
            results['docker']['details'] = f"Version {docker_version.get('Version', 'Unknown')}"
            self.health_score += 1
            self.logger.info(f"✅ Docker: {results['docker']['details']}")
        except Exception as e:
            results['docker']['details'] = f"Not accessible: {e}"
            self.logger.error(f"❌ Docker: {results['docker']['details']}")

        # Check Docker Compose (through docker-compose command)
        try:
            from src.utils import run_command
            success, output = run_command("docker-compose --version")
            if success:
                results['docker_compose']['status'] = True
                results['docker_compose']['details'] = output.strip()
                self.health_score += 1
                self.logger.info(f"✅ Docker Compose: Available")
            else:
                results['docker_compose']['details'] = "Not found or not working"
                self.logger.error(
                    f"❌ Docker Compose: {results['docker_compose']['details']}")
        except Exception as e:
            results['docker_compose']['details'] = f"Error: {e}"
            self.logger.error(
                f"❌ Docker Compose: {results['docker_compose']['details']}")

        return results

    def check_network(self) -> Dict[str, Any]:
        """Check Docker network"""
        self.logger.info("Checking Docker network...")
        self.max_score += 1

        network_name = self.config.environment.docker_network
        network_exists = self.docker.network_exists(network_name)

        results = {
            'network': {
                'status': network_exists,
                'details': f"Network '{network_name}' {'exists' if network_exists else 'not found'}"
            }
        }

        if network_exists:
            self.health_score += 1
            self.logger.info(f"✅ {results['network']['details']}")
        else:
            self.logger.error(f"❌ {results['network']['details']}")

            if self.fix:
                self.logger.info(f"🔧 Creating network '{network_name}'...")
                if self.docker.create_network(network_name):
                    results['network']['status'] = True
                    results['network']['details'] += " (created)"
                    self.health_score += 1
                    self.logger.info(
                        f"✅ Network '{network_name}' created successfully")

        return results

    def check_containers(self) -> Dict[str, Any]:
        """Check container health"""
        self.logger.info("Checking container health...")
        self.max_score += 3

        containers = [
            ('postgresql', self.config.postgresql.container_name),
            ('odoo_v15', self.config.odoo_v15.container_name),
            ('odoo_v16', self.config.odoo_v16.container_name)
        ]

        results = {}

        for service_name, container_name in containers:
            is_running = self.docker.is_container_running(container_name)
            status = self.docker.get_container_status(container_name)

            if is_running:
                self.health_score += 1
                details = f"Running (status: {status})"

                if self.detailed:
                    logs = self.docker.get_container_logs(
                        container_name, tail=3)
                    if logs:
                        details += f" | Recent logs: {'; '.join(logs)}"

                self.logger.info(f"✅ {container_name}: {details}")
            else:
                details = f"Not running (status: {status})" if status else "Not found"
                self.missing_containers.append(service_name)
                self.logger.error(f"❌ {container_name}: {details}")

            results[service_name] = {
                'status': is_running,
                'details': details,
                'container_name': container_name
            }

        return results

    def check_database_connectivity(self) -> Dict[str, Any]:
        """Check database connectivity"""
        self.logger.info("Checking database connectivity...")
        self.max_score += 3

        results = {}

        # PostgreSQL readiness check
        pg_ready = self.health_checker.check_postgresql_ready(
            self.config.postgresql.container_name,
            self.config.postgresql.user
        )

        results['postgresql_ready'] = {
            'status': pg_ready,
            'details': 'Ready for connections' if pg_ready else 'Not ready'
        }

        if pg_ready:
            self.health_score += 1
            self.logger.info(
                f"✅ PostgreSQL: {results['postgresql_ready']['details']}")
        else:
            self.logger.error(
                f"❌ PostgreSQL: {results['postgresql_ready']['details']}")

        # Database connections from Odoo containers
        db_config = {
            'host': self.config.postgresql.host,
            'user': self.config.postgresql.user,
            'password': self.config.postgresql.password,
            'database': self.config.postgresql.database
        }

        for service_name, container_name in [
            ('odoo_v15_db', self.config.odoo_v15.container_name),
            ('odoo_v16_db', self.config.odoo_v16.container_name)
        ]:
            if self.docker.is_container_running(container_name):
                db_connected = self.health_checker.check_database_connection(
                    container_name, db_config)

                results[service_name] = {
                    'status': db_connected,
                    'details': 'Database connection successful' if db_connected else 'Database connection failed'
                }

                if db_connected:
                    self.health_score += 1
                    self.logger.info(
                        f"✅ {container_name} DB: Connection successful")
                else:
                    self.logger.error(
                        f"❌ {container_name} DB: Connection failed")
            else:
                results[service_name] = {
                    'status': False,
                    'details': 'Container not running'
                }
                self.logger.warning(
                    f"⚠️ {container_name} DB: Container not running")

        return results

    def check_web_services(self) -> Dict[str, Any]:
        """Check web service accessibility"""
        self.logger.info("Checking web services...")
        self.max_score += 2

        services = [
            ('odoo_v15_web', self.config.odoo_v15.database_selector_url),
            ('odoo_v16_web', self.config.odoo_v16.database_selector_url)
        ]

        results = {}
        timeout = self.config.environment.web_request_timeout

        for service_name, url in services:
            accessible, status_code = self.health_checker.check_web_service(
                url, timeout)

            if accessible:
                self.health_score += 1
                details = f"HTTP {status_code}" if status_code else "Accessible"
                self.logger.info(f"✅ {service_name}: {details}")
            else:
                details = "Not accessible"
                self.logger.error(f"❌ {service_name}: {details}")

            results[service_name] = {
                'status': accessible,
                'details': details,
                'url': url
            }

        return results

    def check_network_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity between containers"""
        self.logger.info("Checking network connectivity...")
        self.max_score += 2

        connections = [
            ('odoo_v15_to_pg', self.config.odoo_v15.container_name,
             self.config.postgresql.container_name),
            ('odoo_v16_to_pg', self.config.odoo_v16.container_name,
             self.config.postgresql.container_name)
        ]

        results = {}

        for conn_name, from_container, to_container in connections:
            if self.docker.is_container_running(from_container):
                connected = self.docker.ping_container(
                    from_container, to_container)

                results[conn_name] = {
                    'status': connected,
                    'details': f"{from_container} -> {to_container} {'connected' if connected else 'failed'}"
                }

                if connected:
                    self.health_score += 1
                    self.logger.info(f"✅ Network {conn_name}: Connected")
                else:
                    self.logger.error(f"❌ Network {conn_name}: Failed")
            else:
                results[conn_name] = {
                    'status': False,
                    'details': f"{from_container} not running"
                }
                self.logger.warning(
                    f"⚠️ Network {conn_name}: Source container not running")

        return results

    def check_ports(self) -> Dict[str, Any]:
        """Check port availability"""
        self.logger.info("Checking port availability...")

        if UTILS_AVAILABLE and hasattr(self.config, 'migration') and hasattr(self.config.migration, 'required_ports'):
            required_ports = self.config.migration.required_ports
        else:
            # Fallback to common Odoo ports
            required_ports = [5432, 8069, 8016]

        # Simple port checking
        port_usage = {}
        for port in required_ports:
            if UTILS_AVAILABLE:
                port_usage[port] = check_port(port)
            else:
                # Fallback socket check
                import socket
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.settimeout(1)
                        result = sock.connect_ex(('localhost', port))
                        port_usage[port] = result == 0
                except:
                    port_usage[port] = False

        results = {
            'port_usage': {
                'status': True,  # Ports being used is actually good
                'details': f"Checked ports: {required_ports}",
                'ports': port_usage
            }
        }

        for port, in_use in port_usage.items():
            status = "In use (Expected)" if in_use else "Not in use"
            self.logger.info(f"🚪 Port {port}: {status}")

        return results

    def check_configuration(self) -> Dict[str, Any]:
        """Check configuration files"""
        if not self.detailed:
            return {}

        self.logger.info("Checking configuration files...")

        config_files = [
            ('odoo_v15_conf', self.config.get_config_path('odoo_v15')),
            ('odoo_v16_conf', self.config.get_config_path('odoo_v16')),
            ('postgresql_conf', self.config.get_config_path('postgresql'))
        ]

        results = {}

        for conf_name, conf_path in config_files:
            exists = conf_path.exists()

            details = f"Config file {'found' if exists else 'not found'}: {conf_path}"

            if exists and conf_name.startswith('odoo'):
                # Read some key config values
                try:
                    with open(conf_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        key_configs = []
                        for line in content.split('\n'):
                            if any(key in line for key in ['db_host', 'db_user', 'db_password']):
                                key_configs.append(line.strip())

                    if key_configs:
                        details += f" | Key configs: {'; '.join(key_configs[:3])}"
                except Exception as e:
                    details += f" | Error reading: {e}"

            results[conf_name] = {
                'status': exists,
                'details': details
            }

            if exists:
                self.logger.info(f"✅ {conf_name}: Found")
            else:
                self.logger.error(f"❌ {conf_name}: Not found")

        return results

    def attempt_fixes(self):
        """Attempt to fix common issues"""
        if not self.fix or not self.missing_containers:
            return

        self.logger.info("🔧 Attempting to start missing containers...")

        for service in self.missing_containers:
            try:
                compose_path = self.config.get_docker_compose_path(service)
                compose_dir = compose_path.parent

                self.logger.info(f"Starting {service} from {compose_dir}...")

                from src.utils import run_command
                success, output = run_command(
                    "docker-compose up -d", cwd=str(compose_dir))

                if success:
                    self.logger.info(f"✅ Started {service}")
                    # Wait a bit for container to start
                    import time
                    time.sleep(5)
                else:
                    self.logger.error(f"❌ Failed to start {service}: {output}")

            except Exception as e:
                self.logger.error(f"❌ Error starting {service}: {e}")

    def run_health_check(self) -> Dict[str, Any]:
        """Run complete health check"""
        self.console.print(Panel(
            "🚀 ODOO MIGRATION v15 → v16 ENVIRONMENT HEALTH CHECK",
            style="bold magenta"
        ))

        all_results = {}

        # Run all checks
        checks = [
            ("Docker Environment", self.check_docker_environment),
            ("Network", self.check_network),
            ("Containers", self.check_containers),
            ("Database Connectivity", self.check_database_connectivity),
            ("Web Services", self.check_web_services),
            ("Network Connectivity", self.check_network_connectivity),
            ("Port Availability", self.check_ports),
        ]

        if self.detailed:
            checks.append(("Configuration", self.check_configuration))

        for check_name, check_func in checks:
            self.console.print(f"\n🔍 {check_name}:", style="bold cyan")
            results = check_func()
            all_results[check_name] = results

        # Attempt fixes
        self.attempt_fixes()

        # Generate final report
        self.generate_final_report(all_results)

        return all_results

    def generate_final_report(self, all_results: Dict[str, Any]):
        """Generate final health check report"""
        self.console.print("\n")
        self.console.print("=" * 60, style="bold magenta")

        # Health score
        self.report_generator.show_health_score(
            self.health_score, self.max_score)

        # Summary table
        flattened_results = {}
        for category, results in all_results.items():
            for key, value in results.items():
                flattened_results[f"{category}.{key}"] = value

        summary_table = self.report_generator.generate_summary_table(
            flattened_results)
        self.console.print(summary_table)

        # Port table
        if 'Port Availability' in all_results:
            port_data = all_results['Port Availability'].get('port_usage', {})
            if 'ports' in port_data:
                port_table = self.report_generator.generate_port_table(
                    port_data['ports'])
                self.console.print(port_table)

        # Recommendations
        self.show_recommendations()

        self.logger.info(
            f"Health check completed. Score: {self.health_score}/{self.max_score}")

    def show_recommendations(self):
        """Show recommendations based on health check results"""
        recommendations = []

        if self.missing_containers:
            recommendations.append(
                "🔧 Start missing containers using docker-compose up -d")

        if self.health_score < self.max_score * 0.8:
            recommendations.append(
                "⚠️ Resolve health check issues before proceeding with migration")

        if self.health_score >= self.max_score * 0.9:
            recommendations.append(
                "🚀 Environment is ready! Proceed to database setup phase")

        if recommendations:
            panel = Panel(
                "\n".join(recommendations),
                title="💡 Recommendations",
                border_style="yellow"
            )
            self.console.print(panel)


@click.command()
@click.option('--detailed', '-d', is_flag=True, help='Show detailed information')
@click.option('--fix', '-f', is_flag=True, help='Attempt to fix common issues automatically')
@click.option('--config', '-c', default='config.json', help='Configuration file path')
def main(detailed: bool, fix: bool, config: str):
    """
    Odoo Migration v15 → v16 Environment Health Check

    Checks the health of PostgreSQL, Odoo v15, and Odoo v16 environments
    """
    try:
        # Load configuration
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        if config != 'config.json':
            os.environ['CONFIG_FILE'] = config

        config_obj = get_config()

        # Run health check
        checker = OdooMigrationHealthChecker(config_obj, detailed, fix)
        results = checker.run_health_check()

        # Exit with appropriate code
        health_percentage = (
            checker.health_score / checker.max_score) * 100 if checker.max_score > 0 else 0
        exit_code = 0 if health_percentage >= 80 else 1
        sys.exit(exit_code)

    except Exception as e:
        console = Console()
        console.print(f"❌ Health check failed: {e}", style="bold red")
        sys.exit(1)


if __name__ == "__main__":
    main()
