"""
Module Installation Script - Cài đặt modules Odoo qua odoo-bin command
Simplified approach using Docker exec và odoo-bin command

@author: Migration Team
@version: 1.0.0
"""

import os
import time
import subprocess
import logging
import requests
from typing import List, Dict, Any
from pathlib import Path

from .config import Config
from .utils import setup_logging


class OdooModuleInstaller:
    """Class quản lý cài đặt modules Odoo qua command line"""

    def __init__(self, config: Config):
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
            Dict chứa kết quả cài đặt
        """
        odoo_config = getattr(self.config, f'odoo_{version}')
        container_name = odoo_config.container_name

        result = {
            'version': version,
            'database': database_name,
            'total_modules': len(modules),
            'installed_modules': [],
            'failed_modules': [],
            'status': 'in_progress'
        }

        self.logger.info(f"🔧 Cài đặt {len(modules)} modules cho {version} database {database_name}")

        # Dừng Odoo container trước khi cài đặt modules
        self._stop_odoo_container(container_name)

        try:
            # Cài đặt modules từng batch
            batch_size = 5  # Giảm batch size để tránh lỗi
            for i in range(0, len(modules), batch_size):
                batch = modules[i:i + batch_size]
                self.logger.info(f"📦 Installing batch {i // batch_size + 1}: {', '.join(batch)}")

                try:
                    self._install_module_batch_command(container_name, database_name, batch, version)
                    result['installed_modules'].extend(batch)
                    self.logger.info(f"✅ Batch {i // batch_size + 1} installed successfully")

                except Exception as e:
                    self.logger.warning(f"⚠️ Batch {i // batch_size + 1} failed: {e}")
                    result['failed_modules'].extend(batch)
                    continue

                # Delay giữa các batch
                time.sleep(5)

            result['status'] = 'completed'
            self.logger.info(
                f"✅ Module installation completed. Success: {len(result['installed_modules'])}, Failed: {len(result['failed_modules'])}")

        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            self.logger.error(f"❌ Module installation failed: {e}")

        finally:
            # Khởi động lại Odoo container
            self._start_odoo_container(container_name, version)

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
            '--stop-after-init'
        ]

        self.logger.debug(f"Executing: {' '.join(install_cmd)}")

        try:
            # Run command với timeout
            result = subprocess.run(
                install_cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
                cwd=os.path.join(self.config.project.workspace_root)
            )

            if result.returncode != 0:
                self.logger.warning(f"Command failed: {result.stderr}")
                # Có thể một số modules không tồn tại, không throw error
            else:
                self.logger.debug(f"Command output: {result.stdout}")

        except subprocess.TimeoutExpired:
            raise Exception(f"Module installation timeout for batch: {modules}")
        except Exception as e:
            raise Exception(f"Failed to install modules {modules}: {e}")

    def _stop_odoo_container(self, container_name: str) -> None:
        """Dừng Odoo container"""
        try:
            cmd = ['docker', 'stop', container_name]
            subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            self.logger.info(f"🛑 Stopped container {container_name}")
            time.sleep(5)
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to stop container {container_name}: {e}")

    def _start_odoo_container(self, container_name: str, version: str) -> None:
        """Khởi động Odoo container"""
        try:
            odoo_config = getattr(self.config, f'odoo_{version}')

            # Khởi động container từ docker-compose
            compose_path = os.path.join(self.config.project.workspace_root, odoo_config.docker_compose_path)
            cmd = ['docker-compose', '-f', compose_path, 'up', '-d']

            subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            self.logger.info(f"🚀 Started container {container_name}")
            time.sleep(10)  # Đợi container khởi động

        except Exception as e:
            self.logger.warning(f"⚠️ Failed to start container {container_name}: {e}")

    def get_available_modules(self, version: str) -> List[str]:
        """Lấy danh sách modules có sẵn trong container"""
        odoo_config = getattr(self.config, f'odoo_{version}')
        container_name = odoo_config.container_name

        try:
            # Command để list modules
            cmd = [
                'docker', 'exec', container_name,
                'find', '/usr/lib/python3/dist-packages/odoo/addons', '-name', '__manifest__.py',
                '-exec', 'dirname', '{}', ';'
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                # Parse kết quả để lấy tên modules                modules = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        module_name = os.path.basename(line)
                        modules.append(module_name)
                
                return sorted(list(set(modules)))
            else:
                self.logger.warning(f"Failed to get modules list: {result.stderr}")
                return []

        except Exception as e:
            self.logger.error(f"Error getting available modules: {e}")
            return []

    def create_database_with_demo(self, version: str, database_name: str) -> Dict[str, Any]:
        """Tạo database với demo data qua HTTP API"""
        odoo_config = getattr(self.config, f'odoo_{version}')
        
        result = {
            'version': version,            'database': database_name,
            'status': 'in_progress'
        }

        try:
            # Đảm bảo container đang chạy
            self._start_odoo_container(odoo_config.container_name, version)
            
            # Chờ Odoo web service sẵn sàng
            time.sleep(10)
            
            # Kiểm tra xem database đã tồn tại chưa
            if self._database_exists_in_postgresql(database_name):
                self.logger.info(f"Database {database_name} already exists, skipping creation")
                result['status'] = 'completed'
                return result
            
            # Tạo database qua HTTP API
            create_url = f"{odoo_config.web_url}/web/database/create"
            
            data = {
                'master_pwd': 'admin',  # Master password
                'name': database_name,
                'lang': 'en_US',
                'country_code': 'US',
                'demo': 'True',  # Bật demo data (as string)
                'login': 'admin',
                'password': 'admin',
                'phone': '',
                'confirm_password': 'admin'
            }
            
            self.logger.info(f"🏗️ Creating database {database_name} with demo data via HTTP...")
            
            response = requests.post(
                create_url, 
                data=data, 
                timeout=300,  # 5 minutes timeout
                allow_redirects=False  # Không follow redirects để kiểm tra response code
            )
            
            # HTTP 303 redirect to /web means success
            if response.status_code in [200, 302, 303]:
                # Chờ một chút để database hoàn thành khởi tạo
                time.sleep(15)
                
                # Verify database được tạo trong PostgreSQL
                if self._database_exists_in_postgresql(database_name):
                    result['status'] = 'completed'
                    self.logger.info(f"✅ Database {database_name} created successfully via HTTP")
                else:
                    result['status'] = 'failed'
                    result['error'] = "Database not found in PostgreSQL after creation"
                    self.logger.error(f"❌ Database {database_name} not found after creation")
                    
            else:
                result['status'] = 'failed'
                result['error'] = f"HTTP {response.status_code}: {response.text[:500]}"
                self.logger.error(f"❌ Failed to create database: HTTP {response.status_code}")

        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            self.logger.error(f"❌ Error creating database: {e}")

        return result

    def _database_exists_in_postgresql(self, database_name: str) -> bool:
        """Kiểm tra xem database có tồn tại trong PostgreSQL không"""
        try:
            import psycopg2
            
            # Use localhost instead of container name when connecting from host
            host = 'localhost' if self.config.postgresql.host == 'postgresql' else self.config.postgresql.host
            
            conn = psycopg2.connect(
                host=host,
                port=self.config.postgresql.port,
                user=self.config.postgresql.user,
                password=self.config.postgresql.password,
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
            host = 'localhost' if self.config.postgresql.host == 'postgresql' else self.config.postgresql.host
            
            # Terminate all connections to the database
            conn = psycopg2.connect(
                host=host,
                port=self.config.postgresql.port,
                user=self.config.postgresql.user,
                password=self.config.postgresql.password,
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
            self.logger.info(f"✅ Database {database_name} deleted successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting database {database_name}: {e}")
            return False
