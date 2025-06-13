"""
Simple Utilities for Odoo Migration v15 to v16
Essential functions only - no complex dependencies
"""
import subprocess
import socket
import logging
import os
import time
from typing import Tuple, Optional, List, Dict, Any
from datetime import datetime


def run_command(command: str, cwd: Optional[str] = None, timeout: int = 30) -> Tuple[bool, str]:
    """
    Run shell command and return success status and output

    Args:
        command: Command to run
        cwd: Working directory  
        timeout: Command timeout in seconds

    Returns:
        Tuple of (success, output)
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8'
        )
        return result.returncode == 0, result.stdout.strip() if result.stdout else result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, f"Command timeout after {timeout}s"
    except Exception as e:
        return False, str(e)


def check_port(port: int, host: str = 'localhost') -> bool:
    """
    Check if port is available/in use

    Args:
        port: Port number to check
        host: Host to check (default: localhost)

    Returns:
        True if port is in use, False if available
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            return result == 0  # 0 means connection successful (port in use)
    except Exception:
        return False


def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    Setup simple logging configuration

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger
    """
    logger = logging.getLogger("odoo_migration")

    # Clear existing handlers
    logger.handlers.clear()

    # Set level
    logger.setLevel(getattr(logging, level.upper()))

    # Create console handler
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def get_timestamp() -> str:
    """Get current timestamp string"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def ensure_directory(path: str) -> None:
    """Ensure directory exists"""
    os.makedirs(path, exist_ok=True)


def check_container_running(container_name: str) -> bool:
    """
    Check if Docker container is running

    Args:
        container_name: Name of container to check

    Returns:
        True if container is running
    """
    success, output = run_command(
        f"docker ps --filter name={container_name} --format table")
    return success and container_name in output


def check_database_connection(db_config) -> bool:
    """
    Simple database connection check using psql command

    Args:
        db_config: Database configuration object

    Returns:
        True if connection successful
    """
    # Try using psql command (simpler than psycopg2 dependency)
    cmd = f"psql -h {db_config.host} -p {db_config.port} -U {db_config.user} -d postgres -c '\\l'"

    # Set password via environment variable
    env = os.environ.copy()
    env['PGPASSWORD'] = db_config.password

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            env=env,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


def wait_for_service(url: str, timeout: int = 60) -> bool:
    """
    Wait for web service to be ready

    Args:
        url: URL to check
        timeout: Maximum wait time in seconds

    Returns:
        True if service becomes ready
    """
    import urllib.request

    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                if response.status == 200:
                    return True
        except Exception:
            pass

        time.sleep(2)

    return False


class DockerManager:
    """Simple Docker container management"""

    def __init__(self):
        self.logger = setup_logging()

    def get_container_status(self, container_name: str) -> Optional[str]:
        """
        Get container status

        Args:
            container_name: Name of container

        Returns:
            Container status string or None if not found
        """
        success, output = run_command(
            f"docker ps -a --filter name=^{container_name}$ --format '{{{{.Status}}}}'"
        )

        if success and output:
            if "Up" in output:
                return "running"
            elif "Exited" in output:
                return "stopped"
            else:
                return output.strip()

        return None

    def start_container(self, container_name: str) -> bool:
        """
        Start container

        Args:
            container_name: Name of container to start

        Returns:
            True if successful
        """
        success, output = run_command(f"docker start {container_name}")
        return success

    def stop_container(self, container_name: str) -> bool:
        """
        Stop container

        Args:
            container_name: Name of container to stop

        Returns:
            True if successful
        """
        success, output = run_command(f"docker stop {container_name}")
        return success


def check_database_exists_mcp(database_name: str) -> bool:
    """
    Check if database exists using MCP PostgreSQL

    Args:
        database_name: Name of database to check

    Returns:
        True if database exists
    """
    try:
        # Get list of databases using external MCP functions
        databases = get_databases_list_mcp()
        return database_name in databases

    except Exception as e:
        # Fallback to basic method if MCP fails
        return check_database_exists_basic(database_name)


def get_databases_list_mcp() -> List[str]:
    """
    Get list of databases using Docker PostgreSQL connection

    Returns:
        List of database names
    """
    try:        # Use Docker to connect to PostgreSQL container
        cmd = 'docker exec postgresql psql -U odoo -d postgres -t -c "SELECT datname FROM pg_database WHERE datistemplate = false;"'

        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            # Parse the output to get database names
            databases = []
            for line in result.stdout.strip().split('\n'):
                db_name = line.strip()
                if db_name and not db_name.startswith('-') and db_name != '':
                    databases.append(db_name)
            return databases
        else:
            # Fallback to basic list
            return ['postgres']

    except Exception as e:
        # Fallback to basic list
        return ['postgres']


def check_database_exists_basic(database_name: str) -> bool:
    """
    Basic database existence check using Docker PostgreSQL

    Args:
        database_name: Name of database to check

    Returns:
        True if database exists
    """
    try:        # Use Docker to check if database exists
        cmd = f'docker exec postgresql psql -U odoo -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname=\'{database_name}\'"'

        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )

        return result.returncode == 0 and '1' in result.stdout.strip()

    except Exception:
        return False


def list_databases_mcp() -> List[str]:
    """
    List all databases using MCP PostgreSQL via subprocess

    Returns:
        List of database names
    """
    try:
        # Call mcp functions directly
        cmd = 'python -c "from pg_mcp.src.server import list_databases; print(list_databases())"'

        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=os.path.join(os.path.dirname(__file__), '..', '..')
        )

        if result.returncode == 0:
            import json
            databases = json.loads(result.stdout.strip())
            return databases

        return []

    except Exception:
        return []


def get_database_size_mcp(database_name: str) -> str:
    """
    Get database size using MCP PostgreSQL via subprocess

    Args:
        database_name: Name of database

    Returns:
        Human readable size string
    """
    try:
        cmd = f'python -c "from pg_mcp.src.server import execute_query; result = execute_query(\'SELECT pg_size_pretty(pg_database_size(\\\\\\\'{database_name}\\\\\\\')) as size\'); print(result)"'

        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=os.path.join(os.path.dirname(__file__), '..', '..')
        )

        if result.returncode == 0:
            import json
            data = json.loads(result.stdout.strip())
            if data.get('rows'):
                return data['rows'][0][0]

        return "Unknown"

    except Exception:
        return "Unknown"


def delete_database_mcp(database_name: str) -> Tuple[bool, str]:
    """
    Delete database using MCP PostgreSQL via subprocess

    Args:
        database_name: Name of database to delete

    Returns:
        Tuple of (success, message)
    """
    try:
        # First terminate connections
        terminate_cmd = f'python -c "from pg_mcp.src.server import execute_query; execute_query(\'SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = \\\\\\\'{database_name}\\\\\\\' AND pid <> pg_backend_pid()\')"'

        subprocess.run(
            terminate_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=os.path.join(os.path.dirname(__file__), '..', '..')
        )

        # Then drop database
        drop_cmd = f'python -c "from pg_mcp.src.server import execute_query; execute_query(\'DROP DATABASE IF EXISTS \\\\\\\"{database_name}\\\\\\\"\')"'

        result = subprocess.run(
            drop_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.path.join(os.path.dirname(__file__), '..', '..')
        )

        if result.returncode == 0:
            return True, f"Database {database_name} deleted successfully"
        else:
            return False, f"Failed to delete database: {result.stderr}"

    except Exception as e:
        return False, f"Failed to delete database {database_name}: {str(e)}"


def validate_database_deletion_mcp(expected_deleted_databases: List[str]) -> Dict[str, Any]:
    """
    Validate database deletion using MCP PostgreSQL

    Args:
        expected_deleted_databases: List of database names that should be deleted

    Returns:
        Dict containing validation results
    """
    logger = setup_logging()

    validation_result = {
        'status': 'success',
        'total_checked': len(expected_deleted_databases),
        'successfully_deleted': 0,
        'still_exists': [],
        'validation_details': {},
        'database_count': 0,
        'existing_databases': []
    }

    try:
        logger.info(
            "🔍 Starting database deletion validation using MCP PostgreSQL...")

        # Get current list of databases using MCP
        current_databases = get_databases_list_mcp()
        validation_result['database_count'] = len(current_databases)
        validation_result['existing_databases'] = current_databases

        logger.info(f"📊 Current databases found: {current_databases}")

        # Check each expected deleted database
        for db_name in expected_deleted_databases:
            if db_name in current_databases:
                validation_result['still_exists'].append(db_name)
                validation_result['validation_details'][db_name] = {
                    'deleted': False,
                    'status': 'ERROR: Still exists',
                    'size': get_database_size_mcp(db_name)
                }
                logger.error(
                    f"❌ Database {db_name} still exists - deletion failed!")
            else:
                validation_result['successfully_deleted'] += 1
                validation_result['validation_details'][db_name] = {
                    'deleted': True,
                    'status': 'Successfully deleted',
                    'size': 'N/A'
                }
                logger.info(f"✅ Database {db_name} confirmed deleted")

        # Determine overall status
        if validation_result['still_exists']:
            validation_result['status'] = 'partial_failure'

        logger.info(
            f"🎯 Validation complete: {validation_result['successfully_deleted']}/{validation_result['total_checked']} databases deleted successfully")

        return validation_result

    except Exception as e:
        logger.error(f"❌ Validation failed: {e}")
        validation_result['status'] = 'error'
        validation_result['error'] = str(e)
        return validation_result


def verify_postgresql_health_mcp() -> Dict[str, Any]:
    """
    Verify PostgreSQL health using MCP PostgreSQL

    Returns:
        Dict containing health check results
    """
    logger = setup_logging()

    health_result = {
        'status': 'healthy',
        'connection': False,
        'database_count': 0,
        'databases': [],
        'total_size': 'Unknown',
        'system_databases': 0,
        'user_databases': 0
    }

    try:
        logger.info("🔍 Checking PostgreSQL health using MCP...")

        # Test connection and get database list
        databases = get_databases_list_mcp()
        health_result['connection'] = len(databases) > 0
        health_result['database_count'] = len(databases)
        health_result['databases'] = databases

        # Categorize databases
        system_dbs = ['postgres', 'template0', 'template1']
        health_result['system_databases'] = len(
            [db for db in databases if db in system_dbs])
        health_result['user_databases'] = len(
            [db for db in databases if db not in system_dbs])

        # Get total size of postgres database as health indicator
        if 'postgres' in databases:
            health_result['total_size'] = get_database_size_mcp('postgres')

        logger.info(
            f"✅ PostgreSQL health check complete: {health_result['database_count']} databases, {health_result['user_databases']} user DBs")

        return health_result

    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        health_result['status'] = 'error'
        health_result['error'] = str(e)
        return health_result
