"""
Utilities for Odoo Migration v15 to v16
"""
import os
import logging
import subprocess
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from pathlib import Path
import docker
import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Setup logging configuration"""
    logger = logging.getLogger("odoo_migration")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


class DockerManager:
    """Manager for Docker operations"""
    
    def __init__(self):
        try:
            self.client = docker.from_env()
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Docker: {e}")
    
    def is_container_running(self, container_name: str) -> bool:
        """Check if container is running"""
        try:
            container = self.client.containers.get(container_name)
            return container.status == "running"
        except docker.errors.NotFound:
            return False
        except Exception:
            return False
    
    def get_container_status(self, container_name: str) -> Optional[str]:
        """Get container status"""
        try:
            container = self.client.containers.get(container_name)
            return container.status
        except docker.errors.NotFound:
            return None
        except Exception:
            return None
    
    def get_container_logs(self, container_name: str, tail: int = 10) -> List[str]:
        """Get container logs"""
        try:
            container = self.client.containers.get(container_name)
            logs = container.logs(tail=tail, decode=True)
            return logs.strip().split('\n') if logs else []
        except Exception:
            return []
    
    def get_container_ports(self, container_name: str) -> Dict[str, Any]:
        """Get container port mappings"""
        try:
            container = self.client.containers.get(container_name)
            return container.attrs.get('NetworkSettings', {}).get('Ports', {})
        except Exception:
            return {}
    
    def network_exists(self, network_name: str) -> bool:
        """Check if Docker network exists"""
        try:
            self.client.networks.get(network_name)
            return True
        except docker.errors.NotFound:
            return False
        except Exception:
            return False
    
    def create_network(self, network_name: str) -> bool:
        """Create Docker network"""
        try:
            self.client.networks.create(network_name)
            return True
        except Exception:
            return False
    
    def ping_container(self, from_container: str, to_container: str) -> bool:
        """Test network connectivity between containers"""
        try:
            container = self.client.containers.get(from_container)
            result = container.exec_run(f"ping -c 1 {to_container}")
            return result.exit_code == 0
        except Exception:
            return False


class HealthChecker:
    """Health checker for services"""
    
    def __init__(self, docker_manager: DockerManager, logger: logging.Logger):
        self.docker = docker_manager
        self.logger = logger
    
    def check_web_service(self, url: str, timeout: int = 10) -> Tuple[bool, Optional[int]]:
        """Check if web service is accessible"""
        try:
            response = requests.head(url, timeout=timeout)
            return True, response.status_code
        except requests.exceptions.RequestException:
            return False, None
    
    def check_database_connection(self, container_name: str, db_config: Dict[str, Any]) -> bool:
        """Check database connection from container"""
        try:
            container = self.docker.client.containers.get(container_name)
            cmd = f"psql -h {db_config['host']} -U {db_config['user']} -d {db_config['database']} -c '\\l'"
            result = container.exec_run(cmd, environment={'PGPASSWORD': db_config['password']})
            return result.exit_code == 0
        except Exception:
            return False
    
    def check_postgresql_ready(self, container_name: str, user: str) -> bool:
        """Check if PostgreSQL is ready for connections"""
        try:
            container = self.docker.client.containers.get(container_name)
            result = container.exec_run(f"pg_isready -U {user}")
            return result.exit_code == 0
        except Exception:
            return False


class PortChecker:
    """Port availability checker"""
    
    @staticmethod
    def is_port_in_use(port: int) -> bool:
        """Check if port is in use"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    
    @staticmethod
    def get_port_usage(ports: List[int]) -> Dict[int, bool]:
        """Get usage status for multiple ports"""
        return {port: PortChecker.is_port_in_use(port) for port in ports}


class ReportGenerator:
    """Generate health check reports"""
    
    def __init__(self, console: Console):
        self.console = console
    
    def generate_summary_table(self, results: Dict[str, Any]) -> Table:
        """Generate summary table"""
        table = Table(title="🔍 Environment Health Check Summary")
        table.add_column("Component", style="cyan", no_wrap=True)
        table.add_column("Status", justify="center")
        table.add_column("Details", style="dim")
        
        # Add rows based on results
        for component, data in results.items():
            if isinstance(data, dict) and 'status' in data:
                status_emoji = "✅" if data['status'] else "❌"
                status_text = "OK" if data['status'] else "FAILED"
                details = data.get('details', '')
                
                table.add_row(
                    component,
                    f"{status_emoji} {status_text}",
                    details
                )
        
        return table
    
    def generate_port_table(self, port_usage: Dict[int, bool]) -> Table:
        """Generate port usage table"""
        table = Table(title="🚪 Port Usage")
        table.add_column("Port", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Service", style="dim")
        
        service_map = {
            5432: "PostgreSQL",
            8069: "Odoo v15 Web",
            8016: "Odoo v16 Web", 
            8172: "Odoo v15 Longpolling",
            8272: "Odoo v16 Longpolling"
        }
        
        for port, in_use in port_usage.items():
            status = "🟢 In Use" if in_use else "🔴 Available"
            service = service_map.get(port, "Unknown")
            table.add_row(str(port), status, service)
        
        return table
    
    def show_health_score(self, score: int, max_score: int):
        """Show health score with color coding"""
        percentage = (score / max_score) * 100 if max_score > 0 else 0
        
        if percentage >= 90:
            color = "green"
            status = "EXCELLENT - Ready for migration!"
            emoji = "🟢"
        elif percentage >= 75:
            color = "yellow"
            status = "GOOD - Minor issues to address"
            emoji = "🟡"
        elif percentage >= 50:
            color = "orange3"
            status = "FAIR - Several issues need attention"
            emoji = "🟠"
        else:
            color = "red"
            status = "POOR - Major issues must be resolved"
            emoji = "🔴"
        
        panel = Panel(
            f"{emoji} Health Score: {score}/{max_score} ({percentage:.1f}%)\n"
            f"Status: {status}",
            title="📊 Overall Health",
            border_style=color
        )
        
        self.console.print(panel)


def run_command(command: str, cwd: Optional[str] = None, capture_output: bool = True) -> Tuple[bool, str]:
    """Run shell command and return success status and output"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            encoding='utf-8'
        )
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)


def ensure_directory(path: str):
    """Ensure directory exists"""
    Path(path).mkdir(parents=True, exist_ok=True)


def get_timestamp() -> str:
    """Get current timestamp string"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")
