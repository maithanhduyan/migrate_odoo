"""
Health Check module for Odoo Migration v15 to v16
Replaces PowerShell health_check.ps1 with Python implementation
"""
import os
import sys
import click
from typing import Dict, Any, List
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import get_config, Config
from src.utils import (
    setup_logging, DockerManager, HealthChecker, PortChecker, 
    ReportGenerator, ensure_directory, get_timestamp
)


class OdooMigrationHealthChecker:
    """Main health checker class for Odoo Migration"""
    
    def __init__(self, config: Config, detailed: bool = False, fix: bool = False):
        self.config = config
        self.detailed = detailed
        self.fix = fix
        self.console = Console()
        
        # Setup logging
        log_dir = Path("log")
        ensure_directory(str(log_dir))
        log_file = log_dir / f"health_check_{get_timestamp()}.log"
        
        self.logger = setup_logging(
            log_level=config.environment.log_level,
            log_file=str(log_file)
        )
        
        # Initialize managers
        try:
            self.docker = DockerManager()
            self.health_checker = HealthChecker(self.docker, self.logger)
            self.report_generator = ReportGenerator(self.console)
        except Exception as e:
            self.logger.error(f"Failed to initialize managers: {e}")
            sys.exit(1)
        
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
                self.logger.error(f"❌ Docker Compose: {results['docker_compose']['details']}")
        except Exception as e:
            results['docker_compose']['details'] = f"Error: {e}"
            self.logger.error(f"❌ Docker Compose: {results['docker_compose']['details']}")
        
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
                    self.logger.info(f"✅ Network '{network_name}' created successfully")
        
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
                    logs = self.docker.get_container_logs(container_name, tail=3)
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
            self.logger.info(f"✅ PostgreSQL: {results['postgresql_ready']['details']}")
        else:
            self.logger.error(f"❌ PostgreSQL: {results['postgresql_ready']['details']}")
        
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
                db_connected = self.health_checker.check_database_connection(container_name, db_config)
                
                results[service_name] = {
                    'status': db_connected,
                    'details': 'Database connection successful' if db_connected else 'Database connection failed'
                }
                
                if db_connected:
                    self.health_score += 1
                    self.logger.info(f"✅ {container_name} DB: Connection successful")
                else:
                    self.logger.error(f"❌ {container_name} DB: Connection failed")
            else:
                results[service_name] = {
                    'status': False,
                    'details': 'Container not running'
                }
                self.logger.warning(f"⚠️ {container_name} DB: Container not running")
        
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
            accessible, status_code = self.health_checker.check_web_service(url, timeout)
            
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
            ('odoo_v15_to_pg', self.config.odoo_v15.container_name, self.config.postgresql.container_name),
            ('odoo_v16_to_pg', self.config.odoo_v16.container_name, self.config.postgresql.container_name)
        ]
        
        results = {}
        
        for conn_name, from_container, to_container in connections:
            if self.docker.is_container_running(from_container):
                connected = self.docker.ping_container(from_container, to_container)
                
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
                self.logger.warning(f"⚠️ Network {conn_name}: Source container not running")
        
        return results
    
    def check_ports(self) -> Dict[str, Any]:
        """Check port availability"""
        self.logger.info("Checking port availability...")
        
        required_ports = self.config.migration.required_ports
        port_usage = PortChecker.get_port_usage(required_ports)
        
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
                success, output = run_command("docker-compose up -d", cwd=str(compose_dir))
                
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
        self.report_generator.show_health_score(self.health_score, self.max_score)
        
        # Summary table
        flattened_results = {}
        for category, results in all_results.items():
            for key, value in results.items():
                flattened_results[f"{category}.{key}"] = value
        
        summary_table = self.report_generator.generate_summary_table(flattened_results)
        self.console.print(summary_table)
        
        # Port table
        if 'Port Availability' in all_results:
            port_data = all_results['Port Availability'].get('port_usage', {})
            if 'ports' in port_data:
                port_table = self.report_generator.generate_port_table(port_data['ports'])
                self.console.print(port_table)
        
        # Recommendations
        self.show_recommendations()
        
        self.logger.info(f"Health check completed. Score: {self.health_score}/{self.max_score}")
    
    def show_recommendations(self):
        """Show recommendations based on health check results"""
        recommendations = []
        
        if self.missing_containers:
            recommendations.append("🔧 Start missing containers using docker-compose up -d")
        
        if self.health_score < self.max_score * 0.8:
            recommendations.append("⚠️ Resolve health check issues before proceeding with migration")
        
        if self.health_score >= self.max_score * 0.9:
            recommendations.append("🚀 Environment is ready! Proceed to database setup phase")
        
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
        health_percentage = (checker.health_score / checker.max_score) * 100 if checker.max_score > 0 else 0
        exit_code = 0 if health_percentage >= 80 else 1
        sys.exit(exit_code)
        
    except Exception as e:
        console = Console()
        console.print(f"❌ Health check failed: {e}", style="bold red")
        sys.exit(1)


if __name__ == "__main__":
    main()
