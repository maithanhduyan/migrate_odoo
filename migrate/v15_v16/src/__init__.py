# Migration package for Odoo v15 -> v16
"""
Odoo Migration v15 to v16 Package

This package provides tools for migrating Odoo from version 15 to version 16,
including health checks, database analysis, configuration generation, and migration utilities.
"""

__version__ = "1.0.0"
__author__ = "Migration Team"

from .config import get_config, Config
from .utils import setup_logging, DockerManager, HealthChecker
from .health_check import OdooMigrationHealthChecker
from .config_generator import OdooConfigGenerator

__all__ = [
    'get_config',
    'Config', 
    'setup_logging',
    'DockerManager',
    'HealthChecker',
    'OdooMigrationHealthChecker',
    'OdooConfigGenerator'
]