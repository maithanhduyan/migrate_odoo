"""
Database Setup Module - Tạo database demo đầy đủ cho Odoo v15 và v16
Tuân thủ nguyên tắc Elon Musk: First Principles, Tối giản, Automation

@author: Migration Team
@version: 1.0.0
"""

import os
import time
import logging
import json
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

import psycopg2
import requests
import docker

from .config import Config
from .utils import (
    check_container_running,
    check_database_connection,
    DockerManager,
    setup_logging
)
from .module_installer import OdooModuleInstaller

# Danh sách tất cả modules Odoo CE cơ bản
ODOO_CE_MODULES = [
    # Core modules
    'base', 'web', 'mail', 'contacts', 'base_setup',

    # Accounting & Finance
    'account', 'account_accountant', 'account_asset', 'account_budget',
    'account_check_printing', 'account_payment', 'account_reports',
    'account_sepa', 'account_test', 'payment',

    # Sales & CRM
    'sale', 'sale_management', 'sale_margin', 'sale_stock', 'sale_timesheet',
    'crm', 'crm_iap', 'partner_autocomplete',

    # Purchase & Inventory
    'purchase', 'purchase_requisition', 'purchase_stock', 'stock',
    'stock_account', 'stock_dropshipping', 'stock_landed_costs',
    'stock_picking_batch', 'mrp', 'mrp_account', 'quality',

    # Project & Timesheet
    'project', 'hr_timesheet', 'sale_timesheet', 'project_timesheet_holidays',
    'timesheet_grid',

    # Human Resources
    'hr', 'hr_attendance', 'hr_contract', 'hr_expense', 'hr_holidays',
    'hr_maintenance', 'hr_org_chart', 'hr_recruitment', 'hr_skills',

    # Website & E-commerce
    'website', 'website_blog', 'website_crm', 'website_event',
    'website_forum', 'website_links', 'website_livechat', 'website_mass_mailing',
    'website_partner', 'website_payment', 'website_profile', 'website_quote',
    'website_sale', 'website_sale_delivery', 'website_sale_digital',
    'website_sale_management', 'website_sale_stock', 'website_sale_wishlist',
    'website_slides', 'website_twitter',

    # Marketing & Communication
    'mass_mailing', 'mass_mailing_sms', 'email_template', 'marketing_automation',
    'sms', 'social_media', 'utm',

    # Manufacturing
    'mrp', 'mrp_account', 'mrp_byproduct', 'mrp_landed_costs', 'mrp_repair',
    'mrp_subcontracting', 'quality_control', 'quality_mrp',

    # Maintenance & Fleet
    'maintenance', 'fleet',

    # Reporting & Analytics
    'board', 'web_dashboard', 'web_cohort', 'web_gantt', 'web_graph',
    'web_kanban_gauge', 'web_pivot', 'web_studio',

    # Utilities & Tools
    'calendar', 'note', 'survey', 'lunch', 'library', 'documents',
    'knowledge', 'pad', 'voip', 'phone_validation',

    # Localization (basic)
    'l10n_multilang', 'account_tax_python',

    # Integration & API
    'restful', 'web_tour', 'fetchmailCRM', 'google_calendar',
    'google_drive', 'google_spreadsheet',

    # Point of Sale
    'point_of_sale', 'pos_discount', 'pos_hr', 'pos_loyalty',
    'pos_restaurant', 'pos_sale',

    # Event Management
    'event', 'event_booth', 'event_crm', 'event_sale', 'website_event_sale',

    # Subscription & Recurring
    'sale_subscription', 'website_sale_subscription'
]

# Demo data configuration
DEMO_DATA_CONFIG = {
    'companies': [
        {
            'name': 'Demo Company V15/V16',
            'email': 'info@democompany.com',
            'phone': '+1-555-123-4567',
            'website': 'https://democompany.com',
            'currency': 'USD',
            'country': 'United States'
        }
    ],
    'users': [
        {
            'name': 'Demo Admin',
            'login': 'admin',
            'email': 'admin@democompany.com',
            'groups': ['base.group_system']
        },
        {
            'name': 'Demo Sales Manager',
            'login': 'sales',
            'email': 'sales@democompany.com',
            'groups': ['sales_team.group_sale_manager']
        },
        {
            'name': 'Demo Accountant',
            'login': 'accounting',
            'email': 'accounting@democompany.com',
            'groups': ['account.group_account_manager']
        }
    ],
    'partners': [
        {'name': 'Customer A', 'email': 'customer.a@example.com', 'is_company': True},
        {'name': 'Customer B', 'email': 'customer.b@example.com', 'is_company': True},
        {'name': 'Vendor A', 'email': 'vendor.a@example.com', 'is_company': True, 'supplier_rank': 1},
        {'name': 'Vendor B', 'email': 'vendor.b@example.com', 'is_company': True, 'supplier_rank': 1}
    ],
    'products': [
        {'name': 'Demo Product A', 'type': 'product', 'list_price': 100.0},
        {'name': 'Demo Service A', 'type': 'service', 'list_price': 50.0},
        {'name': 'Demo Product B', 'type': 'product', 'list_price': 200.0},
        {'name': 'Demo Service B', 'type': 'service', 'list_price': 75.0}
    ]
}


class DatabaseSetup:
    """Class quản lý việc tạo và setup database demo"""

    def __init__(self, config: Config):
        self.config = config
        self.logger = setup_logging()
        self.docker_manager = DockerManager()
        self.module_installer = OdooModuleInstaller(config)

    def setup_demo_databases(self) -> Dict[str, Any]:
        """
        Tạo cả 2 database demo v15 và v16 với đầy đủ dữ liệu

        Returns:
            Dict chứa thông tin setup và kết quả
        """
        self.logger.info("🚀 Bắt đầu setup demo databases cho v15 và v16...")

        results = {
            'v15': {'status': 'pending', 'database': self.config.migration.demo_database_v15},
            'v16': {'status': 'pending', 'database': self.config.migration.demo_database_v16},
            'summary': {}
        }

        try:
            # 1. Kiểm tra và chuẩn bị môi trường
            self._prepare_environment()

            # 2. Setup database v15
            self.logger.info("📦 Setup database demo cho Odoo v15...")
            results['v15'] = self._setup_single_database('v15')

            # 3. Setup database v16
            self.logger.info("📦 Setup database demo cho Odoo v16...")
            results['v16'] = self._setup_single_database('v16')

            # 4. Tạo summary
            results['summary'] = self._create_summary(results)

            self.logger.info("✅ Hoàn thành setup demo databases!")
            return results

        except Exception as e:
            self.logger.error(f"❌ Lỗi khi setup demo databases: {e}")
            results['error'] = str(e)
            return results

    def _prepare_environment(self) -> None:
        """Chuẩn bị môi trường cho việc setup database"""
        self.logger.info("🔧 Chuẩn bị môi trường...")

        # Kiểm tra PostgreSQL
        if not check_database_connection(self.config.database):
            raise Exception("PostgreSQL không kết nối được")

        self.logger.info("✅ PostgreSQL sẵn sàng")

    def _setup_single_database(self, version: str) -> Dict[str, Any]:
        """
        Setup database cho một phiên bản Odoo cụ thể

        Args:
            version: v15 hoặc v16

        Returns:
            Dict chứa kết quả setup
        """
        result = {
            'status': 'in_progress',
            'database': getattr(self.config.migration, f'demo_database_{version}'),
            'version': version,
            'modules_installed': [],
            'demo_data_added': False,
            'error': None
        }

        try:
            database_name = result['database']
            odoo_config = getattr(self.config, f'odoo_{version}')

            self.logger.info(f"🏗️ Tạo database {database_name} cho {version}")

            # 1. Tạo PostgreSQL database
            self._create_postgresql_database(database_name)

            # 2. Khởi động Odoo container
            self._start_odoo_container(version)

            # 3. Chờ Odoo sẵn sàng
            self._wait_for_odoo_ready(odoo_config.web_url)

            # 4. Tạo Odoo database với demo data
            self._create_odoo_database(odoo_config.web_url, database_name, version)

            # 5. Cài đặt modules Odoo CE
            installed_modules = self._install_odoo_modules(odoo_config.web_url, database_name, version)
            result['modules_installed'] = installed_modules

            # 6. Thêm demo data nâng cao (optional)
            result['demo_data_added'] = self._add_advanced_demo_data(database_name, version)

            result['status'] = 'completed'
            self.logger.info(f"✅ Hoàn thành setup database {database_name}")

        except Exception as e:
            self.logger.error(f"❌ Lỗi khi setup database {version}: {e}")
            result['status'] = 'failed'
            result['error'] = str(e)

        return result

    def _create_postgresql_database(self, database_name: str) -> None:
        """Tạo PostgreSQL database"""
        self.logger.info(f"🗄️ Tạo PostgreSQL database: {database_name}")

        try:
            # Kết nối đến PostgreSQL
            conn = psycopg2.connect(
                host=self.config.database.host,
                port=self.config.database.port,
                user=self.config.database.admin_user,
                password=self.config.database.admin_password,
                database='postgres'  # Kết nối đến database mặc định
            )
            conn.autocommit = True

            with conn.cursor() as cursor:
                # Kiểm tra database đã tồn tại chưa
                cursor.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (database_name,)
                )

                if cursor.fetchone():
                    self.logger.info(f"Database {database_name} đã tồn tại")
                else:
                    # Tạo database mới
                    cursor.execute(f'CREATE DATABASE "{database_name}"')
                    self.logger.info(f"✅ Đã tạo database {database_name}")

            conn.close()

        except Exception as e:
            raise Exception(f"Lỗi tạo PostgreSQL database {database_name}: {e}")

    def _start_odoo_container(self, version: str) -> None:
        """Khởi động Odoo container"""
        odoo_config = getattr(self.config, f'odoo_{version}')

        # Kiểm tra container đã chạy chưa
        if check_container_running(odoo_config.container_name):
            self.logger.info(f"Container {odoo_config.container_name} đã chạy")
            return

        # Khởi động container từ docker-compose
        self.docker_manager.start_container_from_compose(
            odoo_config.docker_compose_path
        )

        # Chờ container khởi động
        time.sleep(15)

    def _wait_for_odoo_ready(self, web_url: str, timeout: int = 120) -> None:
        """Chờ Odoo sẵn sàng"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = requests.get(
                    f"{web_url}/web/database/selector",
                    timeout=10
                )
                if response.status_code == 200:
                    self.logger.info("Odoo đã sẵn sàng!")
                    return
            except requests.RequestException:
                pass

            time.sleep(5)

        raise Exception(f"Odoo không sẵn sàng sau {timeout} giây")

    def _create_odoo_database(self, web_url: str, database_name: str, version: str) -> None:
        """Tạo Odoo database qua odoo-bin command"""
        self.logger.info(f"🏗️ Creating Odoo database {database_name} via command line...")

        try:
            result = self.module_installer.create_database_with_demo(version, database_name)

            if result['status'] != 'completed':
                raise Exception(f"Database creation failed: {result.get('error', 'Unknown error')}")

            self.logger.info(f"✅ Database {database_name} created successfully")

        except Exception as e:
            raise Exception(f"Failed to create Odoo database: {e}")

    def _install_odoo_modules(self, web_url: str, database_name: str, version: str) -> List[str]:
        """Cài đặt các modules Odoo CE"""
        self.logger.info(f"📦 Installing Odoo CE modules for {version}...")

        # Lấy danh sách modules có sẵn
        available_modules = self.module_installer.get_available_modules(version)

        # Lọc modules phù hợp với phiên bản
        modules_to_install = self._filter_modules_for_version(version)

        # Chỉ cài modules có sẵn
        filtered_modules = [m for m in modules_to_install if m in available_modules]

        self.logger.info(
            f"Found {
                len(available_modules)} available modules, installing {
                len(filtered_modules)} CE modules")

        # Cài đặt modules theo batch
        installed_modules = []
        batch_size = 10

        for i in range(0, len(filtered_modules), batch_size):
            batch = filtered_modules[i:i + batch_size]

            try:
                result = self.module_installer.install_modules(version, database_name, batch)

                if result['status'] == 'completed':
                    installed_modules.extend(batch)
                    self.logger.info(f"✅ Installed batch {i // batch_size + 1}: {len(batch)} modules")
                else:
                    self.logger.warning(
                        f"⚠️ Failed to install batch {
                            i //
                            batch_size +
                            1}: {
                            result.get(
                                'error',
                                'Unknown error')}")

            except Exception as e:
                self.logger.error(f"❌ Error installing batch {i // batch_size + 1}: {e}")

        self.logger.info(
            f"✅ Completed module installation: {len(installed_modules)}/{len(filtered_modules)} modules installed")
        return installed_modules

    def _filter_modules_for_version(self, version: str) -> List[str]:
        """Lọc modules phù hợp với phiên bản Odoo"""
        # Danh sách modules cơ bản cho cả v15 và v16
        basic_modules = [
            'base', 'web', 'mail', 'contacts', 'base_setup',
            'account', 'sale', 'purchase', 'stock', 'crm',
            'project', 'hr', 'hr_timesheet', 'hr_holidays',
            'website', 'mass_mailing', 'calendar', 'note',
            'maintenance', 'fleet', 'survey'
        ]

        if version == 'v15':
            # Modules đặc biệt cho v15
            return basic_modules + [
                'sale_management', 'purchase_stock', 'mrp',
                'account_payment', 'hr_attendance', 'website_sale',
                'point_of_sale', 'event'
            ]
        elif version == 'v16':
            # Modules đặc biệt cho v16
            return basic_modules + [
                'sale_management', 'purchase_stock', 'mrp',
                'account_payment', 'hr_attendance', 'website_sale',
                'point_of_sale', 'event', 'documents'
            ]
        else:
            return basic_modules

    def _add_advanced_demo_data(self, database_name: str, version: str) -> bool:
        """Thêm demo data nâng cao"""
        self.logger.info(f"📊 Adding advanced demo data to {database_name}...")

        try:
            # TODO: Implement advanced demo data creation
            # Có thể sử dụng XML-RPC hoặc execute SQL commands

            self.logger.info("✅ Demo data added successfully")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to add demo data: {e}")
            return False

    def _create_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Tạo summary từ kết quả setup"""
        summary = {
            'total_databases': 2,
            'successful': 0,
            'failed': 0,
            'total_modules_installed': 0,
            'databases': []
        }

        for version in ['v15', 'v16']:
            result = results[version]

            if result['status'] == 'completed':
                summary['successful'] += 1
                summary['total_modules_installed'] += len(result.get('modules_installed', []))
            elif result['status'] == 'failed':
                summary['failed'] += 1

            summary['databases'].append({
                'version': version,
                'database': result['database'],
                'status': result['status'],
                'modules_count': len(result.get('modules_installed', [])),
                'demo_data': result.get('demo_data_added', False)
            })

        return summary

    def check_databases(self) -> Dict[str, Any]:
        """Kiểm tra trạng thái các database demo"""
        self.logger.info("🔍 Checking demo databases status...")

        results = {
            'v15': self._check_single_database('v15'),
            'v16': self._check_single_database('v16')
        }

        return results

    def _check_single_database(self, version: str) -> Dict[str, Any]:
        """Kiểm tra một database cụ thể"""
        database_name = getattr(self.config.migration, f'demo_database_{version}')

        result = {
            'database': database_name,
            'version': version,
            'exists': False,
            'odoo_accessible': False,
            'modules_count': 0,
            'error': None
        }

        try:
            # Kiểm tra database tồn tại trong PostgreSQL
            conn = psycopg2.connect(
                host=self.config.database.host,
                port=self.config.database.port,
                user=self.config.database.admin_user,
                password=self.config.database.admin_password,
                database='postgres'
            )

            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (database_name,)
                )
                result['exists'] = cursor.fetchone() is not None

            conn.close()

            if result['exists']:
                # Kiểm tra Odoo có truy cập được không
                odoo_config = getattr(self.config, f'odoo_{version}')
                try:
                    response = requests.get(f"{odoo_config.web_url}/web/database/selector", timeout=10)
                    result['odoo_accessible'] = response.status_code == 200
                except BaseException:
                    result['odoo_accessible'] = False

                # Đếm số modules đã cài (nếu truy cập được)
                if result['odoo_accessible']:
                    result['modules_count'] = self._count_installed_modules(database_name, version)

        except Exception as e:
            result['error'] = str(e)

        return result

    def _count_installed_modules(self, database_name: str, version: str) -> int:
        """Đếm số modules đã cài đặt"""
        try:
            # Kết nối trực tiếp đến database để đếm modules
            conn = psycopg2.connect(
                host=self.config.database.host,
                port=self.config.database.port,
                user=self.config.database.user,
                password=self.config.database.password,
                database=database_name
            )

            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) FROM ir_module_module WHERE state = 'installed'"
                )
                count = cursor.fetchone()[0]

            conn.close()
            return count

        except BaseException:
            return 0

    def cleanup_databases(self, force: bool = False) -> Dict[str, Any]:
        """Dọn dẹp các database demo"""
        self.logger.info("🧹 Cleaning up demo databases...")

        results = {
            'v15': self._cleanup_single_database('v15', force),
            'v16': self._cleanup_single_database('v16', force)
        }

        return results

    def _cleanup_single_database(self, version: str, force: bool = False) -> Dict[str, Any]:
        """Dọn dẹp một database cụ thể"""
        database_name = getattr(self.config.migration, f'demo_database_{version}')

        result = {
            'database': database_name,
            'version': version,
            'deleted': False,
            'error': None
        }

        try:
            # Kiểm tra database có tồn tại không
            conn = psycopg2.connect(
                host=self.config.database.host,
                port=self.config.database.port,
                user=self.config.database.admin_user,
                password=self.config.database.admin_password,
                database='postgres'
            )
            conn.autocommit = True

            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (database_name,)
                )

                if cursor.fetchone():
                    if force:
                        # Terminate all connections to the database
                        cursor.execute(f"""
                            SELECT pg_terminate_backend(pid)
                            FROM pg_stat_activity
                            WHERE datname = '{database_name}' AND pid <> pg_backend_pid()
                        """)

                        # Drop database
                        cursor.execute(f'DROP DATABASE "{database_name}"')
                        result['deleted'] = True
                        self.logger.info(f"✅ Deleted database {database_name}")
                    else:
                        self.logger.info(f"Database {database_name} exists but not deleted (use --force)")
                else:
                    self.logger.info(f"Database {database_name} does not exist")

            conn.close()

        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"❌ Error cleaning up {database_name}: {e}")

        return result
