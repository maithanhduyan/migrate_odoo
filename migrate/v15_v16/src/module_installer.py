"""
Module Installation Script - Cài đặt modules Odoo qua odoo-bin command
Improved version with proper error handling and container management

@author: Migration Team
@version: 1.0.1
"""

import os
import time
import subprocess
import logging
import requests
from typing import List, Dict, Any
from pathlib import Path

from .utils import setup_logging


class OdooModuleInstaller:
    """Class quản lý cài đặt modules Odoo qua command line"""

    def __init__(self, config):
        self.config = config
        self.logger = setup_logging()

    def install_modules_via_command(self, version: str, database_name: str, modules: List[str]) -> Dict[str, Any]:
        """
        Cài đặt modules qua odoo-bin command trong container

        Args:
            version: 'v15' hoặc 'v16'
            database_name: Tên database
            modules: Danh sách modules cần cài

        Returns:
            Dict chứa kết quả cài đặt        """
        odoo_config = self.config.get(f'odoo_{version}', {})
        container_name = odoo_config.get('container_name', f'odoo_{version}')

        result = {
            'version': version,
            'database': database_name,
            'total_modules': len(modules),
            'installed_modules': [],
            'failed_modules': [],
            'status': 'in_progress'
        }

        self.logger.info(
            f"🔧 Cài đặt {len(modules)} modules cho {version} database {database_name}")

        # Đảm bảo Odoo container đang chạy
        self._ensure_container_running(container_name, version)

        try:
            # Cài đặt modules từng batch
            batch_size = 3  # Giảm batch size để tránh lỗi
            for i in range(0, len(modules), batch_size):
                batch = modules[i:i + batch_size]
                self.logger.info(
                    f"📦 Installing batch {i // batch_size + 1}: {', '.join(batch)}")

                try:
                    self._install_module_batch_command(
                        container_name, database_name, batch, version)
                    result['installed_modules'].extend(batch)
                    self.logger.info(
                        f"✅ Batch {i // batch_size + 1} installed successfully")

                except Exception as e:
                    self.logger.warning(
                        f"⚠️ Batch {i // batch_size + 1} failed: {e}")
                    result['failed_modules'].extend(batch)
                    continue

                # Delay giữa các batch
                time.sleep(3)

            result['status'] = 'completed'
            self.logger.info(
                f"✅ Module installation completed. Success: {len(result['installed_modules'])}, Failed: {len(result['failed_modules'])}")

        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            self.logger.error(f"❌ Module installation failed: {e}")

        return result

    def _install_module_batch_command(
            self,
            container_name: str,
            database_name: str,
            modules: List[str],
            version: str) -> None:
        """Cài đặt một batch modules qua odoo-bin command"""
        modules_str = ','.join(modules)

        # Command để cài đặt modules
        install_cmd = [
            'docker', 'exec', container_name,
            'odoo', '--database', database_name,
            '--init', modules_str,
            '--stop-after-init',
            '--no-http'
        ]

        self.logger.debug(f"Executing: {' '.join(install_cmd)}")

        try:
            # Run command với timeout
            result = subprocess.run(
                install_cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
                cwd=os.path.join(self.config.get('project', {}).get('workspace_root', './'))
            )

            if result.returncode != 0:
                self.logger.warning(f"Command failed: {result.stderr}")
                # Có thể một số modules không tồn tại, không throw error
            else:
                self.logger.debug(f"Command output: {result.stdout}")

        except subprocess.TimeoutExpired:
            raise Exception(
                f"Module installation timeout for batch: {modules}")
        except Exception as e:
            raise Exception(f"Failed to install modules {modules}: {e}")

    def uninstall_modules_via_command(self, version: str, database_name: str, modules: List[str]) -> Dict[str, Any]:
        """
        Gỡ bỏ modules qua odoo-bin command trong container

        Args:
            version: 'v15' hoặc 'v16'
            database_name: Tên database
            modules: Danh sách modules cần gỡ bỏ

        Returns:
            Dict chứa kết quả gỡ bỏ        """
        odoo_config = self.config.get(f'odoo_{version}', {})
        container_name = odoo_config.get('container_name', f'odoo_{version}')

        result = {
            'version': version,
            'database': database_name,
            'total_modules': len(modules),
            'uninstalled_modules': [],
            'failed_modules': [],
            'status': 'in_progress'
        }

        self.logger.info(
            f"🗑️ Gỡ bỏ {len(modules)} modules từ {version} database {database_name}")

        # Đảm bảo Odoo container đang chạy
        self._ensure_container_running(container_name, version)

        try:
            # Gỡ bỏ modules từng cái một
            for module in modules:
                self.logger.info(f"🗑️ Uninstalling module: {module}")

                try:
                    self._uninstall_module_command(
                        container_name, database_name, module, version)
                    result['uninstalled_modules'].append(module)
                    self.logger.info(
                        f"✅ Module {module} uninstalled successfully")

                except Exception as e:
                    self.logger.warning(
                        f"⚠️ Failed to uninstall {module}: {e}")
                    result['failed_modules'].append(module)
                    continue

                # Delay giữa các modules
                time.sleep(2)

            result['status'] = 'completed'
            self.logger.info(
                f"✅ Module uninstallation completed. Success: {len(result['uninstalled_modules'])}, Failed: {len(result['failed_modules'])}")

        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            self.logger.error(f"❌ Module uninstallation failed: {e}")

        return result

    def _uninstall_module_command(
            self,
            container_name: str,
            database_name: str,
            module: str,
            version: str) -> None:
        """Gỡ bỏ một module qua SQL command hoặc Odoo shell"""

        # Method 1: Sử dụng SQL để set state = 'to remove' và chạy -u base
        # Đây là cách an toàn hơn để uninstall modules

        try:
            # Step 1: Set module state to 'to remove' trong database
            sql_cmd = [
                'docker', 'exec', 'postgresql',
                'psql', '-U', 'odoo', '-d', database_name,
                '-c', f"UPDATE ir_module_module SET state='to remove' WHERE name='{module}' AND state='installed';"
            ]

            self.logger.debug(f"Setting module {module} to 'to remove' state")
            result = subprocess.run(
                sql_cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise Exception(f"Failed to set module state: {result.stderr}")

            # Step 2: Run Odoo with -u base to process uninstallation
            update_cmd = [
                'docker', 'exec', container_name,
                'odoo', '--database', database_name,
                '--update', 'base',
                '--stop-after-init',
                '--no-http'
            ]

            self.logger.debug(f"Processing uninstallation for {module}")
            
            result = subprocess.run(
                update_cmd,
                capture_output=True,
                text=True,
                timeout=180,  # 3 minutes timeout
                cwd=os.path.join(self.config.get('project', {}).get('workspace_root', './'))
            )

            if result.returncode != 0:
                self.logger.warning(f"Update command failed: {result.stderr}")
                # Check if module was actually uninstalled
                check_cmd = [
                    'docker', 'exec', 'postgresql',
                    'psql', '-U', 'odoo', '-d', database_name,
                    '-t', '-c', f"SELECT state FROM ir_module_module WHERE name='{module}';"
                ]

                check_result = subprocess.run(
                    check_cmd, capture_output=True, text=True, timeout=10)
                if check_result.returncode == 0:
                    state = check_result.stdout.strip()
                    if state == 'uninstalled':
                        self.logger.info(
                            f"Module {module} successfully uninstalled despite warning")
                        return

                raise Exception(f"Failed to uninstall module {module}")
            else:
                self.logger.debug(f"Uninstall command output: {result.stdout}")

        except subprocess.TimeoutExpired:
            raise Exception(
                f"Module uninstallation timeout for module: {module}")
        except Exception as e:
            raise Exception(f"Failed to uninstall module {module}: {e}")

    def _ensure_container_running(self, container_name: str, version: str) -> None:
        """Đảm bảo container đang chạy"""
        try:
            # Kiểm tra container có đang chạy không
            check_cmd = ['docker', 'inspect', container_name,
                         '--format', '{{.State.Running}}']
            result = subprocess.run(
                check_cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0 and result.stdout.strip() == 'true':
                self.logger.debug(
                    f"Container {container_name} already running")
                return

            # Khởi động container nếu chưa chạy
            self._start_odoo_container(container_name, version)

        except Exception as e:
            self.logger.warning(f"⚠️ Error checking container status: {e}")
            # Try to start anyway
            self._start_odoo_container(container_name, version)

    def _start_odoo_container(self, container_name: str, version: str) -> None:
        """Khởi động Odoo container"""
        try:
            odoo_config = self.config.get(f'odoo_{version}', {})

            # Khởi động container từ docker-compose
            compose_path = os.path.join(
                self.config['project']['workspace_root'], odoo_config.get('docker_compose_path', f'odoo_{version}/compose.yml'))
            cmd = ['docker-compose', '-f', compose_path, 'up', '-d']

            subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            self.logger.info(f"🚀 Started container {container_name}")
            time.sleep(15)  # Đợi container khởi động đầy đủ

        except Exception as e:
            self.logger.warning(
                f"⚠️ Failed to start container {container_name}: {e}")

    def get_available_modules(self, version: str) -> List[str]:
        """Lấy danh sách modules có sẵn trong container"""
        odoo_config = self.config.get(f'odoo_{version}', {})
        container_name = odoo_config.get('container_name', f'odoo_{version}')

        try:
            # Command để list modules
            cmd = [
                'docker', 'exec', container_name,
                'find', '/usr/lib/python3/dist-packages/odoo/addons', '-name', '__manifest__.py',
                '-exec', 'dirname', '{}', ';'
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                # Parse kết quả để lấy tên modules
                modules = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        module_name = os.path.basename(line)
                        modules.append(module_name)

                return sorted(list(set(modules)))
            else:
                self.logger.warning(
                    f"Failed to get modules list: {result.stderr}")
                return []

        except Exception as e:
            self.logger.error(f"Error getting available modules: {e}")
            return []

    def _database_exists_in_postgresql(self, database_name: str) -> bool:
        """Kiểm tra xem database có tồn tại trong PostgreSQL không"""
        try:
            import psycopg2

            # Use localhost instead of container name when connecting from host
            host = 'localhost' if self.config['postgresql']['host'] == 'postgresql' else self.config['postgresql']['host']

            conn = psycopg2.connect(
                host=host,
                port=self.config['postgresql']['port'],
                user=self.config['postgresql']['user'],
                password=self.config['postgresql']['password'],
                database='postgres'
            )

            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (database_name,)
                )
                exists = cursor.fetchone() is not None

            conn.close()
            return exists

        except Exception as e:
            self.logger.error(f"Error checking database existence: {e}")
            return False

    def _delete_database_from_postgresql(self, database_name: str) -> bool:
        """Xóa database khỏi PostgreSQL"""
        try:
            import psycopg2

            # Use localhost instead of container name when connecting from host
            host = 'localhost' if self.config['postgresql']['host'] == 'postgresql' else self.config['postgresql']['host']

            # Terminate all connections to the database
            conn = psycopg2.connect(
                host=host,
                port=self.config['postgresql']['port'],
                user=self.config['postgresql']['user'],
                password=self.config['postgresql']['password'],
                database='postgres'
            )

            conn.autocommit = True

            with conn.cursor() as cursor:
                # Terminate all active connections to the database
                cursor.execute("""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = %s AND pid <> pg_backend_pid()
                """, (database_name,))

                # Drop the database
                cursor.execute(f'DROP DATABASE IF EXISTS "{database_name}"')

            conn.close()
            self.logger.info(
                f"✅ Database {database_name} deleted successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting database {database_name}: {e}")
            return False

    def list_demo_databases(self, version: str) -> List[str]:
        """Liệt kê tất cả demo databases cho version (v15 hoặc v16)"""
        try:
            import psycopg2
            # Use localhost if needed
            host = 'localhost' if self.config['postgresql']['host'] == 'postgresql' else self.config['postgresql']['host']
            conn = psycopg2.connect(
                host=host,
                port=self.config['postgresql']['port'],
                user=self.config['postgresql']['user'],
                password=self.config['postgresql']['password'],
                database='postgres'
            )
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT datname FROM pg_database 
                    WHERE datname NOT IN ('postgres', 'template0', 'template1')
                    AND datname LIKE %s
                    ORDER BY datname
                    """,
                    (f'%demo%{version}%',)
                )
                results = cursor.fetchall()
            conn.close()
            return [row[0] for row in results]
        except Exception as e:
            self.logger.error(
                f"Error listing demo databases for {version}: {e}")
            return []

    def create_demo_database(self, version: str, database_name: str, force_recreate: bool = False) -> dict:
        """Tạo demo database cho version (v15 hoặc v16) với tên chỉ định."""
        import psycopg2
        host = 'localhost' if self.config['postgresql']['host'] == 'postgresql' else self.config['postgresql']['host']
        result = {'status': 'failed', 'error': None}
        try:
            if self._database_exists_in_postgresql(database_name):
                if force_recreate:
                    self.logger.info(
                        f"Force recreate: Xóa database {database_name} trước khi tạo lại.")
                    self._delete_database_from_postgresql(database_name)
                else:
                    self.logger.info(
                        f"Demo database {database_name} đã tồn tại.")
                    result['status'] = 'exists'
                    return result
            conn = psycopg2.connect(
                host=host,
                port=self.config['postgresql']['port'],
                user=self.config['postgresql']['user'],
                password=self.config['postgresql']['password'],
                database='postgres'
            )
            conn.autocommit = True
            with conn.cursor() as cursor:
                cursor.execute(f'CREATE DATABASE "{database_name}"')
            conn.close()
            self.logger.info(f"✅ Đã tạo demo database {database_name}")
            result['status'] = 'completed'
            return result
        except Exception as e:
            self.logger.error(
                f"Error creating demo database {database_name}: {e}")
            result['error'] = str(e)
            return result

    def delete_database(self, version: str, database_name: str) -> bool:
        """Xóa database bất kỳ cho version (v15 hoặc v16)."""
        return self._delete_database_from_postgresql(database_name)

    def create_database_with_demo(self, version: str, database_name: str) -> dict:
        """Tạo database Odoo với demo data và modules cơ bản."""
        result = {'status': 'failed', 'installed_modules': [], 'error': None}
        try:
            # Tạo database qua Odoo command với demo data
            cmd = [
                'docker', 'exec', self.config[f'odoo_{version}']['container_name'],
                'odoo', '--database', database_name,
                '--init', 'base',
                '--without-demo=False',  # Include demo data
                '--stop-after-init',
                '--no-http'
            ]

            self.logger.info(
                f"Creating Odoo database {database_name} with demo data...")
            process_result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300)

            if process_result.returncode == 0:
                result['status'] = 'completed'
                result['installed_modules'] = ['base']
                self.logger.info(
                    f"✅ Database {database_name} created with demo data")
            else:
                result['error'] = f"Command failed: {process_result.stderr}"
                self.logger.error(
                    f"❌ Failed to create database: {result['error']}")

            return result
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(
                f"❌ Error creating database {database_name}: {e}")
            return result
